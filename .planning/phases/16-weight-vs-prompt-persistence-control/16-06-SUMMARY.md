---
phase: 16-weight-vs-prompt-persistence-control
plan: 06
subsystem: measurement
tags: [capability-ladder, run-driver, report-writer, clobber-guard, proxy-validity, unit-problem, pytest]

# Dependency graph
requires:
  - phase: 16 (plan 05)
    provides: "SYNTHETIC_VALUES / SYNTHETIC_FACT_ORDER (slots), build_near_prompt / build_far_prompt, ladder_distance, and the minimal --vet main() this plan extends"
  - phase: 16 (plan 04)
    provides: "the pre-registration this run is judged against — LADDER_CELL_PASS_K / _Z / _QUESTIONS / _DRAWS, LADDER_FLOOR_*, RUNG_DIFFICULTY_ORDER, cell_passed / cell_report / format_cell / licensed_headline / monotonicity_anomalies"
  - phase: 16 (plan 03)
    provides: "the every-draw_all-asserts guard — the new call site is covered IN PLACE, with no DRAW_ALL_ASSERTED_BY exemption"
  - phase: 16 (plan 02)
    provides: "assert_value_in_prompt (union of detectors) and the PERS-05 item-seed fix inside run_fairness_control, which the top rung re-runs"
  - phase: 14 (teach-then-recall)
    provides: "draw_all, score_question, contains_value, RecallItem, load_adapted_model, echo_provenance, run_fairness_control, SEED; results/phase16_recall_sample.json (binding fixture); results/phase14_recall_report.md:378 (the committed floor)"
  - phase: 15 (plan 04 CR-02)
    provides: "scripts/_verdict.py::VERDICT_SECTION / recorded_verdict — the one anchored verdict-section read the clobber guard imports"
provides:
  - "load_core_items() — the binding fixture's 216 core questions as RecallItems carrying its own seed indices, length PROVEN equal to LADDER_CELL_QUESTIONS"
  - "run_ladder_cell() — one cell: same 216 questions, same 9 draws, inside adapter_disabled, every prompt proven to carry its value before any draw"
  - "run_top_rung() — the D-11.1 fairness control RE-RUN post-fix on real taught values (D-13), by calling the shared control"
  - "floor_in_both_units() / top_rung_delta() — the committed floor in draws AND questions with the draw unit labelled forbidden, and the re-run's delta as structured data (D-19)"
  - "proxy_validity() + PROXY_FRAME_CAVEAT — D-15's subtraction, its divergence rule committed before either number existed, and the recorded frame caveat that travels inside the result"
  - "assert_ladder_report_not_clobbered() / write_ladder_report() — the report text, its verdict branch and its clobber guard, all committed before a single number exists"
  - "run_full_ladder() + the extended main() — no-argument default is the full run (16-07's entry point); --vet survives; an unrecognized argument still exits non-zero"
