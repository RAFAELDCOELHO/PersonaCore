---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
plan: 19
subsystem: planning
tags: [retract-in-place, traceability, validation-contract, false-figure, differential-privacy, subnormal]

# Dependency graph
requires:
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "22-17's `_log_erfc` routing fix and its `LOG_ERFC_BAND` sweep — the arithmetic half of round 2, and V-35/V-36's subject"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "22-18's fourteenth `DELTA_FRONTIER` row, retargeted `_inert_points` and in-band round-trip σ — the coverage half, and the artifact this plan's correction points at"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "22-16's record plan — the precedent for withholding the SC3 verdict and for proving the success criteria byte-unchanged by sha256"
  - phase: 21-the-privacy-unit-the-dp-data-path-and-the-n64-corpus
    provides: "REQUIREMENTS.md's UNIT-04 row — the retract-in-place SHAPE this plan copies (its dated `CLOSED … (plan 22-10)` plus 'the sentences above are left unamended'), not its wording"
provides:
  - "the false 'EXACTLY ZERO at σ ≥ 0.42' figure retracted in place in BOTH committed files, originals left standing, with the true measurement and the reason it was false"
  - "`ZERO_BOUNDARIES['erfc_zero_x']` corrected 27.5 → the measured 27.2, the 'a subnormal, still information' premise retracted with its cost, and the subnormal cliff 26.54325845425098 recorded beside it"
  - "DPSGD-03's row carrying gap-closure round 2 in round 1's three-part shape, plus an explicitly-labelled statement of WHAT WOULD MAKE A ROUND 3 NECESSARY with WARNING-4 named as genuinely OPEN"
  - "22-VALIDATION.md's V-35 … V-39 — five rows, one per guard round 2 added, every Automated command RUN before its row was written"
  - "the ROADMAP's five Phase-22 success criteria asserted BYTE-UNCHANGED by sha256, HEAD against worktree"
affects: [23 — this is the row Phase 23's `mitigation_budget.py` reads INSTEAD of re-deriving, and where WARNING-4 waits as an open risk]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reproduce a pre-fix route OUT OF TREE by rebinding the module-level function the caller looks up, rather than reverting the module — a fixed defect can still be measured without un-fixing it"
    - "A retraction states what the figure ACTUALLY measured, not only that it was wrong — the denominator is the finding"
    - "Correct the unconsumed constant that carries a retracted premise, and record in the constant's own comment that no test reads it — that is why it rotted"
    - "A closure records what would REOPEN it, each item paired with the guard that watches it or with the explicit statement that nothing does"

key-files:
  created:
    - .planning/phases/22-dp-sgd-core-accountant-and-the-correctness-battery/22-19-SUMMARY.md
  modified:
    - tests/fixtures/phase22_reference.py
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/phases/22-dp-sgd-core-accountant-and-the-correctness-battery/22-VALIDATION.md

key-decisions:
  - "[Phase 22] The plan's own premise that pre- and post-fix ε are 'bit-identical for σ ≥ 0.4125' was MEASURED FALSE and is not transcribed: they differ up to σ=0.4238, and at exactly 0.42 by 7.8216e-11. So the retracted sentence is false under BOTH readings, and the correction says so instead of adopting the plan's tidier explanation"
  - "[Phase 22] The worst subnormal log error is reported on TWO grids with both numbers (0.20941 at the verifier's own x, 0.22118 on a finer grid) because both x map to the SAME float64 erfc — the grid-dependence IS the evidence that the mantissa is gone, not noise to pick a winner from"
  - "[Phase 22] WARNING-4's 46 disagreements are ATTRIBUTED to `22-VERIFICATION.md` rather than re-derived: a 30,000-draw log-uniform sweep is not reproducible draw-for-draw, and a re-run would produce a different number presented as a confirmation"
  - "[Phase 22] `erfc_subnormal_x` was ADDED rather than `erfc_zero_x` merely corrected, because the module now routes on the subnormal cliff and a table recording only the zero cliff records the boundary nothing uses"

patterns-established:
  - "Retract-in-place applied to a figure INSIDE an argument: name which conjunct it supports, so a reader sees what the correction costs the argument rather than only that a number moved"

requirements-completed: []
requirements-contributed: [DPSGD-03]

# Metrics
duration: ~35min
completed: 2026-08-26
---

# Phase 22 Plan 19: The Record Matches the Measurement, Round 2 — Summary

**One sentence in two committed files made the erfc-SUBNORMAL band look already covered. It is now
retracted in place in both, with the true measurement, the reason it was false — and the finding
that it is false under BOTH readings, not just the one the plan handed me.**

**No source code was touched.** Suite unmoved at **1338 passed, 1 skipped**, which is the point:
this plan's only product is a written record that matches the tree.

**Commits:** `bf7e215` (Task 1), `db63f2d` (Task 2).

## Performance

- **Duration:** ~35 min wall clock, including one full-suite run at 225.81 s
- **Tasks:** 2 of 2
- **Files modified:** 4 (1 test fixture — comments and literal data only; 3 planning documents)

| Commit | Task | Subject |
|--------|------|---------|
| `bf7e215` | 1 | `docs(22-19)`: retract the "EXACTLY ZERO at sigma >= 0.42" figure in both committed files |
| `db63f2d` | 2 | `docs(22-19)`: record gap-closure round 2, and what would make a round 3 |

---

## The False Figure, Measured Rather Than Transcribed

The plan gave five figures and said *"confirm rather than transcribe."* **All five reproduced
exactly.** The pre-fix route was reproduced **out of tree** — 22-17 has landed and the module cannot
be un-fixed in place — by importing the shipped `accountant` and rebinding its module-level
`_log_erfc` to `if erfc(x) > 0.0: math.log(erfc(x))`, which `delta_closed` picks up by global lookup
at `accountant.py:394`. No repository file was edited to take the measurement.

| σ | plan said | measured here | fix's delta at that σ |
|---|---|---|---|
| 0.4185 | 9.6308e-12 | **9.6308e-12** | 6.87805368215777e-09 |
| 0.4200 | 1.1001e-13 | **1.1001e-13** | 7.821654435247183e-11 |
| 0.4250 | 9.9323e-17 | **9.9323e-17** | **0.0** (bit-identical) |
| 0.4300 | 1.5526e-16 | **1.5526e-16** | **0.0** |
| 0.4500 | 3.0649e-16 | **3.0649e-16** | **0.0** |

The first two agree with `22-VERIFICATION.md`'s own table (9.631e-12 at 0.4185, 1.100e-13 at
0.4200), as the plan predicted. **The error is never exactly zero** — it reaches machine epsilon
only past σ ≈ 0.425, and is ~1e-16 even there.

