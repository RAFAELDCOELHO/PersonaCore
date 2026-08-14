---
phase: 17-multi-persona-isolation-matrix
plan: 08
subsystem: isolation-report-mode-and-inferential-gate
tags: [stat-01, stat-02, stat-03, stat-06, iso-03, iso-04, d-10, d-11, d-13, d-15, d-18, d-21, th-17-26, th-17-45, mutation-proved]
requires:
  - scripts/phase16_persistence.py (fact_signs / sign_test_exact / holm / cluster_bootstrap /
    report_proportion / rule_of_three / WILSON_LABEL / HOLM_ALPHA / SIGN_TEST_N /
    BOOTSTRAP_* — imported UNCHANGED; STAT-04 satisfied literally by import)
  - scripts/phase17_personas.py (HOLM_FAMILY_CELLS, CELL_ALTERNATIVE, SIGN_UNIT, BASE_ROW,
    PERSONA_SEEDS, REPLICATION_SEEDS, GATE_AGGREGATION_RATIONALE, ALL_FAIL_BRANCH,
    gate_cleared, worst_pair, assert_phase17_family_closed,
    assert_family_length_matches_phase16 — the verdict IMPORTS the pre-registration)
  - scripts/phase17_isolation.py (17-04's assemble_matrix / base_texts_by_slot /
    score_completion and 17-06's assert_sweeps_ran_on_distinct_weights / values_by_slot /
    SWEEPS / sweep_record_path — extended ADDITIVELY, nothing edited)
  - scripts/_verdict.py (recorded_verdict — the ONE copy of the anchored `## Verdict` read)
  - scripts/phase14_factset.py (BASE_PRIOR_SEEDS — read lazily, as a 2-of-8 sanity anchor only)