affects: [16-07, 16-08, 16-09, 16-10, 16-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A report section list is derived from globals() by prefix, so 'every LADDER_* constant is printed' is true by construction rather than by a hand-kept list"
    - "A caveat that qualifies a number travels INSIDE the dict carrying that number, so no renderer can emit one without the other"
    - "When a committed formatter's separator collides with the output format, swap the separator — never re-format the numbers"
    - "The writer _proves its own output matches the guard that will protect it, or the protection is nominal"
    - "A run driver refuses an argument it does not recognize rather than falling through to its default, when the default costs ~80 minutes"

key-files:
  created: []
  modified:
    - "scripts/phase16_ladder.py — +760/-9 lines: load_core_items, run_ladder_cell, run_top_rung, floor_in_both_units, top_rung_delta, proxy_validity, assert_ladder_report_not_clobbered, _rung_rows, write_ladder_report, run_full_ladder, extended main(); constants FIXTURE_PATH, NEAR_DISTANCE/FAR_DISTANCE, DRAW_UNIT_LABEL/QUESTION_UNIT_LABEL, PROXY_CELL, PROXY_DIVERGENCE_RULE, PROXY_FRAME_CAVEAT, LADDER_REPORT_PATH, D14_CLAUSE, REPORT_FRAMING"
    - "tests/test_phase16_ladder.py — +579 lines, 16 new tests (24 -> 40)"

key-decisions:
  - "cell_report is NESTED under 'cell' rather than merged into the cell result: its `questions` key is the DENOMINATOR while the result's is the per-question records, and merging would have destroyed one of the two silently"
  - "The value is resolved by item.fact.SLOT, not .id — SYNTHETIC_FACT_ORDER holds slots (16-05 Deviation 2), so the plan's literal `.index(item.fact.id)` would have raised on every question"
  - "The no-argument default becomes the full ladder run (16-07 invokes it bare), but an UNRECOGNIZED argument still exits non-zero — the refusal 16-05 built is kept where it still earns its keep"
  - "No --force flag on the ladder's clobber guard: an operator who learns a force flag is always needed passes it after a human has recorded a verdict (the 15-04 CR-02 failure mode)"
  - "The top rung's distance column reads 'not measured' rather than being back-filled: the taught statements end in a period, so ladder_distance would raise on every top-rung prompt at the END of an ~80-minute run"
  - "PROXY_FRAME_CAVEAT records 16-05's handover concern AS LOCKED — build_far_prompt's signature is unchanged, and the caveat makes the two D-15 verdicts asymmetric (CONSISTENT is stronger; DIVERGES cannot separate frame from material)"

requirements-completed: []  # PERS-01 requires the ladder to RUN (16-07); STAT-01/02/05 span phases 16/17/18 — same hold-back as 16-04 and 16-05
requirements-advanced: [PERS-01, STAT-01, STAT-02, STAT-05]

# Metrics
duration: 30min
completed: 2026-08-13
---

# Phase 16 Plan 06: The Executable Ladder — Cell Runner, Top Rung, Report Writer Summary

**The entire PERS-01 pipeline is now committed — the per-cell runner, the top rung, the D-15 proxy check, the exact text of the report and its verdict branch — before it has produced a single number. The ladder has NOT been run; that is plan 16-07.**

## Performance

- **Duration:** ~30 min wall clock (15:06 → 15:36 -03:00)
- **Tasks:** 3
- **Files created:** 0 · **Files modified:** 2
- **Tests added:** 16 (449 → 465 passed; 24 → 40 in `tests/test_phase16_ladder.py`)
- **Diff:** `scripts/phase16_ladder.py` +760/-9, `tests/test_phase16_ladder.py` +579

## Task Commits

1. **Task 1 — `run_ladder_cell`: one cell, 216 questions, 9 draws, value proven in view** — `ebcf1ef` (feat)
2. **Task 2 — the top rung, its delta against the committed floor, and D-15's proxy check** — `8314f64` (feat)
3. **Task 3 — the report writer, its clobber guard, and the full-run `main()`** — `f5f21ef` (feat)

## THE LADDER HAS NOT BEEN RUN

`results/phase16_ladder_report.md` does not exist and `git status --porcelain results/` is empty.
Plan 16-07 owns the run. Everything this plan produced is code and tests: the report's framing
paragraph, its pre-registration table, its unit table, its D-15 section, its monotonicity section
and its verdict branch are all in git **before** the numbers they will carry, which is the ordering
PERS-01 makes blocking.

The phase gate this plan owed 16-07 is discharged: **`465 passed, 1 skipped, 83 warnings in
117.36s`**, zero failed, zero errors, zero collection errors, against the orchestrator's
pre-dispatch baseline of `449 passed, 1 skipped`. Delta `+16` = exactly this plan's 16 new tests.

## What landed

### Task 1 — the cell is a parametrization of the committed instrument

`run_ladder_cell(model, tok, device, forbid, items, *, span, distance)` runs inside
`adapter_disabled(model)` and, per question: resolves the synthetic value by slot position, builds
the row's prompt, **proves the value is in view with `assert_value_in_prompt` before anything is
drawn**, measures the distance, proves the seed index is stamped, then draws through the shared
`draw_all` and scores through the shared `score_question`.

Nothing about the draw count is a parameter. It comes from `phase14_recall.draw_all` — 1 greedy +
`N_SEEDED_SAMPLES` — which is the same loop the committed floor was measured through.
`test_ladder_cell_draws_nine_times_per_question` pins it by returning a hit in **2 of 9 draws for
all 216 questions**, so `k = 432` and `n_answerable = 216` are two different numbers: a cell that
ever counted draws would return them equal, and the resulting bound would be nine times tighter
than the floor it is compared against.

`load_core_items()` reads the binding fixture's own `seed_index` verbatim — per arm, each
restarting at 0, exactly as `stamp_seed_indices` stamped them — and `_prove`s the length equals
`LADDER_CELL_QUESTIONS`. `test_load_core_items_matches_the_binding_fixture` also sha256s the
fixture before and after the call: Phases 17 and 18 consume that file unchanged.

### Task 2 — the top rung, both units, and D-15

`run_top_rung` builds the statements map exactly as `phase14_recall.main()` does and calls
`run_fairness_control` directly. It defines no loop of its own; the AST test asserts both halves,
because a parallel copy would drift from the arm it is compared against while still producing
something that looks like a delta.

`floor_in_both_units()` recomputes the five numbers 16-CONTEXT.md recorded, from
`erasure_gate.wilson_upper_bound` / `rule_of_three`, and the test pins them at `round(x, 6)`:

| unit | count | rate | one-sided 95% Wilson upper |
|---|---|---|---|
| draws — **the unit STAT-01 forbids for inference** | 1 of 1944 | 0.000514 | 0.002302 |
| questions — the STAT-01 unit | 1 of 216 | 0.004630 | 0.020482 |
| rule of three at 216 (the ceiling if it were zero) | — | — | 0.013889 |

Nine times the difference in the upper bound. Both are printed and the forbidden one carries its
label in the report, because citing the draw unit alone is what would make the prompt arm look far
more definitively at zero than the legal unit supports.

`proxy_validity` compares the `(5, 30)` synthetic cell against the top rung. `PROXY_CELL` is
derived as `RUNG_DIFFICULTY_ORDER[-2]` rather than retyped, and the divergence threshold is
`LADDER_CELL_PASS_K` itself (asserted by AST on the `Name`, not by comment), so no second literal
exists to be chosen once the two counts are on the table.

### Task 3 — a report whose text predates its numbers

`write_ladder_report` emits, in order: provenance · the framing paragraph (all-fail is
pre-registered and NORMAL; the instrument-broken signal is non-monotonicity) · the pre-registration
table · the 7-rung table · the top-rung section in both units with D-19 in prose · the D-15 section
with its caveat · the monotonicity section (which says "none" rather than being absent) ·
`## Verdict` = `licensed_headline()`'s own output plus the D-14 clause.

Both branch shapes were rendered end-to-end before commit — an all-fail ladder and a ladder with a
non-monotone pass — and checked for the bare-zero regex, the rung count, and the anchored verdict
section.

`assert_ladder_report_not_clobbered` imports `VERDICT_SECTION` / `recorded_verdict` from
`scripts/_verdict.py`; `'split("## Verdict")'` appears **0** times in the driver. There is
deliberately **no `--force`**: this report is written once, and the 15-04 CR-02 lesson is that a
force flag which becomes routine is a force flag that eventually destroys a hand-recorded verdict.

## The interface 16-07 will call, verified end to end

`.venv/bin/python scripts/phase16_ladder.py` (no arguments) is the full ladder run. Proven without
paying for the run: a fake report carrying a recorded verdict was placed at
`results/phase16_ladder_report.md`, the driver was invoked bare, and it **exited 1 in under a
second** with the guard's message — before preflight, before the model load. The fake file was then
removed and `git status --porcelain results/` confirmed empty.

```
[phase16_ladder] /Users/juliorcoelho/PersonaCore/results/phase16_ladder_report.md already carries
a recorded verdict — it is the committed PERS-01 licensing decision, recorded before any comparison
was scored. ...
EXIT=1
```

That is both halves of 16-07's contract in one observation: the bare entry point is the ladder, and
the clobber guard runs before anything expensive.

## Observed RED — two guards watched failing, both reverted byte-identical

A structural guard nobody has watched fail is a guard nobody has verified (the 15-03 precedent).
Both mutations were applied to `scripts/phase16_ladder.py` after Task 3 was committed and restored
from `git show HEAD:...` inside a `finally`; **`git diff --exit-code` was clean afterwards**.

**A — the new `draw_all` call site stops asserting in place** (deleted the
`assert_value_in_prompt` line from `run_ladder_cell`):

```
E           AssertionError: scripts/phase16_ladder.py::run_ladder_cell draws completions but calls
neither assert_value_in_prompt nor assert_no_value_in_prompt, and is not listed in
DRAW_ALL_ASSERTED_BY. Either assert in place, or name the caller that asserts on its behalf —
nothing draws unchecked.
E           assert None is not None
tests/test_phase14_scoring.py:632: AssertionError
FAILED tests/test_phase14_scoring.py::test_every_draw_all_call_site_asserts_something
1 failed in 0.80s

A RESTORED bytes-identical: True
```

This is the coverage route 16-05 handed forward (T-16-19) proving itself live: the distance-~2 row
is invisible to the `persona=` guard by construction, and this is what covers it.

**B — the pre-registration clause is quietly paraphrased** (`licencia só` → `licencia somente`):

```
E       AssertionError: assert 'licensed_hea...o silenciada.' == 'licensed_hea...o silenciada.'
E         Skipping 173 identical leading characters in diff, use -v to show
E         - licencia só o enunciado de déficit de capacidade do SC1. ...
E         ?           ^^^
E         + licencia somente o enunciado de déficit de capacidade do SC1. ...
E         ?           ^^^^^^^^
tests/test_phase16_ladder.py:1188: AssertionError
FAILED tests/test_phase16_ladder.py::test_report_carries_the_d14_verbatim_clause
1 failed in 0.08s

B RESTORED bytes-identical: True
```

The test rebuilds the clause from `16-CONTEXT.md`'s own blockquote — it does not compare two
literals — so a re-wrap in the driver cannot pass either (T-16-27).

## Verification

```
.venv/bin/python -m pytest tests/test_phase16_ladder.py -q
    40 passed                                     (24 from 16-04/16-05 + 16 new)

.venv/bin/python -m pytest tests/test_phase14_scoring.py tests/test_phase16_fixture_regen.py -q
    47 passed

.venv/bin/python -m pytest -q
    465 passed, 1 skipped, 83 warnings in 117.36s (0:01:57)

.venv/bin/python -m ruff check .              All checks passed!
.venv/bin/python -m ruff format --check .     145 files already formatted

grep -c 'split("## Verdict")' scripts/phase16_ladder.py     0
grep -c "VERDICT_SECTION"    scripts/phase16_ladder.py      3
git diff --stat results/phase16_recall_sample.json          (empty)
git status --porcelain results/                             (empty — the ladder has not run)
git status --short                    M .gitignore / ?? AGENTS.md  (both pre-existing)
git diff --diff-filter=D f582e4e HEAD                       (empty — no deletions in any task commit)
```

### Acceptance criteria, item by item

| Task | Criterion | Result |
|---|---|---|
| 1 | `pytest tests/test_phase16_ladder.py -q` exits 0 | 30 passed at that commit |
| 1 | plan's AST one-liner (`run_ladder_cell` contains a `with`) | exit `0` |
| 1 | `draw_all` / `score_question` imported; no local generation or scoring loop | AST-asserted by `test_ladder_cell_reuses_the_shared_instrument_rather_than_copying_it` |
| 1 | `run_ladder_cell` calls `assert_value_in_prompt`, no `DRAW_ALL_ASSERTED_BY` exemption | asserted, and observed RED above |
| 1 | `pytest tests/test_phase14_scoring.py -q` exits 0 | 42 passed |
| 1 | `pytest tests/test_phase16_fixture_regen.py -q` exits 0, fixture diff empty | 5 passed; diff empty |
| 2 | `pytest tests/test_phase16_ladder.py -q` exits 0 | 34 passed at that commit |
| 2 | `grep -c "def run_top_rung\|def top_rung_delta\|def proxy_validity\|def floor_in_both_units"` | **4** |
| 2 | AST: `run_top_rung` calls `run_fairness_control`, no `for` loop | asserted |
| 2 | `LADDER_FLOOR_*` unchanged — `git diff` on those three lines empty | empty (also for `LADDER_CELL_PASS_K`) |
| 2 | `proxy_validity`'s threshold is the `LADDER_CELL_PASS_K` Name | AST-asserted |
| 3 | `pytest tests/test_phase16_ladder.py -q` exits 0 with >= 25 collected | **40 collected, 40 passed** |
| 3 | `grep -c 'split("## Verdict")'` returns 0 | **0** |
| 3 | `grep -c "VERDICT_SECTION"` returns >= 1 | **3** |
| 3 | plan's importlib one-liner (< 3 s, has `main`) | exit `0`, **0.045 s** |
| 3 | D-14 clause byte-identical to `16-CONTEXT.md` | asserted against the file, and observed RED above |
| 3 | full suite green — the phase gate | **465 passed, 1 skipped** |

## Decisions Made

- **`cell_report` is nested under `"cell"`, not merged into the cell result.** The plan says
  "`cell_report(...)` merged in", but that row keys `questions` to the **denominator** while the
  result keys it to the **per-question records** — the shape `run_fairness_control` returns and the
  shape the top rung therefore has. A merge would have silently destroyed one of the two. The
  report converts both shapes through one path (`_rung_rows` → `cell_report(result["n_answerable"])`),
  so the seven rungs render identically regardless of which function produced them.
- **The top rung's distance is reported as "not measured", not back-filled.** The taught statements
  end in a period (`my name is <value>.`), so `ladder_distance` — whose contract is "the value ends
  a prefix of the prompt" — raises on them. Measuring it would have meant either a
  silent-fallback branch or a `ValueError` at the *end* of an ~80-minute run. The D-15 section says
  what was and was not measured instead.
- **No `--force` on the ladder's clobber guard.** Phase 14's guard has one; this one does not. If
  the report genuinely must be regenerated, the honest path is deleting it in a reviewed commit
  where the removal is visible in the diff.
- **The pre-registration table is derived from `globals()` by prefix.** "Every `LADDER_*` constant
  is printed" is then true by construction. The framing prose is named `REPORT_FRAMING` precisely
  so the prefix filter stays a prefix rather than becoming a judgement call — the first render
  dumped a two-paragraph blob into a table cell and named the fix.
- **An unrecognized argument exits non-zero.** 16-05 recorded that the argumentless refusal was a
  property, not an accident. The plan moves the default to the full run (16-07 invokes it bare), so
  the refusal was kept where it still matters: `--force` or a typo must not launch ~80 minutes of
  generation.

## Concerns recorded, implemented AS LOCKED

**1. D-15's two cells differ in FRAME as well as in material — 16-05's handover concern, decided
here.** `build_far_prompt`'s locked signature `(tok, question, value)` carries no fact id, so
`FAR_FRAME` is one fact-agnostic persona line for all eight facts, while `run_fairness_control`
uses each fact's own taught statement. For the name slot the two coincide; for the other seven the
synthetic cell's persona names a different slot than the question asks about. **Decided
explicitly, as the plan's silence and the dispatch both direct: implemented AS LOCKED, with the
caveat carried into the report.** `PROXY_FRAME_CAVEAT` is a module-level constant returned inside
`proxy_validity`'s dict, so no renderer can emit the number without it, and it names the asymmetry
the difference creates — `proxy_consistent` is the **stronger** reading because it holds despite an
extra difference, while `proxy_diverges` cannot separate the frame from the material.

**2. The `(5, 30)` row's distance is a distribution (13 / 26 / 60), not `~30`.** The report's rung
table prints min / median / max for every synthetic cell, and the column header says so. No prose
in the driver renders that row as a constant.

**3. `n_answerable` is only comparable to the floor at the floor's own draw count.** Both
`run_ladder_cell`'s docstring and `LADDER_CELL_DRAWS`'s committed comment say it; the draw count is
not a parameter of the cell runner, so it cannot be shaved for wall clock without editing the
shared instrument.

## Deviations from Plan

### 1. [Environment] `make test` substituted with the venv-explicit invocation

- **Plan text:** `<verification>` specifies `make test`; `<verify>` blocks specify `.venv/bin/pytest`.
- **What was run:** `.venv/bin/python -m pytest -q`, `.venv/bin/python -m ruff check .`.
- **Why:** recorded fact about this machine, same substitution as 16-01 through 16-05 — a bare
  `pytest` resolves to a pyenv 3.12 shim and yields ~63 spurious
  `ModuleNotFoundError: No module named 'torch'` collection errors across files this plan never
  touched. The gate actually run is the full suite the `make` target wraps.

### 2. [Rule 3 — Blocking] The synthetic value is resolved by `item.fact.slot`, not `.id`

- **Found during:** Task 1, writing the resolution line.
- **Issue:** the plan prescribes
  `SYNTHETIC_VALUES[span][SYNTHETIC_FACT_ORDER.index(item.fact.id)]`. `SYNTHETIC_FACT_ORDER` holds
  **slots**, not ids — 16-05 Deviation 2 made that substitution because every core fact id ends in
  its own value and a literal tuple of ids would have embedded eight locked values in the driver.
  `.index(item.fact.id)` would therefore raise `ValueError` on the first question of every cell.
- **Fix:** `.index(item.fact.slot)`, preceded by a `_prove` that the slot is in the committed order
  — a bare `ValueError` from `.index` names nothing, and this failure mode means the fixture and the
  material have drifted apart.
- **Files modified:** `scripts/phase16_ladder.py`
- **Committed in:** `ebcf1ef`

### 3. [Rule 1 — Bug] `cell_report` nested rather than merged (key collision)

- **Plan text:** "and `cell_report(...)` merged in".
- **Issue:** `cell_report`'s row and the cell result both use the key `questions`, for the
  denominator and for the per-question records respectively. A merge silently drops one.
- **Fix:** nested under `"cell"`; the records keep the meaning `run_fairness_control` gives them,
  which is what lets the writer render synthetic cells and the top rung through one path.
- **Committed in:** `ebcf1ef`

### 4. [Structure] `test_main_is_guarded()` was not added — it already exists

- **Plan text:** Task 3 lists `test_main_is_guarded()` — "assert the module has a `main` attribute
  and that the AST contains an `if __name__ == "__main__":` block".
- **What landed:** nothing new. 16-05's committed `test_main_exists_and_is_guarded` asserts exactly
  that (plus that the guard calls only `main`, and that torch and the fact set are not module-level
  imports), and it still passes. A second identical test would be two assertions to keep in sync.
- **Instead:** `test_main_still_supports_vet_and_defaults_to_the_full_ladder` covers the behaviour
  this plan actually changed, including the unrecognized-argument refusal.

### 5. [Structure] The `--vet` mode is checked behaviourally, not as an "argparse spec"

- **Plan text:** "`test_main_still_supports_vet()` — the argparse spec still accepts `--vet`".
- **What landed:** the driver uses plain `sys.argv` inspection (16-05's shape, unchanged), so the
  test monkeypatches both entry points and `sys.argv` and asserts which one ran. That is a stronger
  check than reading a parser spec, and introducing `argparse` for two modes would have been a
  rewrite of the `--vet` branch the plan explicitly forbids.

### 6. [Rule 2 — Missing validation] An unrecognized argument exits non-zero

- **Not in the plan**, which specifies only that the no-argument default becomes the full run.
- **Why added:** a mistyped flag would otherwise silently launch ~80 minutes of generation. That is
  input validation at the one trust boundary this driver has, and it preserves the property 16-05
  recorded as deliberate.

### 7. [Structure] Two extra tests beyond the plan's list

- `test_ladder_cell_reuses_the_shared_instrument_rather_than_copying_it` makes Task 1's third and
  fourth acceptance criteria structural rather than manual greps.
- The partial-ladder refusal is asserted inside
  `test_report_writer_emits_every_rung_and_no_bare_zero_percent`: a six-row table rendered as the
  committed ladder would present a partial measurement as a complete one while every individual
  number stayed correct.

---

**Total deviations:** 7 (1 environment, 2 blocking/bug fixes forced by upstream reality, 3
structure, 1 Rule 2 validation). **No behaviour the plan specifies was removed.** Every function
name, constant name, section, threshold and verdict string is as locked.

## Issues Encountered

- **The first rendered report leaked `LADDER_FRAMING` into the pre-registration constants table**
  — the table is derived by the `LADDER_` prefix, and the framing prose matched it. Found by
  rendering the report end-to-end before committing, not by reading. Fixed by renaming the constant
  to `REPORT_FRAMING` rather than by special-casing the filter.
- **Four report paragraphs were built as separate list entries and wrapped mid-clause** — the same
  defect 16-05 re-ran the vetting run to avoid. Joined into single implicit-concatenated strings so
  each paragraph is one output line.
- **`statistics.median` over 216 items returns a float**, so the distance column formats the median
  with `:g` (renders `26`, not `26.0`, and `26.5` when the two middle values differ).
- **No package was installed and none was needed.** `pyproject.toml` is byte-unchanged, so 16-01's
  STAT-04 freeze was never approached (T-16-SC).
- **The identifier D-10 declares non-existent** stayed out of the touched files, all three commit
  messages and this summary.

## Next Phase Readiness

- **16-07 can run immediately.** The gate it requires is green (`465 passed, 1 skipped`), the entry
  point is verified, and the working tree carries only the two pre-existing unrelated items.
- **Expect ~1512 per-question progress lines in the raw log**, plus one `===== rung ... =====`
  banner and one `format_cell` summary per rung, plus the provenance echo. `2>&1 | tee
  results/phase16_ladder_raw.log` captures all of it.
- **The report will be written once.** A second bare invocation over a recorded verdict exits 1
  before the model loads. If the run dies mid-way, no report exists and a re-drive is unblocked —
  but the wall clock is paid again.
- **The top rung prints through `run_fairness_control`**, so its per-question lines are tagged
  `[phase14_recall]` and carry locked fact values in the persona spans. That is the one sanctioned
  in-context placement (T-16-31 accepts it), already true of the committed Phase 14 transcripts.
- **`proxy_validity`'s verdict is what 16-10's report writer must carry forward.** If it comes back
  `proxy_diverges`, every low rung is suspect and the four-arm report must say so — and
  `PROXY_FRAME_CAVEAT` must travel with it, because divergence cannot be attributed to the material
  alone.

## Self-Check: PASSED

`scripts/phase16_ladder.py` carries every claimed symbol — `load_core_items`, `run_ladder_cell`,
`run_top_rung`, `floor_in_both_units`, `top_rung_delta`, `proxy_validity`,
`assert_ladder_report_not_clobbered`, `_rung_rows`, `write_ladder_report`, `run_full_ladder`,
`main`, `D14_CLAUSE`, `PROXY_CELL`, `PROXY_FRAME_CAVEAT`, `LADDER_REPORT_PATH` — all located by
grep and all exercised by the 40-test file run. All three task commits resolve in `git log`:
`ebcf1ef`, `8314f64`, `f5f21ef`; none deletes a tracked file. Both deliberate-RED observations were
run and their output is reproduced verbatim above; both mutations restored byte-identically with
`git diff --exit-code` clean. Full suite `465 passed, 1 skipped`, ruff clean.
`results/phase16_ladder_report.md` does **not** exist — the ladder has not been run. Working tree
carries only the two pre-existing unrelated items this plan did not touch: modified `.gitignore`,
untracked `AGENTS.md`.

---
*Phase: 16-weight-vs-prompt-persistence-control*
*Completed: 2026-08-13*
</content>
</invoke>