The right-hand column is the whole diagnosis in one place: at σ ≥ 0.425 the *fix's delta* is exactly
zero while the *error* is 1e-16 or 1e-17. That is the mis-measurement, visible as data.

### A SEVENTH figure caught wrong, and it was this plan's own

The plan explains the retracted sentence as measuring the fix's delta, *"pre-fix versus post-fix
SHIPPED values, **genuinely bit-identical for sigma >= 0.4125**"*. **Measured, that is false too.**
Swept at step 1e-4 over σ ∈ [0.4100, 0.4599] and at step 5e-4 over [0.4100, 0.4700]:

```
points where pre-fix != post-fix (step 5e-4): 19
  0.4135 0.414 0.4145 0.415 0.4155 0.416 0.4165 0.417 0.4175
  0.418 0.4185 0.419 0.4195 0.42 0.4205 0.421 0.4215 0.422 0.4225

at sigma = 0.42 EXACTLY: pre = 709.5584251988014
                         post = 709.5584251987232   identical = False   |delta| = 7.8216e-11
highest sigma at which they differ (step 1e-4): 0.4238
```

So the retracted sentence is **false under both readings**: the error is not zero at σ ≥ 0.42, and
neither is the fix's delta. The correction says so in both files rather than adopting the plan's
tidier explanation, and attributes what it can: the *"it measured the fix's delta"* diagnosis is
`22-VERIFICATION.md`'s own account of its own error, carried as an attribution, not asserted as my
measurement — because measurement shows even that reading does not hold at exactly 0.42.

### The two erfc cliffs, re-bisected

```
first x with math.erfc(x) == 0.0     : 27.2          (prev float 27.199999999999996 -> 1e-323)
first x with math.erfc(x) SUBNORMAL  : 26.54325845425098
                                       prev float's erfc = 2.2250738585076065e-308  (NORMAL)
                                       this   float's erfc = 2.225073858507186e-308  (subnormal)
math.erfc(27.0) = 5.23705e-319       math.erfc(27.5) = 0.0
```

`erfc_zero_x` was committed as **27.5**, which is not the boundary — merely a point past it. It now
reads **27.2**, and `erfc_subnormal_x = 26.54325845425098` is added beside it, because `_log_erfc`
routes on the *subnormal* cliff since 22-17 and a table recording only the zero cliff records the
boundary nothing uses.

### What a subnormal `erfc` actually costs — the "still information" premise

| grid | worst absolute error of `math.log(math.erfc(x))` | at x | relative in `exp(eps + log)` |
|---|---|---|---|
| 1001-pt uniform over the band | **0.20941** | 27.196716292271255 | **23.295%** |
| `26.0 + k*1e-4` | **0.22118** | 27.1965 | 24.755% |
| 400 consecutive floats below 27.2 | 0.030668 | 27.199999999998578 | 3.11% |