provides:
  - run_report_mode / read_sweep_records / draws_per_question / cell_rates / compare_cells /
    describe_matrix / base_prior_anchor / render_report / prereg_commit /
    assert_isolation_report_not_clobbered / ISOLATION_REPORT_PATH
  - the FIRST production caller of assert_sweeps_ran_on_distinct_weights (17-06's handover #1)
  - tests/test_phase17_stats.py — 19 tests (10 from 17-01, 9 new)
affects:
  - plan 17-09 (runs `--report` after the four sweeps; the report path and every refusal are
    committed here, so that run produces numbers and nothing else)
  - plan 17-10 (replaces EXACTLY the one `not yet measured` line in `## Replication (ISO-05)`
    and asserts everything above the addendum is byte-identical)
  - plan 17-11 (adds `--replicate`; its seed-scoped records are structurally unreachable from
    `read_sweep_records`, which reads the four unscoped paths BY NAME rather than by glob)
tech-stack:
  added: []
  patterns:
    - the whole report text committed BEFORE it produces a number
    - the verdict computed by importing a pre-registered function, never retyped as prose
    - every display constant derived from the instrument that produced the numbers beside it
    - a static call-site scan and a runtime closure guard, because neither catches the other's case
    - guards mutation-proved — watched failing before being trusted
key-files:
  created: []
  modified:
    - scripts/phase17_isolation.py (1172 -> 1937 lines, purely additive)
    - tests/test_phase17_stats.py (380 -> 975 lines, 9 tests added, 0 deleted)
    - .planning/REQUIREMENTS.md (STAT-03 Pending -> Complete)
decisions:
  - the two achievable p values the report publishes as a design property are RETURNED BY
    compare_cells, never recomputed by the writer — a second sign_test_exact call site is a
    second hypothesis family, and the new D-21 scan caught exactly that on its first run
  - report_proportion's raw-count denominator is the RECORDED draws-per-question times each
    cell's own question count, never SHARED_ARM_CONFIG.n_draws
  - the four category counts render once per ROW, never once per cell (17-04's D-12 handover)
metrics:
  duration: 32min
  tasks: 3
  files: 2
  completed: 2026-08-14
---

# Phase 17 Plan 08: The Report Mode, the Imported Gate and the D-10 Branch Summary

The complete text of Phase 17's verdict — including the branch taken when the gate does NOT clear,
the fork between "not judgeable" and "leakage found", and every sentence that reads a number — is
now in git history before a single Phase 17 number exists, the gate is assembled entirely from
imported Phase 16 statistics with the family closed at both the static and the runtime level, and
ISO-04's unskippable cross-process proof finally has a production caller.

## What Was Built

### Task 1 — the report mode, the ISO-04 proof and the gate (commit `c2acc0e`)

`run_report_mode()` is pure CPU: no torch, no model, no tokenizer, no generation. The order is the
contract, and each step is a precondition of the next:

| # | step | what it forecloses |
|---|---|---|
| 1 | `assert_isolation_report_not_clobbered()` | a recorded verdict overwritten. FIRST, before a byte is read |
| 2 | `read_sweep_records()` | the four UNSCOPED records read BY NAME — 17-11's seed-scoped replicates are structurally unreachable rather than filtered out |
| 3 | `assert_sweeps_ran_on_distinct_weights(records)` | **17-06's handover #1, discharged.** A fabricated matrix from sweeps that shared weights, refused BEFORE any scoring |
| 4-5 | `base_texts_by_slot` then `assemble_matrix(records, ...)` | **all four records**, so cells `(base, j)` are computed rather than published empty |
| 6 | `describe_matrix` then `compare_cells(cell_rates(matrix))` | descriptive first, gate second, and the gate over the nine adapter cells only |
| 7 | `render_report(...)` | — |

`main()`'s `--report` branch dropped its `# noqa: F821` **in this same commit**, as 17-06 required.

**`compare_cells` is the one function permitted to call `holm` or `sign_test_exact`.** Nothing
statistical is written: `fact_signs`, `sign_test_exact` and `holm` are imported unchanged, and
STAT-04 is satisfied literally by import. Both halves of the closure run —
`assert_phase17_family_closed` (a dynamically-built cell list) and the static AST scan (a new call
site) — plus `assert_family_length_matches_phase16`, F-08's pin on the coincidence that Phase 16's
`C(4,2)` and this phase's `3x2` both equal 6.

**`cell_rates` drops the base row before the family is built and `compare_cells` re-proves the
absence.** The filter is not trusted: a base cell reaching the gate raises naming `0.0071429`, the
alpha a seventh comparison would price — below the achievable `0.0078125`, so the headline would die
arithmetically at every possible outcome including perfect unanimity.

Measured on synthetic four-record sets, before any of it was written down:

| fixture | result |
|---|---|
| perfect diagonal, zero off-diagonals | six rows, all rejected, every p exactly `0.0078125`, `gate_cleared` **True** |
| one slot ties in one comparison | that comparison p `0.0703125`, retained at alpha `0.05`, five of six, `gate_cleared` **False** |
| a `("base", j)` key in `per_cell` | `SystemExit` naming `0.0071429` |

### Task 2 — the report writer, committed before it produces a number (commit `c9c3274`)

`render_report` writes `results/phase17_isolation_report.md`. Seven sections, every framing string a
module-level constant: **Pre-Registration** (the six comparisons with their declared directions, the
seeds, the step alphas, and the margin stated as a known property of the design), **The Matrix**
(four rows — three adapters and the base — each cell through `report_proportion`'s `formatted` so
none can render a bare percentage), **Categories**, **Gate** (all six Holm rows, always),
**Verdict**, **Replication (ISO-05)**, **Provenance**.

**The margin is derived, not typed.** Slot unanimity gives `0.0078125`, the first step alpha is
`0.0083333`, and the margin is `0.0005208`; a single tie gives `0.0703125`, above even the last
step's `0.05`. So the gate requires all **48** slot-level observations (6 comparisons x 8 slots) to
favour the diagonal, and the report says so before the run rather than after it.

**The verdict is `gate_cleared`'s own return value.** When it is `False` the writer emits
`ALL_FAIL_BRANCH` in full and then both of the things the branch requires — not either: (a) the
three diagonal magnitudes with their bootstrap intervals, and (b) the adapter-off column read OFF
THE SAME MATRIX rather than restated. Then the fork is rendered explicitly (a low diagonal means the
matrix has NO POWER to judge isolation and "not demonstrated" means "not judgeable", never
"isolation failed"; a high diagonal with a blocking off-diagonal is a real leakage finding), D-15's
no-ranking sentence, the cross-phase anchors each labelled with its unit so the fork is decidable,
and **D-11 named as this phase's instance of a milestone pattern**.

Two `_prove`s run over the RENDERED text before it is written — the half a source scan structurally
cannot do, because a format string produces the number the reader actually sees: the report must
carry a `## Verdict` section the clobber guard can anchor on, and it must contain no bare zero
percentage anywhere.

### Task 3 — the tests, and the one that went red on its first run (commit `2c363f0`)

Nine new tests, 19 in the file, **1.6 s whole file, slowest test 0.29 s**, CPU-only.

| test | what it pins |
|---|---|
| `test_gate_modules_covers_all_four_phase17_drivers` | the D-21 glob resolves to all four drivers, counted AND named |
| `test_nothing_outside_the_six_pairs_enters_the_verdict_path` | `holm` / `sign_test_exact` reach only `compare_cells` across all four drivers; `holm` at exactly ONE site; `compare_cells` calls both closure guards; Phase 16's per-fact grouping helper has no call site anywhere |
| `test_the_base_row_is_published_but_never_gated` | ISO-03 / STAT-03, with the m=7 arithmetic asserted rather than quoted |
| `test_the_matrix_publishes_the_base_column` | the B4 regression, driven THROUGH `run_report_mode` so the four-record contract is asserted at the production call site |
| `test_signs_use_the_question_unit` | STAT-01 on a fixture where the two units order differently, with the draw-unit counterfactual computed |
| `test_no_bare_zero_percent` | STAT-02 over four driver sources AND over a rendered report |
| `test_zero_cells_carry_both_clustering_ends` | both rule-of-three ends, derived from the fixture, with the label naming which is optimistic |
| `test_all_fail_branch` | D-10 / D-11, both outcomes, plus the single `not yet measured` line |
| `test_report_refuses_a_clobber` | the guard runs FIRST — proved by leaving the sweep directory empty |

## The Guards, Watched Failing

### The D-21 scan went red on its FIRST run, against my own writer

This is the finding worth carrying forward. `render_report` computed the two achievable p values for
§Pre-Registration by calling `sign_test_exact` itself. The new scan refused it:

```
E   AssertionError: sign_test_exact is called from somewhere other than compare_cells — every
    call site OUTSIDE the one permitted function is a second hypothesis family
E   assert ['compare_cells', 'render_report', 'render_report'] == ['compare_cells']
```

The fix is not a suppression: `compare_cells` now RETURNS `achievable`, so the margin the report
publishes is the same instrument's output as the p values it is compared against, and the two cannot
drift. The test was written to catch a Phase 17 driver adding a gate call and it caught one
immediately — in the plan that wrote it.

### The three plan-mandated deliberate-RED probes

`scripts/phase17_isolation.py` sha256 is **`fb677f813231911ae5fdeca869cf15c1fac78e0a8c232fa16131b098d8d5ffc0`** before and after every probe.

| probe | observed |
|---|---|
| a second `holm(...)` in a new function | `AssertionError: ... Holders: ['_red_probe_second_family', 'compare_cells']` — **the failure names the function** |
| the assembly swapped to the DRAW rate | `SystemExit: [phase16_persistence] PROOF FAILED: 48 successes outside [0, 24] questions — 'successes' is in the STAT-01 QUESTION unit here, not the draw unit` |
| only the three adapter records to `assemble_matrix` | `SystemExit: [phase17_isolation] PROOF FAILED: assemble_matrix received 3 sweep record(s) ... handing over only the adapter records leaves cells (base, j) uncomputed and publishes an EMPTY BASE COLUMN as 'the control'` |

The second probe is worth reading carefully: it fails at `report_proportion`'s own guard, an
INDEPENDENT second layer, rather than at the sign assertion the test was written for. So the
counterfactual is computed in the test itself instead of inferred — the same fixture run through the
same `compare_cells` on a draw-unit `per_cell` gives `p = 1.0` where the question unit gives
`0.0078125`. The flip is observed, not argued.

### The runtime unit guard

`monkeypatch.setattr(iso.personas, "SIGN_UNIT", "draw")` makes `compare_cells` raise naming STAT-01,
so a silent revert to the draw rate cannot publish without going red.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `report_proportion`'s third argument would publish "9 draws" beside "0/104 questions"**

- **Found during:** Task 1, writing `describe_matrix`.
- **Issue:** the plan specifies
  `report_proportion(cell["n_answerable"], cell["n_questions"], SHARED_ARM_CONFIG.n_draws)`. That
  third argument is the RAW-COUNT denominator and renders literally as `"{n} draws"`;
  `SHARED_ARM_CONFIG.n_draws` is **9**, the per-question budget, so a 104-question cell would publish
  `0/104 questions (...; 9 draws)` — understating the raw count by two orders of magnitude, on the
  one axis T-16-40 records as the repudiation surface. Phase 16's own `_proportion_row` passes
  `aggregate["n_draws"]`, the TOTAL. `report_proportion` only `_prove`s `n_draws > 0`, so 9 passes
  silently.
- **Fix:** `draws_per_question(records)` reads the budget off the recorded completions,
  `_prove`s it single-valued across all four sweeps AND equal to each record's own published
  `config["n_draws"]`, and `describe_matrix` multiplies it by each cell's own question count. The
  second half of that proof is the stronger claim — a record whose completions disagree with the
  parity block it publishes describes a generation budget none of its completions came from.
- **Files modified:** `scripts/phase17_isolation.py`
- **Commit:** `c2acc0e`

**2. [Rule 1 - Bug] `render_report` calling `sign_test_exact` is a second hypothesis family**

- **Found during:** Task 3, first run of the new D-21 scan (see above).
- **Fix:** `compare_cells` returns `achievable`; the writer reads it. Ties the published margin to
  the instrument that produced the p values beside it.
- **Files modified:** `scripts/phase17_isolation.py`, `tests/test_phase17_stats.py`
- **Commit:** `2c363f0`

**3. [Rule 1 - Bug] §Categories per CELL would relabel a row property as a per-column one**

- **Found during:** Task 2.
- **Issue:** the plan says "`## Categories` — per cell, the diagonal / leak / base_prior /
  confabulation counts". 17-04's handover #5 is explicit that these are a **ROW** property: `classify`
  takes no `j` by design (D-12), so the counts are identical across a row's three cells, and
  `matrix[(a, b)]["leak"]` is NOT "how often B's value appeared under adapter A" — that quantity is
  `n_answerable`. Rendering them per cell would print each number three times under three column
  headings, which is the exact misreading 17-04 records as a live repudiation surface.
- **Fix:** the section renders ONE ROW PER MATRIX ROW (4 rows), with `CATEGORY_ROW_PROPERTY_NOTE`
  stating the property and naming the per-column number.
- **Files modified:** `scripts/phase17_isolation.py`
- **Commit:** `c9c3274`

**4. [Rule 2 - Missing critical functionality] `resamples` as a committed test seam, printed in the artifact**

- **Found during:** Task 2.
- **Issue:** `cluster_bootstrap` at the pre-registered 10,000 resamples over 12 cells makes any test
  that exercises the whole assembly take tens of seconds, and this phase's test files run in ~1 s.
- **Fix:** `describe_matrix` and `run_report_mode` take `resamples` as a keyword whose DEFAULT is
  `persistence.BOOTSTRAP_RESAMPLES` — read from the committed constant, never retyped — forwarding
  to `cluster_bootstrap`'s OWN already-committed keyword. `main()` passes nothing, and §The Matrix
  **prints the count actually used**, so a lowered one is visible in the published artifact rather
  than hidden in a call. This is a seam, not a knob: the interval method and the resample count for
  the published report are fixed by the default.
- **Files modified:** `scripts/phase17_isolation.py`
- **Commit:** `c9c3274`

### Interpretations recorded

**`grep -c "aggregate_by_fact"` returns 1, not the 0 the criterion asks for, and the invariant is
asserted instead.** The single occurrence is **pre-existing**, in 17-04's `assemble_matrix`
docstring, where it explains why that function must not be called. This plan's own additions avoid
the identifier (the recorded 17-01/17-04/17-05/17-06 shape, arriving a fifth time), so the count did
not move. Editing another plan's committed reasoning to satisfy a grep would delete the warning the
grep exists to protect. The property the criterion is a proxy for — **no CALL SITE** — is asserted
mechanically instead, in `test_nothing_outside_the_six_pairs_enters_the_verdict_path`, across all
four Phase 17 drivers. `ast` call-site count: **0**.

**`holm` is count-pinned at one site; `sign_test_exact` is not.** Phase 16's twin asserts a sorted
list of holder names, which works there only because each holder calls each callee once. Here
`sign_test_exact` legitimately runs once per comparison in a comprehension plus twice for the two
design anchors, so the holder assertion is a SET and `holm` — the call that FORMS the family — gets
its own `len(sites) == 1`. A second `holm(...)` even inside `compare_cells` would be a second family
priced at the same alpha, and that is now red.

**The report is write-once, and `## Replication (ISO-05)` sits AFTER `## Verdict`.** So
`recorded_verdict` returns the verdict body alone, and a second `--report` run refuses. 17-10 edits
the one placeholder line in a reviewed commit rather than re-running the driver.

**The tests use the REAL minted values, not synthetic ones.** SC3's synthetic-value property belongs
to the scoring core and is pinned in `tests/test_phase17_scoring.py`; the report path legitimately
reads the material at the run's edge (`run_report_mode` calls `values_by_slot()`), so exercising it
on the committed values is testing the mapping the published report will actually use.

**Fixture size.** 8 slots x 3 questions x 4 draws, not the real 8 x 13 x 9. `assemble_matrix`
imposes no per-slot question count (only `held_out_by_slot` does, and the report path never calls
it) and the sign test needs the 8 SLOTS, which the fixture keeps. Every bound the tests assert is
DERIVED from the fixture, so a fixture of a different size cannot make a test pass on a number the
report never printed.

## Verification

| Check | Result |
|---|---|
| `pytest -q tests/test_phase17_stats.py -x` | **19 passed** in 1.36s (>= 16 required; was 10) |
| `pytest -q tests/test_phase17_stats.py --durations=5` | slowest **0.29 s** |
| `pytest -q tests/test_phase17_stats.py tests/test_phase17_scoring.py -x` | **37 passed** |
| `pytest -q` (full suite) | **645 passed, 1 skipped** in 124.06s (baseline 636/1 + 9 new; floor 579/1) |
| `assemble_matrix` call args in `run_report_mode` (AST) | `records, values_by_slot(...` — the full list, no `adapter_records` |
| `holm` / `sign_test_exact` holder set (AST) | `{'compare_cells'}` |
| `aggregate_by_fact` CALL sites (AST, all four drivers) | **0** |
| `re.search(r'\b0(\.0+)?%', source)` | `None` on all four Phase 17 drivers |
| `grep -c "0.2486\|0.2000"` (ISO-07) | **0** |
| rendered report: `recorded_verdict` parseable / no bare zero / one `not yet measured` line | all three, in both the cleared and the five-of-six case |
| `prereg_commit()` | `d549e0b` — 17-01's own add commit, resolved through `--diff-filter=A` |
| `git diff -- pyproject.toml` (STAT-04) | empty |
| `git status --short results/ checkpoints/ data/` | empty — this plan writes no report |
| `.venv/bin/ruff check .` + `format --check .` (the CI version, 0.15.16) | clean, 155 files |
| `make lint` | **red — pre-existing DEF-17-01, count unchanged at 9** |

## Deferred Issues

`make lint` still fails from **DEF-17-01** (recorded at 17-01, pre-existing to it). `Makefile:16`
runs bare `ruff`, which resolves on this box to a pyenv shim holding **ruff 0.1.15** against the
project's `ruff~=0.15` pin. The count is **unchanged at 9** — `tests/test_phase17_stats.py` was
already in that list after 17-01, and `scripts/phase17_isolation.py` is not in it. `.venv/bin/ruff`
0.15.16 — the version `.github/workflows/ci.yml:36-38` installs and runs — is clean on both files.
Nothing new deferred by this plan.

## Known Stubs

One, and it is the plan's own mandate rather than an omission: `## Replication (ISO-05)` renders
`REPLICATION_PENDING_LINE` — **"ISO-05 replication result: not yet measured."** — as a single,
greppable line. It is not a placeholder standing in for missing code: everything ISO-05 needs at
report time (the six ordered off-diagonal rates, `worst_pair`'s selection over them, the k=3 seeds,
and the D-16 descriptive-only statement) is rendered above it. Only the MEASUREMENT is absent,
because `--replicate` is plan 17-11 and the run is 17-10. Rendering the section with the words
rather than omitting it is what makes the absence visible; 17-10 Task 3 replaces exactly that line
and asserts everything else above the addendum is byte-identical, which is why the phrase appears
nowhere else in the module (verified: `count == 1`).

## Handover Notes

1. **17-09 runs `python scripts/phase17_isolation.py --report` after all four sweeps.** It passes no
   `resamples`, so the published interval runs at the pre-registered `BOOTSTRAP_RESAMPLES`. The
   report is **write-once**: `assert_isolation_report_not_clobbered` refuses a second run, so a
   re-drive needs the file deleted in a reviewed commit.
2. **17-09 must still assert `checked > 0`** in
   `test_phase17_prereg_is_frozen_before_every_phase17_result` (17-01's handover #2). That guard is
   vacuous until a `results/phase17_*` artifact is committed, and **this plan commits none** —
   `git status --short results/` is empty. 17-07 commits the first one.
3. **17-10 Task 3 replaces exactly `REPLICATION_PENDING_LINE`.** It is the only line in the module
   carrying "not yet measured", and `test_all_fail_branch` asserts the count is 1 in both gate
   outcomes.
4. **17-11's seed-scoped records cannot be swept into the matrix.** `read_sweep_records` reads the
   four unscoped paths BY NAME; there is no glob to widen. Keep it that way — a replicate scored
   into the matrix is a fifth row of a matrix closed at four.
5. **Do not let a writer call `holm` or `sign_test_exact`.** Anything the report needs from the
   instrument comes back on `compare_cells`'s return dict. That is now enforced, and it went red on
   its first run — see above.
6. **The category counts remain a ROW property** (17-04's handover #5, honoured in §Categories).
7. **`base_prior_anchor` is reported, never asserted on.** A miss on `rose` / `the country` prints as
   a **sweep problem to investigate before trusting the derivation on the other six slots**. If
   17-09's real run shows a miss, that is a signal about the sweep, not a finding about isolation,
   and it must not be suppressed.

## Requirements

**STAT-03 marked Complete.** Its text is about the correction METHOD across the isolation matrix —
"use Holm step-down, not Benjamini-Hochberg" — not about a measured artifact, and this plan is where
the method is applied: `compare_cells` is the only path from the matrix to a verdict, it calls
Phase 16's `holm` unchanged, and BH is now structurally unreachable (a static call-site scan across
all four drivers plus two runtime closure guards, all watched failing). 17-01 and 17-08 are its only
claimants and 17-01 explicitly deferred it here, so declining again would leave it Pending forever.
Nothing later in the phase can make it more true: the ISO-05 replication is descriptive by
construction (D-16) and `gate_cleared` structurally cannot admit a replication row.

**ISO-03 and ISO-05 NOT marked.** Both require a measured artifact that does not exist. ISO-03 reads
"the **matrix** carries an explicit adapter-off control column" — no adapter has trained, no sweep
has run and no matrix exists; this plan ships the code that computes and publishes that column, and
17-09 produces it. ISO-05 reads "the worst-colliding pair **is replicated** across seeds" — nothing
has been replicated; 17-10 and 17-11 own it. This is 17-01's recorded over-claim pattern avoided a
sixth time. STAT-01, STAT-02, STAT-04, STAT-05 and STAT-06 were already Complete from Phase 16 and
are unaffected.

## Threat Flags

None. No new network endpoint, auth path or schema change at a trust boundary. The one new
file-access pattern — reading four recorded JSON sweep records and writing one markdown report — is
`json.loads` over files this repository wrote, guarded by the clobber refusal on the write side.

Register dispositions: **TH-17-26** mitigated (`assert_phase17_family_closed` at runtime including
its refusal of any pair naming `BASE_ROW`, `compare_cells`'s own `intruders` proof, `cell_rates`'s
structural drop, and the D-21 static scan over all four drivers — four layers, three watched
failing); **TH-17-45** mitigated (`assemble_matrix` `_prove`s the four-record contract and
`test_the_matrix_publishes_the_base_column` reads the numbers back out of both §The Matrix and the
all-fail branch's item (b), driven through `run_report_mode`); **TH-17-27** mitigated
(`report_proportion` for every rate, the source regex over all four drivers, the regex over the
RENDERED text inside the writer, and both clustering ends at every cell); **TH-17-28** mitigated
(`_verdict.recorded_verdict` clobber guard FIRST, watched firing with the sweep directory empty so
the ordering itself is proved); **TH-17-29** mitigated
(`assert_sweeps_ran_on_distinct_weights` now has its production caller, before scoring);
**TH-17-30** mitigated (`_prove` against the committed `SIGN_UNIT` literal in `compare_cells`,
watched firing under monkeypatch, plus a fixture where the two units order differently and the
draw-unit counterfactual computed); **TH-17-SC** holds — zero packages installed,
`pyproject.toml` byte-identical.

## Self-Check: PASSED

Files:

- FOUND: `scripts/phase17_isolation.py` (1937 lines, was 1172)
- FOUND: `tests/test_phase17_stats.py` (975 lines, was 380)
- FOUND: every symbol this plan claims — `run_report_mode`, `render_report`, `compare_cells`,
  `cell_rates`, `describe_matrix`, `read_sweep_records`, `draws_per_question`, `base_prior_anchor`,
  `assert_isolation_report_not_clobbered`, `prereg_commit`

Commits:

- FOUND: `c2acc0e` feat(17-08): add the report mode, the ISO-04 proof and the imported gate
- FOUND: `c9c3274` feat(17-08): add the report writer and the pre-registered D-10 all-fail branch
- FOUND: `2c363f0` test(17-08): pin the six-pairs scan, the question unit, the base row and the branch