The first row **reproduces `22-VERIFICATION.md`'s own 2.094e-01 at the same x** exactly, and the
plan's "≈23.3%" lands at 23.295%. **Both grid figures are published rather than one being chosen**,
because the grid-dependence is itself the evidence: `math.erfc(27.1965)` and
`math.erfc(27.196716292271255)` are **the same float64, `1e-323`** — `math.log` cannot tell those
two x apart, which is precisely what "the mantissa is gone" means. (22-17's D-1 recorded the same
lesson: a grid is part of a figure's provenance.)

Surviving mantissa bits across the band, measured:

| x | `erfc(x)` | mantissa bits | absolute log error |
|---|---|---|---|
| 26.54325845425098 | 2.225073858507186e-308 | 53 / 53 | 3.4521e-14 |
| 26.8 | 2.484962157e-314 | 34 / 53 | 2.18e-11 |
| 27.0 | 5.23705e-319 | 18 / 53 | 4.744e-7 |
| 27.15 | 1.53e-322 | 6 / 53 | 0.0091656 |
| 27.199999999999996 | 1e-323 | 3 / 53 | 0.030668 |

The 4.744e-7 at x=27.0 matches 22-17's M-H message verbatim (`4.7440e-07 ABSOLUTE in the log`),
which is an independent cross-check on the whole measurement chain.

---

## What Each Correction Says, and Where

Both corrections follow **UNIT-04's shape** — a dated block appended, every original sentence left
standing — not its wording. (Recorded because the plan calls UNIT-04 the "worked retract-in-place
precedent": UNIT-04 has the shape, `CLOSED 2026-08-26 (plan 22-10)` plus *"The sentences above are
left unamended…"*, but **not the literal phrase "RETRACTED IN PLACE"**. The only prior occurrence of
that phrase is round 1's own block inside DPSGD-03. Shape copied; phrase not hunted for.)

| File | What the correction adds |
|---|---|
| `tests/fixtures/phase22_reference.py` — `EPSILON_OVERFLOW_REGIME` provenance | Five parts: what it actually measured (a **denominator** error, the class `accountant.py`'s own docstring names); the true figures; that the fix's-delta reading also fails at 0.42; that the two rows were **not** the whole reachable band ([0.4135, 0.4185] reachable and unswept, 1.9227e-03 wrong **without refusing**); and the artifact that discharges it, the fourteenth `DELTA_FRONTIER` row named by its `(eps, mu)` |
| `tests/fixtures/phase22_reference.py` — `ZERO_BOUNDARIES` | `erfc_zero_x` 27.5 → 27.2, the "still information" phrase retracted with its measured cost, `erfc_subnormal_x` added, and — in the section header — that **no test reads this dict** |
| `.planning/REQUIREMENTS.md` — DPSGD-03 | The same five parts, plus a **sixth that belongs only there** |

**Attribution, in both files.** The figure originated in `22-VERIFICATION.md`'s **first** report and
the round-1 gap plans transcribed it faithfully; the verifier retracts it in its own name
(*"the error is mine, not the executors'"*). No executor is blamed for a figure they were handed,
and it is recorded that the figure entered the fixture **through a plan** rather than obscured.

### The sixth part, which belongs only in DPSGD-03

The figure sits inside the row's **"NO PUBLISHED NUMBER WAS WRONG"** argument as one of its four
reasons — that is what makes it load-bearing rather than incidental. So the correction also records
that **the "no published number is optimistic" clause no longer covers this band**: round 1's defect
dropped a strictly positive term and therefore over-stated ε *in every band*, conservative by
construction; a subnormal's lost bits round both ways, and `22-VERIFICATION.md` measured the shipped
ε **below** the 60-dps truth at **σ = 0.4150, 0.4165, 0.4170 and 0.4175**. **A change in KIND, not
in magnitude.** What still holds is stated in the same breath: WARNING-3 — no production code
reports an ε at all, and Phase 23's `mitigation_budget.py` is the first consumer.

---

## Round 2, Recorded in Round 1's Three-Part Shape

Appended dated below the round-1 block; round 1 is **not** rewritten.

1. **What was measured false** — the two-oracle agreement, still, one band over, at the project's own
   frozen δ. Denominators separated as round 1 was forced to: **1.9190e-03** is the two-ORACLE gap
   with the closed form as denominator (re-measured `0.001918992313688636`); **1.9227e-03** is
   `delta_closed` against 60-dps truth (re-measured `0.0019227`). `delta_closed` there was
   **bit-identical to the pre-22-12 code** — a sibling defect the fix stepped over, not a regression.
   Direction **privacy-UNDERSTATING** at four σ.
2. **Why round 1's closure could not see it** — all five `missing:` items *were* genuinely closed and
   independently re-verified; the criterion is not "five items were addressed". `_inert_points()`
   was keyed on the property the defect satisfies (`erfc(b) > 0.0`) and therefore certified the
   defective band as healthy; 0 of 22 pinned points had a subnormal `erfc(b)`; `_round_trip_pairs()`
   bottomed out at σ=0.5. **Proven by EXECUTION**: `_log_erfc` returning `-12345.0` for every
   subnormal input left the full suite byte-identical to baseline at `1314 passed, 1 skipped`.
3. **What closed it, plan by plan** — 22-17 (the predicate keyed on a **format** property, the
   crossover proof that the new worst case *equals* the perfect-routing floor, the band sweep, M-H
   at 1 distinct test / 5 node ids, M-H-both's `F821`); 22-18 (the fourteenth row, the retargeted
   filter, the in-band round-trip σ, four count meta-guards plus a hard-equality pin, M-J at 2
   distinct tests, M-H re-applied at +3 node ids); 22-19 (this record).

**Every figure in that block is either re-measured here or attributed to the SUMMARY it came from.**
The 1.0174e-11-vs-1.0154e-11 denominator split and the row-dependent `mp.mpf(str)`-vs-`mp.mpf(float)`
gap (4.078e-15 here against 22-12's 8.90e-15 on a different row) are both carried into the row, so a
later reader does not file them as contradictions.

### The transferable finding, recorded as a finding rather than as trivia

Round 2 corrected **three figures in its own inputs**, and this plan caught a **fourth** — every one
by an executor who measured rather than transcribed:

| Corrected figure | Was | Measured |
|---|---|---|
| the "~29× sliver ratio" | 29× | a **grid artifact** — an accumulated `x += 0.05` grid whose "26.95" was really 26.950000000000102 |
| its replacement, *"bit-identical at EVERY point in the sliver"* | 1.0× | **also false** — 18/32 and 211/400 identical, the rest 1–5 ulp apart |
| *"the tree has zero `sys.float_info` uses"* | zero | **one**, in tests, deliberate |
| *"bit-identical for σ ≥ 0.4125"* (this plan's own input) | ≥ 0.4125 | they differ up to **σ = 0.4238** |

Round 1 had already produced three such corrections plus a SUMMARY margin off by 1000×. The rule the
row now states: **a figure entering a permanent record is either re-measured in the session that
writes it or attributed to the artifact it came from, with its denominator named — and a grid is
part of a figure's provenance, not a detail beneath it.**

---

## What Would Make a Round 3 Necessary

The part that is new, and the reason this plan exists rather than only its Task 1. Round 1 fixed a
point and the next verifier found the adjacent band; a set that merely fixes *this* band and adds one
more committed row invites the identical outcome. Three things, each paired with the guard that
watches it — or, for the third, with the honest statement that nothing does.

| # | What would reopen it | Watched by |
|---|---|---|
| 1 | the routing boundary moving toward the **lossy** side | **V-35**, 22-17's band sweep — it asserts the route ACTUALLY CHOSEN is accurate across all three regimes and reddens **without naming the boundary**; the previously shipped predicate fails it by eleven orders |
| 2 | the boundary moving the **other** way, into the healthy band | **NOT V-35** — the limit is stated rather than left to be inferred — but **V-38** plus its hard-count companion, under 22-12's **M-B** (6 of 7 pinned ε move, 4 to `0.0`) |
| 3 | a **NEW band, in a different function**, that no committed row sweeps | **NOTHING. This is the open one.** |

**Item 3 is `22-VERIFICATION.md` WARNING-4, and it is recorded as GENUINELY OPEN.** Outside the
subnormal band a 30,000-draw log-uniform sweep found **46 further two-oracle disagreements above
1e-9, worst 6.08e-09 at δ = 6.26e-237**. Three checkable grounds make it not-a-blocker rather than a
deferral label, and all three are in the row:

- it is a **different mechanism** — cancellation in `0.5*erfc(a) - second` near the representability
  floor, **not routing** — so it is *not* this defect one band over;
- it is **6× over budget, not 1.9e6×**;
- **0 of the 46 is at a δ above 1e-12**, against this project's frozen δ of **1e-5** — seven decades
  away — with `_MIN_TARGET_DELTA = 1e-300` (`accountant.py:124`) flooring the solver.

**It is not claimed closed, and it is not inflated into a blocker.** Those figures are
**attributed** to `22-VERIFICATION.md`, not re-derived: a 30,000-draw log-uniform sweep is not
reproducible draw-for-draw, and re-running it would produce a different number presented as a
confirmation.

**And what this plan set does not establish**, stated in the row: it closes the band the
re-verification measured and converts the guard from a fixed point list into a sweep of the
predicate's own neighbourhood, so a boundary move is caught by data rather than by the next verifier.
**It does not prove the accountant correct everywhere.** A bound measured on a band is a statement
about that band — this phase's own central finding, pointed at its own closure.

---

## The Verdict Is Withheld, and Both Warnings Are Accounted For

**The SC3 verdict is not claimed here, for the second round running.** The row records measured
state and closes by saying the call is a `/gsd:verify-phase 22` re-verification's, in round 1's own
words. `requirements.mark-complete` was **not called** — for the eighth consecutive plan, and here
for the concrete reason as well as the principled one: the handler leaves traceability cells
**empty**, and the entire deliverable of Task 2 is that cell's content. `requirements-completed: []`
and `requirements-contributed: [DPSGD-03]` in this SUMMARY's frontmatter, matching all seven
preceding gap plans.

**WARNING-1 was CLOSED by 22-13**, not deferred, and the row says so in the same sentence as
WARNING-2 so the pair cannot be read as two open warnings. **WARNING-2** — no production driver can
resume a DP arm — stays routed to **Phase 23 beside DPSGD-06**, on the reasoning that it is a
missing **feature** rather than a defect in what Phase 22 shipped, and that building it now would
anticipate what only Phase 23, whose first act is a genuinely real training run, actually needs.

---

## The Success Criteria Were Not Touched, and That Is Asserted

The cheapest way to close a failed verification is to rewrite the criterion it failed. Extracted
from `HEAD` and from the worktree — anchored on `/^### Phase 22: DP-SGD Core/` **first**, because an
`awk` matching every `**Success Criteria**` heading spans all nine phases and hashes to something
else entirely — and compared by hash, not by reading a diff:

```
73a316f4aaff10371ea2e6a605810af7d3b6990f56c4324413ef7068d0ccd968  (HEAD)
73a316f4aaff10371ea2e6a605810af7d3b6990f56c4324413ef7068d0ccd968  (worktree, after all ROADMAP edits)
24 lines, 5 (DPSGD- markers
```

Equal to **22-16's recorded value**. Re-run after the ROADMAP edits, not only before.

**`grep '^-[^-]'` was not used**, per 22-16's recorded failure. Every deleted line in this plan's
whole diff was enumerated instead — **six**, and **two of them begin with `- `**, i.e. exactly the
class that filter drops silently:

```
1: - [x] **Phase 22: DP-SGD Core, …**      <- re-emitted, extended with round 2's outcome
2: **Plans**: 19 plans in 13 waves (16 executed; …   <- re-emitted as (19 executed; …
3: Full suite `1332 passed, 1 skipped` = …           <- re-emitted, extended
4: `/gsd:verify-phase 22`'s** — 22-18 and 22-19 remain.)  <- re-emitted
5: - [ ] 22-19-PLAN.md — the record: …               <- re-emitted as [x] with its execution record
6:     "erfc_zero_x": 27.5,                          <- the intentional value correction
```

Additions dominate everywhere: REQUIREMENTS +1/−1 (one line, re-emitted with every original sentence
inside it), ROADMAP +28/−5, VALIDATION **+53/−0**, fixture +72/−1.

---

## The Validation Contract: Five Rows, Five Commands, All Run First

V-35 … V-39 continue the numbering from V-34 in the existing seven-column shape (9 `|`-delimited
fields, matching the header exactly — checked). **Every `Automated command` was executed before its
row was written**, and each Status cell carries that run's own output:

| V-ID | Guard | Command result |
|---|---|---|
| V-35 | 22-17's band sweep — the CHOSEN route asserted accurate across all three `math.erfc` regimes, boundary never named | **17 passed** |
| V-36 | its run-time three-regime non-vacuity companion + the hard-equality boundary-row pin | **1 passed** |
| V-37 | 22-18's fourteenth `DELTA_FRONTIER` row, V-01 and V-02 legs | **2 passed, 212 deselected** |
| V-38 | `_inert_points()` retargeted off `erfc(b) > 0.0`, plus its hard-count companion | **19 passed** |
| V-39 | the in-band round-trip σ=0.414 (4 legs) + the hard-equality pin that 0.414 is present | **5 passed, 209 deselected** |

The addendum also records, rather than editing the planning-time row, that the *Full suite command*
cell says `make test` — **broken in this tree** — and that every command used
`.venv/bin/python -m pytest`. It states the structural difference from round 1 explicitly: round 1's
guards were a **point list**, which is worth exactly the band it sweeps; V-35 is parametrized on the
boundary's own neighbourhood and V-36 exists because V-35 can be satisfied vacuously by a table that
has drifted off the boundary.

---

## Verification

| Check | Command | Result |
|---|---|---|
| Full suite | `.venv/bin/python -m pytest -q` | **`1338 passed, 1 skipped`** in 225.81 s |
| Baseline (22-18's close) | — | `1338 passed, 1 skipped` — **UNMOVED**, as required |
| Regressions | — | **zero**; this plan changes no code, so any movement would have been a defect |
| Task 1's subset | `pytest tests/test_phase22_{reference,accountant}.py -q` | `217 passed` — 22-18's count, unmoved |
| Lint | `.venv/bin/ruff check . && .venv/bin/ruff format --check .` | `All checks passed!` / `203 files already formatted` |
| Blast radius | `git diff --exit-code -- src/ scripts/ pyproject.toml requirements.txt` | **exit 0**, both at HEAD and across `bf7e215~1..HEAD` |
| Frozen pin | `git diff --exit-code 6ee90dc..HEAD -- scripts/mitigation_accountant.py` | **exit 0** — read, never written |
| Success criteria | sha256 of the Phase-22 block, HEAD vs worktree | **identical**, `73a316f4…`, 24 lines / 5 markers |
| Retractions | `grep -o "RETRACTED IN PLACE" .planning/REQUIREMENTS.md \| wc -l` | **2** — round 1's and round 2's |
| (the trap, demonstrated) | `grep -c "RETRACTED IN PLACE" .planning/REQUIREMENTS.md` | **1** — it counts LINES, and DPSGD-03 is one line |
| DPSGD-03 row shape | `awk -F'\|'` | **1 line, 5 fields** (3 columns + 2 sentinels), 31,197 chars |
| Requirements table intact | 5-field check over every `\| REQ \| Phase` row | UNIT-04 / DPSGD-01 / DPSGD-02 read 6 fields **at HEAD too** — pre-existing inline pipes, not introduced here; 48 rows before and after |
| New V-rows | `awk -F'\|'` field count | **9 each**, matching both addendum headers |
| Unticked Phase-22 boxes | `grep -c '^- \[ \] 22-'` | **0** |
| Plan count | `ls .planning/phases/22-*/22-*-PLAN.md \| wc -l` vs the count line | **19** vs `19 plans in 13 waves (19 executed` |
| Debt markers | `grep -nE "TBD\|FIXME\|XXX\|TODO\|HACK\|PLACEHOLDER"` over the 4 changed files | **12**, all `TBD` in `ROADMAP.md`, **all pre-existing at HEAD**; **0** in any line this plan added |
| Post-commit deletion check | both commits | **no files deleted** |
| Untracked files introduced | `git status --short \| grep '^??'` | **none** |
| Fixture still import-free | `pytest ...::test_reference_fixture_imports_nothing` | passing (inside the 217) — only comments and literal data changed |

---

## Deviations from Plan

### [Rule 1 — Bug in an inherited figure] The plan's "bit-identical for σ ≥ 0.4125" is false

Measured and recorded in full above. Writing the plan's phrasing into the permanent record would
have replaced one false figure with another in the very sentence correcting it. Both files now carry
the measurement (differing up to σ=0.4238; 7.8216e-11 apart at exactly 0.42) and state that the
retracted sentence is false under **both** readings. The *"it measured the fix's delta"* diagnosis is
carried as an **attribution** to `22-VERIFICATION.md` rather than asserted as mine, since measurement
shows even that reading fails at 0.42.

### [Rule 2 — Missing correctness] `erfc_subnormal_x` added, not just `erfc_zero_x` corrected

The plan asks for the second boundary to be recorded and it was, as a **named dict key** rather than
only as prose in a comment: `_log_erfc` routes on the subnormal cliff since 22-17, so a
`ZERO_BOUNDARIES` recording only the zero cliff records the boundary nothing uses. Verified safe —
nothing reads the dict (below), and the fixture's AST no-import / no-logic guards still pass.

### [Rule 2 — Documentation correctness] "No test reads this dict" recorded in the section header, not only beside the key

The plan asks for it in "the comment". It is placed in the **section-3 header**, because the claim is
about the whole constant rather than about `erfc_zero_x`, and because that is where a reader deciding
whether to trust any of the four values will look. Verified rather than assumed: outside the fixture,
`grep -rn "ZERO_BOUNDARIES" tests/ src/ scripts/` returns exactly one match,
`tests/test_phase22_accountant.py:1509`, and it is **prose inside a docstring** naming
`delta_quadrature_zero_z`.

### [Recorded, not smoothed] Two grids, two worst-case figures, both published

0.20941 at the verifier's own x on a 1001-point uniform grid; 0.22118 at 27.1965 on a finer
`26.0 + k*1e-4` grid. Neither is wrong. Both x map to the **same** float64 `erfc` (`1e-323`), which
is why the worst is grid-dependent at the top of the band — and that is the evidence for the claim
being made, so picking one number would have discarded the argument. (My first probe reported only
0.22118 because its grid mis-ranged; caught and both grids re-run before anything was written.)

### [Stale anchors] Three of the plan's line references

The plan cites the false figure at `phase22_reference.py:137-191` / `:186` and `_MIN_TARGET_DELTA` at
`accountant.py:114`. Measured: the sentence is at **`:240-241`** (22-17 and 22-18 inserted
`LOG_ERFC_BAND` and the fourteenth row above it), and `_MIN_TARGET_DELTA` is at **`:124`**. Located
by `grep` in every case, per the plan's own instruction. `_SMALLEST_NORMAL` at `:96` was correct.
The row and the ROADMAP blocks were located by heading, never by line number.

### [Scope] V-01 … V-34 left as they stand

Round 1's V-26 … V-34 keep their green Status cells and V-01 … V-25 keep `⬜ pending`, for the reason
22-16's addendum gives: re-scoring a validation contract is a verification act, not a recording one.

### [Withheld] `requirements.mark-complete` not called

Eighth consecutive plan. Recorded above with both reasons.

---

## Deferred Issues

**One, and it is the point of the round-3 statement rather than an oversight:** `22-VERIFICATION.md`
**WARNING-4** is recorded in DPSGD-03 as **genuinely open**, with the three checkable grounds that
make it not-a-blocker and an explicit refusal to call it closed. Nothing else was deferred by this
plan.

`deferred-items.md` was **read and not written**. Its two 22-17 entries — the `float_info` comment in
`src/` and the false figure this plan corrects — are now discharged by this plan's Task 1; they are
left standing rather than edited, because the file's own discipline is retract-in-place and the
correction lives in the two files the entries point at. (`22-17` destroyed 157 lines of that file
with a `Write` on an unread file and recovered them in `1f289dd`; the destructive commit `d27a1b6`
remains in history. This plan `Read` every file before editing it and used `Edit` throughout — no
`Write` touched an existing file.)

## Known Stubs

None. This plan created no code, no placeholders and no unwired data paths. Every figure written into
a permanent record was either measured in this session or attributed to the artifact it came from,
with its denominator named. Every command written into `22-VALIDATION.md` was executed first.

## Threat Flags

None. No network endpoint, no auth path, no file-access pattern, no schema at a trust boundary. Three
markdown planning documents and one test fixture's comments changed;
`git diff --exit-code -- src/ scripts/ pyproject.toml requirements.txt` is the shape of this plan's
blast radius and it is empty.

## Threat Register Disposition

| Threat ID | Disposition | Evidence |
|---|---|---|
| T-22-51 (a correction that erases what was claimed) | **mitigated** | Every original sentence stands in both files; corrections appended and dated. `git diff --numstat`: REQUIREMENTS **+1/−1** (the single row line re-emitted with its full original text inside), fixture **+72/−1** (the one deletion is the intentional `27.5 → 27.2` value correction), VALIDATION **+53/−0**, ROADMAP +28/−5 with all five deletions enumerated and shown re-emitted. |
| T-22-52 (success criteria edited to match the result) | **mitigated** | Block extracted with the Phase-22 anchor FIRST, sha256 compared HEAD vs worktree **after** the ROADMAP edits: identical, `73a316f4…`, equal to 22-16's recorded value. `grep '^-[^-]'` explicitly not used; all six deleted lines enumerated instead, two of which begin `- `. |
| T-22-53 (a validation row whose command was never run) | **mitigated** | All five commands executed before their rows were written; each Status cell carries that run's own count (17 / 1 / 2 / 19 / 5). |
| T-22-54 (round 3's open risk inherited silently) | **mitigated** | WARNING-4 named in the row with its worst case, its δ ceiling, its distinct mechanism and the frozen-δ distance — as **genuinely open**, attributed to the verifier, with no claim of closure and no inflation to blocker. |
| T-22-55 (a stale unconsumed constant carrying the retracted premise) | **mitigated** | `erfc_zero_x` 27.5 → the re-bisected 27.2, `erfc_subnormal_x` added, the "still information" phrase retracted with its measured cost, and "no test reads this dict" recorded in the section header after verifying it by grep. |
| T-22-SC (installs) | **accepted** | No installs, no code changes. `git diff --exit-code -- src/ scripts/ pyproject.toml requirements.txt` exits 0. |

## Tooling Hazards Hit

**The zsh backtick hazard was avoided outright.** Both commits used `git commit -F -` with a
**quoted** heredoc; no `-m` string was used. `ls -a | grep -E "^[0-9]"` returns nothing after each
commit — no stray `./700.0`-class file was created.

**`make test` was not used**; every run in this SUMMARY is `.venv/bin/python -m pytest` under the
Python 3.11 venv.

**No `Write` touched an existing file.** Every edited file was `Read` first and changed with `Edit`
— the direct lesson of 22-17's destroyed `deferred-items.md`. `REQUIREMENTS.md`'s DPSGD-03 row is a
single 31,197-character line and `ROADMAP.md` carries nine phases; a `Write` on either would have
been unrecoverable-in-history.

### `gsd-sdk` handler behaviour, measured this session — TENTH in a row, and the hazard MOVED HANDLERS

A snapshot of `STATE.md` was taken **before the first call**; every call used the `--flag` form where
it takes flags; `22-19-SUMMARY.md` was written **before** `roadmap.update-plan-progress`; and
`git diff .planning/` was inspected **after every call**. `status`, `completed_phases` and `percent`
were checked specifically, as instructed.

| Handler | Outcome |
|---|---|
| `state.advance-plan` | **CORRUPTED, with a NEW failure mode.** Frontmatter counters were right (`completed_plans` 46→47, `Plan: 19 of 19`) and it FLATTENED the body `Status:` prose to `Ready to execute` exactly as in 22-13/14/15/16, leaving the `Phase:` counter stale at `(18/19)`. **New: it REGRESSED `stopped_at` BACKWARDS**, from `Completed 22-18-PLAN.md` to `Completed 22-17-PLAN.md`. All three hand-repaired; the full `Status:` chain was restored from the snapshot with 22-19's entry prepended, and all three `PRIOR ENTRY, carried forward verbatim:` markers survive. |
| `state.update-progress` | **THE CLAIMED NO-OP MUTATED TWO FIELDS.** It returned `{"updated": false, "reason": "Progress field not found in STATE.md"}` — the same string as 22-12 … 22-16 — against a frontmatter that plainly has a `progress:` block. But it also flipped `status: executing` → **`planning`** and regressed `stopped_at` to 22-17 **a second time**. Prior sessions recorded this handler as a *silent* no-op needing no repair; that is no longer true, and a handler that reports `updated: false` while writing is worse than one that reports the corruption it caused. |
| `state.record-metric` | **CLEAN — and 22-18's regression did NOT reproduce.** `\| Phase 22 P19 \| 35min \| 2 tasks \| 4 files \|`: the `35min` unit survived with **no word doubling**, and `completed_phases` stayed at **3** and `percent` at **33**. So the `executing → planning` flip belongs to `update-progress` here, **not** to `record-metric` as 22-18 recorded it. Reported as a non-reproduction and a re-attribution, not smoothed into the pattern. |
| `state.add-decision` | **CORRUPTED, identically to 22-16:** wrote `- [Phase ?]: ` in front of the text. Hand-repaired, and the **remaining three decisions were written by hand** rather than risking three more corruptions — 22-13's and 22-16's approach, applied again. |
| `state.record-session` | **PARTIAL.** Its three fields updated and `stopped_at` survived at 22-19, but it did **not** flip `status` to `verifying` as it did for 22-16. Set by hand: the phase is complete and awaiting re-verification. |
| `roadmap.update-plan-progress` | **CLEAN — the blanked-date hazard did NOT reproduce, for the second session running.** Wrote `\| … \| 19/19 \| Complete   \| 2026-08-26 \|` with the date intact. 22-12 … 22-15 all recorded it blanking the date; 22-16 recorded the first non-reproduction and this is the second. |

**The success-criteria hash was re-checked AFTER every SDK call**, not only after my own edits —
still `73a316f4…`, 24 lines, 5 markers. `requirements.mark-complete` was not invoked.

**`completed_phases` stayed at 3 and `percent` at 33**, checked specifically. Neither moved, which is
correct: Phase 22's plans are all executed but its verdict is pending, and the counter is a
plan-execution counter rather than a verdict on SC3 — as 22-16 recorded when it first flipped 2→3.

## Self-Check: PASSED

| Claim | Verification | Result |
|---|---|---|
| all four touched files exist on disk | `[ -f … ]` ×4 | **FOUND** ×4 |
| `REQUIREMENTS.md` carries **two** retractions | `grep -o "RETRACTED IN PLACE" \| wc -l` | **2** |
| DPSGD-03 is still ONE row with 5 fields | `awk -F'\|'` | **1 line, 5 fields** |
| the round-3 statement is present and labelled | `grep -o "WHAT WOULD MAKE A ROUND 3 NECESSARY"` | **1** |
| WARNING-4 is named in the row | `grep -o "WARNING-4"` | **1** |
| the fixture carries the dated correction | `grep -c "RETRACTED IN PLACE 2026-08-26 (plan 22-19)"` | **2** (the provenance block and `erfc_zero_x`) |
| `erfc_zero_x` reads 27.2 with the subnormal cliff beside it | read back from the file | **`27.2`** and **`erfc_subnormal_x: 26.54325845425098`** |
| `22-VALIDATION.md` carries V-35 … V-39 | `grep -cE '^\| V-3[5-9] \|'` | **5** rows |
| ROADMAP Phase 22 fully ticked | `grep -c '^- \[ \] 22-'` | **0** unticked |
| commit `bf7e215` exists | `git log --oneline --all \| grep -q` | **FOUND** |
| commit `db63f2d` exists | `git log --oneline --all \| grep -q` | **FOUND** |
| success criteria byte-unchanged | sha256, HEAD vs worktree | **identical**, `73a316f4…` |
| suite unmoved | `.venv/bin/python -m pytest -q` | **1338 passed, 1 skipped** |
| lint clean | `ruff check` + `ruff format --check` | **passed / 203 files** |

**One defect was caught by this self-check and fixed before the SUMMARY was committed, and it is the
SAME ONE 22-16 recorded:** the file's first write ended with a stray `</content>` tool-call marker
pasted into the document body. Recorded rather than silently corrected, for 22-16's own reason — a
SUMMARY carrying markup that is not prose is the same defect class as a verbatim quote that is not
verbatim — and because a hazard that has now recurred across two record plans is a pattern, not an
accident. The check that finds it is one `grep`, and it belongs in every record plan's self-check
from here.
