---
phase: 16-weight-vs-prompt-persistence-control
plan: 10
subsystem: evaluation
tags: [PERS-02, PERS-03, STAT-02, STAT-05, STAT-06, D-25, D-26, D-27, D-28, sweep, report-writer]

# Dependency graph
requires:
  - phase: 16 (plan 07)
    provides: "the COMMITTED capability ladder — licensed_headline, floor_in_both_units and the span_2 branch this report cites rather than restates"
  - phase: 16 (plan 08)
    provides: "CONDITION_ORDER, SHARED_ARM_CONFIG, PARITY_COLUMNS, assert_arm_parity, load_fixture_items, run_condition, candidate_pool"
  - phase: 16 (plan 09)
    provides: "aggregate_by_fact, cluster_bootstrap, report_proportion, compare_arms, taught_replication — every published rate and the one gate"
  - phase: 14 (teach-then-recall)
    provides: "run_fairness_control (the arm the sweep pressures), echo_provenance, load_adapted_model"
provides:
  - "sweep_cells / build_diluted_persona / build_overwrite_statement / run_sweep — PERS-03 as ONE dilution axis with truncation derived from crossing block_size"
  - "write_persistence_report + assert_persistence_report_not_clobbered — every pre-registered clause committed BEFORE the run that fills it"
  - "main(): --condition NAME | --report, with no mode capable of running two arms"
  - "assert_arm_parity WIRED at last, pinned structurally and live"
  - "the context_length _prove against the LOADED model_cfg that 16-08 asked this plan to add"
affects: [16-11, 17, 18]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A second pressure is DERIVED from the first's crossing point, never declared as its own axis"
    - "A verbatim clause whose text collides with a committed source guard is READ from its artifact, never retyped as a constant"
    - "A permission (D-28) is rendered in the SAME paragraph as the ceiling that bounds it — a permission printed alone is the sentence a reader quotes"
    - "A length is a DISTRIBUTION: every prompt length goes through _length_spread, never rendered as its target"
    - "Object identity that cannot survive a file is re-established only AFTER each recorded column is proven equal to the live object's field"

key-files:
  created: []
  modified:
    - "scripts/phase16_persistence.py — 1249 -> 2785 lines: the sweep, the report writer, main()"
    - "tests/test_phase16_driver.py — 754 -> 1725 lines, 29 -> 69 tests"

key-decisions:
  - "D-25's verbatim qualifier is READ from 16-CONTEXT.md at report time, not stored as a constant — a constant would put a second 0.125 in the module and tests/test_phase16_driver.py:627 pins that count at 1"
  - "build_diluted_persona returns a dict (lines + measurements) rather than a bare line list, so the caller never re-measures what the builder already knows"
  - "The dilution fill is a hill-climb (closest to target), not greedy longest-that-fits — greedy left a 6-token gap on some statements"
  - "The overwrite competitor is the NEXT pool member after the fact's own value, wrapping; slot matching is NOT attempted and is recorded rather than repaired"
  - "run_one_condition threads the LOADER's forbid mask (structural parity with Phase 14) and uses resolve_forbid to PROVE the published hash describes it"

requirements-completed: [PERS-02, PERS-03, STAT-02, STAT-05]

# Metrics
duration: 95min
completed: 2026-08-13
---

# Phase 16 Plan 10: The PERS-03 sweep, the report writer, and one condition per process Summary

**The last code before the un-re-runnable four-arm run: SC5's three "parallel" pressures resolved
into ONE dilution axis whose truncation cells are derived from crossing `block_size`, a report
writer whose every clause was committed before a number existed to fit it, and a `main()` that is
structurally incapable of running two arms.**

## Performance

- **Duration:** ~95 min wall clock
- **Tasks:** 3
- **Files modified:** 2 · created: 0
- **Tests added:** 40 (534 → 574 passed)

## Task Commits

1. **Task 1 — the PERS-03 sweep** — `68340d8` (feat)
2. **Task 2 — the report writer and its clobber guard** — `daac1f1` (feat)
3. **Task 3 — `main()`, one condition per process** — `fd6417f` (feat)

---

## The three obligations this plan inherited — all three closed

### 1. `assert_arm_parity` is now CALLED

16-08 defined it; 16-08's and 16-09's summaries both recorded that nothing called it. It is now
invoked in `run_report_mode`, and pinned **two** ways so a future edit cannot drop it in silence:

- **Structurally** — `test_report_mode_calls_assert_arm_parity` walks the AST and asserts the set
  of functions calling it is exactly `{"run_report_mode"}`. Not `in`: hard equality, so both a
  dropped call and a stray second one turn it red.
- **Live** — the same test writes four arm files whose `forbid_ids_sha256` disagree and asserts
  `SystemExit`. A present-but-dead call would pass the AST half and fail this one.

The identity half of that assertion (`config["shared_arm_config"] is SHARED_ARM_CONFIG`) cannot
survive a JSON round trip, so it is **not** written to disk and **not** rehydrated blind:
`assert_recorded_config_matches_the_shared_object` proves every recorded column equals the live
object's own field FIRST, and only then restores the reference. What `assert_arm_parity` adds on
top is the genuinely cross-process check no single record can make — that all four arms recorded
the same `forbid_ids` content hash.

### 2. `context_length` is `_prove`d against the LOADED `model_cfg`

`ArmConfig.context_length` reads `ModelConfig.block_size` — the **dataclass default**. The run
loads its config from `convbase_slim.pt`. They agree today, and `assert_arm_parity` would keep
passing if they stopped (all four arms read the same default) while the published column described
a context length the model does not have. `run_one_condition` now carries:

```python
_prove(model_cfg.block_size == SHARED_ARM_CONFIG.context_length, ...)
```

pinned by AST in `test_sweep_runs_only_for_the_prompt_stuffed_condition`. A second `_prove` in the
same place asserts the loader's `forbid` mask digest equals `resolve_forbid`'s, so the published
hash provably describes the mask the arms actually generated under.

### 3. The degenerate `proxy_consistent` verdict is explicitly NOT cited

The report does not cite it as validation of anything, and says so, in `## Verdict` directly beside
the ladder citation a reader would otherwise follow into it:

> **This report does not cite the ladder's D-15 `proxy_consistent` verdict as validation of
> anything.** That check compared two cells which BOTH scored zero answerable questions out of 216,
> so they agree trivially: a difference of zero is what two dead cells produce whether or not the
> synthetic substitution was fair. […]

`test_report_headline_is_imported_from_the_ladder` pins its presence.

---

## The sweep, measured

`SWEEP_PROMPT_TARGETS = (46, 96, 160, 224, 320, 448)`. `SWEEP_BLOCK_SIZE` is `ModelConfig.block_size`
with a **module-level** `_prove` at 256 — a config change is a loud import failure, not a quietly
relabelled sweep. An AST test asserts its assigned value is not a literal.

Measured on the real frozen tokenizer over all **ten** committed statements, and on the real
`build_recall_prompt` over all **270** fixture questions:

| target | pressure label | achieved, nominal (min / median / max) | crosses | statement head offset | statement outside trailing 256 | REAL prompt len (min / median / max) |
|---|---|---|---|---|---|---|
| 46 | `dilution` | 44 / 46.5 / 58 | no | **1** | 0 / 270 | 26 / 43 / 88 |
| 96 | `dilution` | 93 / 96 / 97 | no | **1** | 0 / 270 | 77 / 90.5 / 124 |
| 160 | `dilution` | 159 / 160 / 162 | no | **1** | 0 / 270 | 141 / 155 / 192 |
| 224 | `dilution` | 222 / 224.5 / 226 | no | **1** | 0 / 270 | 203 / 219 / **256** |
| 320 | `dilution + truncation` | 318 / 319 / 321 | **yes** | **1** | **270 / 270** | 300 / 314 / 349 |
| 448 | `dilution + truncation` | 445 / 447.5 / 451 | **yes** | **1** | **270 / 270** | 426 / 443 / 480 |

**Exactly two cells cross**, and the crossing is derived — `pressure_label` is computed from
`target > SWEEP_BLOCK_SIZE`, never declared. `grep -c "TRUNCATION_TARGETS\|TRUNCATION_CELLS"`
returns **0**, and an AST test asserts no constant whose name starts with `TRUNCATION` exists and
that only `sweep_cells` and `run_sweep` read `SWEEP_PROMPT_TARGETS`.

**The statement's head offset is 1 on every cell of every fact** — its ids begin immediately after
`<|system|>`, proven inside `build_diluted_persona` rather than assumed. Its conservative end
offset (statement + its newline separator, so any BPE merge across that boundary counts INSIDE the
run) is 13–27 ids across the ten statements.

**The truncated cells provably drop it.** `test_truncated_cells_actually_drop_the_statement` builds
the prompt through the REAL `build_recall_prompt`, takes `prompt_ids[-256:]`, and asserts the
statement's id sequence is **not a contiguous subsequence of that window** — and that it IS present
on every non-crossing cell. Measured over all 270 questions above: **270/270 outside on both
crossing cells, 0/270 on all four others.**

### Three measured facts worth recording

- **The 224 cell's longest real prompt is exactly 256 tokens.** `generate` crops only when
  `idx.size(1) > bs`, so no crop occurs at exactly 256 — the cell is correctly labelled `dilution`,
  but it sits ON the boundary. The report prints `n_over_block_size` per cell from the run's own
  measured lengths, so a question that did cross would be visible rather than assumed away.
- **The committed nominal `33 bare` is not what the fixture reproduces.** Over the binding
  fixture's own 270 questions the bare prompt runs **14 / 28 / 63** tokens (min / median / max).
  33 is the cited nominal used for length TARGETING only; every cell records and publishes its
  measured distribution beside its target. This is the 16-07 lesson applied (the far row is
  13/26/60, never "~30").
- **The two soft-tier statements cannot reach the 46 cell.** Their spans are 25 and 22 ids against
  the 13-id nominal, so cell 1 lands at 58 and 55 for them. `overshoots_target` records it per
  fact; nothing is trimmed and nothing aborts. The eight core statements are 11–15 ids and land
  within ±3 on every cell.

### The overwrite cell

A **statement string**, not a prompt — `grep -c "build_overwrite_prompt"` returns **0**, and
`test_overwrite_returns_a_statement_not_a_prompt` asserts the function does not exist:

```
'my name is quillon. actually it is zibby.'
'i was born in 1987. actually it is 4429.'
```

The competitor is the next member of the sorted committed 20-value pool after the fact's own value,
wrapping — deterministic, zero editorial judgment (D-23). **Slot matching is NOT attempted and that
is recorded rather than repaired**: the committed lexicon carries no slot partition, and inventing
one would be exactly the judgment that lexicon was chosen to avoid. `ADVERSARIAL_OVERWRITE_NOTE`
states this in the report.

**`sweep_cells()` returns 6; `run_sweep` returns 7.** The overwrite is a seventh run on its own
axis at nominal length, labelled `adversarial overwrite (own axis, nominal length)` — neither
`dilution` nor `dilution + truncation`. `test_run_sweep_covers_six_on_axis_cells_plus_the_overwrite`
pins the 6-vs-7 relationship so a future edit cannot drop the row by rendering `sweep_cells()`.

### Zero new call sites — `PERSONA_ALLOWLIST` is still exactly 2

```
(('scripts/phase14_recall.py', 'run_fairness_control'),
 ('scripts/phase16_ladder.py',  'build_far_prompt'))
DRAW_ALL_ASSERTED_BY: 1
```

Every cell routes through the existing `statements` map. `_persona_span_ids` measures the span with
`tok.encode(detokenize(...))` — reproducing exactly what `encode_dialogue` will do
(`serialize.py:82`) — **specifically to avoid** a `build_recall_prompt(..., persona=...)` call site,
because D-21's guard is hard equality and this plan does not touch `tests/test_phase14_scoring.py`
(`git diff --stat` on it is empty across all three commits).

---

## The report writer

Ten sections, in order: Run Provenance (four condition blocks + the assembly block) · What This
Report Is · Run Design · Arm Parity · Per-Fact Results (gated tier) · The Inferential Gate ·
Taught Replication · The Arm-D Structural Floor · Context Pressure · The Floor in Both Units ·
Verdict. Rendered end to end from constructed records: **220 lines, 26.7 KB.**

- **No bare `0%`** — `write_persistence_report` `_prove`s `re.search(r"\b0(\.0+)?%", text) is None`
  on its own output before writing, and a test renders an arm scoring nothing on every fact so the
  zero path is the one under test.
- **The headline is `licensed_headline`'s output.** `committed_ladder_rungs()` reads the branch and
  highest passed rung from `results/phase16_ladder_report.md`'s `## Verdict` section, matches the
  rung back against `RUNG_DIFFICULTY_ORDER` (never parses it), feeds it through
  `ladder.licensed_headline`, and `_prove`s the returned branch equals the one the ladder recorded.
  Resolved live: `((2, 2),) -> span_2`, cited at commit `5a17920`. A test asserts no ladder branch
  statement is duplicated in this module's source.
- **`39.2` is absent** from the module and from every render; `~39 min (35-44 min)` with the 11.5%
  cross-run spread as the stated reason.
- **`0.125` appears exactly once** in the rendered report, inside the D-25 verbatim quote in the
  reconciliation section; `0.05` is the number every computation uses.
- **Both floor units**, with `DRAW_UNIT_LABEL` naming the draw unit as the one STAT-01 forbids.
- **Six Holm rows**, `0.05 / 6 = 0.0083333` formatted from the constants; the taught replication
  table carries no alpha and no rejection column at all.
- **`NOT_DEMONSTRABLE`** is a committed string rendered when no pair clears — a test exercises that
  branch with an all-tied fixture and asserts all six p-values render as `1.0000000`, none rejected.

### D-28 rendered with its ceiling attached

`monotone_claim_allowed` is implemented **as locked** (True for every branch but `no_rung_passed`),
so `span_2` permits the claim. The rendered paragraph is `MONOTONE_CLAIM_LICENSED`, a constant
committed before the run, and it carries the bound in the same breath as the permission:

> D-28's condition is met at the branch level: the committed ladder branch is `span_2` […] **That
> is the whole of what is licensed, and the branch statement in `## Verdict` bounds it.** A
> monotone reading of the cells above describes the degradation of a capability the ladder LOCATED
> at that rung — not of this arm's ability to carry the real taught values, which are longer than
> the passing rung's span and on which every longer-span rung failed. Read the two together or
> neither.

This was written after reading the first render, where the permission stood alone as "monotone
degradation MAY be read off the cells above". That sentence was true under D-28 and would have been
quoted without its ceiling. Recorded here because the fix is the plan's own
`<report_writer_discipline>` applied to a paragraph, not to a number.

---

## `main()` — one condition per process

`--condition NAME` (required, `choices=CONDITION_ORDER`) **or** `--report`, mutually exclusive.
`grep -c '"--all"'` returns **0**; a test reads the argparse spec and asserts no such flag exists.
Measured:

```
.venv/bin/python scripts/phase16_persistence.py                      -> exit 2, names --condition
.venv/bin/python scripts/phase16_persistence.py --condition bogus    -> exit 2, lists the four legal names
```

`run_report_mode` refuses to assemble on any of: a missing arm, a `git_sha` mismatch, fewer than
four distinct pids, differing `(fact_id, split, seed_index)` sets, a failed parity column, or a
sweep count other than one. Each refusal has its own test. The pairing check uses the **triple**
rather than the bare `seed_index`, because every arm's bare index set is `0..n-1` and would match
trivially while the questions behind it differed.

Import cost measured at **0.53 s** (budget 3 s); `main` is called at module level exactly once and
only under the `__name__` guard, asserted by AST.

---

## Verification

```
.venv/bin/python -m pytest tests/test_phase16_driver.py tests/test_phase16_stats.py -q
    80 passed        (Task 1 gate)
.venv/bin/python -m pytest tests/test_phase16_driver.py -q
    59 passed        (Task 2 gate)
.venv/bin/python -m pytest tests/test_phase16_driver.py tests/test_phase16_stats.py \
                          tests/test_phase16_ladder.py -q
    149 passed       (Task 3 gate)

.venv/bin/python -m pytest -q
    574 passed, 1 skipped, 83 warnings in 122.39s (0:02:02)

.venv/bin/python -m ruff check .            All checks passed!
.venv/bin/python -m ruff format --check .   148 files already formatted

git diff --stat pyproject.toml results/     (empty)
git diff --stat tests/test_phase14_scoring.py  (empty)
git status --short                          (empty)
ls results/ | grep -c phase16_arm            0
```

**Baseline was `534 passed, 1 skipped`. Result `574 passed, 1 skipped`. Delta `+40` = this plan's
40 new tests (15 + 14 + 11). Zero failed, zero errors, zero collection errors.**

### Acceptance criteria, item by item

| Criterion | Result |
|---|---|
| Task 1 gate (`driver` + `stats`) exits 0 | **80 passed** |
| `sweep_cells()` is 6 cells, exactly 2 crossing (importlib) | exit 0 |
| `grep -c "TRUNCATION_TARGETS\|TRUNCATION_CELLS"` | **0** |
| `SWEEP_BLOCK_SIZE` assigned value is not a literal (AST) | asserted by test |
| `sweep_applicability()` — 4 entries, each with a non-empty reason | exit 0 |
| `test_context_pressure_sweep_is_not_gated` still green against the real sweep | passed |
| `grep -c "build_overwrite_prompt"` | **0** |
| `tests/test_phase14_scoring.py` green; `PERSONA_ALLOWLIST` == 2; `git diff --stat` empty | 42 passed, **2**, empty |
| Crossing cells' statement outside the trailing 256 window, asserted not eyeballed | 270/270 both cells |
| Task 2 gate exits 0 | **59 passed** |
| `grep -c '39.2'` | **0** |
| `grep -c 'split("## Verdict")'` = 0 and `grep -c VERDICT_SECTION` >= 1 | **0**, **3** |
| D-03 / D-07 / D-25 byte-identical to `16-CONTEXT.md`, asserted against the file | passed |
| `grep -c "import phase16_ladder"` >= 1 | **1** |
| Four parity column headers + four provenance blocks in a render | passed |
| Task 3 gate (`driver` + `stats` + `ladder`) exits 0 | **149 passed** |
| Argumentless invocation exits non-zero naming `--condition` | **exit 2** |
| `grep -c '"--all"'` | **0** |
| Import under 3 s with `main` present | **0.53 s** |
| Full suite green (venv form — the phase gate for 16-11) | **574 passed, 1 skipped** |

---

## Deviations from Plan

### 1. [Interface] `build_diluted_persona` returns a dict, not a bare line list

- **Plan text:** "`build_diluted_persona(tok, statement, target_tokens)` -> a persona line list …
  Return the line list, and record per cell: the measured prompt length, and the statement's token
  offset."
- **What landed:** a dict carrying `lines` plus `achieved_prompt_tokens`, `overshoots_target`,
  `persona_span_tokens`, `statement_head_offset` and `statement_end_offset`.
- **Why:** the plan requires those measurements recorded per cell, and the builder is the only place
  that knows them. Returning the list alone forces the caller to re-measure, which is a second place
  the measurement can be wrong — and a wrong offset is invisible in the rate it accompanies. Both
  readings of the plan are satisfied: `["lines"]` is the line list.

### 2. [Guard hygiene] D-25's verbatim text is READ from `16-CONTEXT.md`, not stored as a constant

- **Plan text:** implies a module-level constant in the D-03 / D-07 register.
- **What landed:** `arm_d_qualifier()`, which extracts the blockquote following `- **D-25:**` from
  `16-CONTEXT.md` at report time.
- **Why:** that text contains the superseded chance-floor figure, and
  `tests/test_phase16_driver.py:627` — committed in 16-08 — pins this module's source at **exactly
  one** occurrence of it, in the comment beside `COSINE_CHANCE_FLOOR` that records the
  reconciliation. A constant would be a second occurrence. The committed guard is substantively
  right, so the fix went on this side of the line (the 16-09 deviation-4 precedent), and reading the
  source of truth is *stronger* than a retyped constant: "verbatim" checked against a second
  hand-typed copy proves only that two copies agree.
- **Two further collisions with committed 16-08 guards, both resolved the same way:** the blockquote
  reader originally used the str prefix METHOD, which
  `test_cosine_arm_is_scored_by_contains_value` forbids anywhere in this module's source so that no
  second scoring predicate can live beside `contains_value`. Replaced with a slice. The comment
  explaining the change then *named* the forbidden token and tripped the same guard again — the
  exact category error 16-09 recorded as its deviation 4 — and was reworded. **No committed guard
  was touched.**

### 3. [Method] The dilution fill is a hill-climb, not greedy longest-that-fits

- **What was tried first:** append the longest filler line that still fits, stop when none does.
  Measured: a 6-token gap on some statements (96 → 90, 160 → 154), outside the ±5 the plan's test
  requires.
- **What landed:** at each step append whichever line brings the built prompt CLOSEST to the target;
  stop when no line improves it. Measured: within ±3 on every cell the statement can reach.
- **Why not just widen the tolerance:** the shortest line in this near-character-level vocabulary
  costs ~5 ids, so ±5 is roughly the structural floor; widening it would have hidden a fixable
  builder weakness behind a looser test.

### 4. [Structure] `run_sweep`'s `_prove` on the statements/values key sets

Not in the plan text. `run_sweep` needs each fact's own value for the overwrite cell and reads it
off the ITEMS (never parsed back out of the statement string). A partial `statements` map would have
raised `KeyError` **after** the six dilution cells had already spent an hour. Added as Rule 2
(missing critical functionality): the abort names both directions of the mismatch.

### 5. [Environment] `make test` / `make lint` substituted with venv-explicit invocations

Same recorded substitution as 16-01/16-02/16-03/16-08/16-09: a bare `pytest` resolves to a pyenv
3.12 shim and yields ~63 spurious `ModuleNotFoundError: No module named 'torch'` collection errors
across files this plan never touched. The gate actually run is the full suite the `make` target
wraps.

---

**Total deviations:** 5 (1 interface, 1 guard hygiene, 1 method, 1 Rule-2 addition, 1 environment).
**One deviation under rules 1-4** — deviation 4, a missing abort on a partial input. No bug was
found in committed code, no locked value was altered, and no committed guard was weakened.

## Concerns recorded, implemented AS LOCKED

**`monotone_claim_allowed("span_2")` returns True, and D-28 is why.** D-28's condition is
branch-level: "the capability ladder got that arm off the floor". The `(2, 2)` rung passed at
15/216, so a rung passed. But the passing rung carried a **two-token synthetic** value while the
material this comparison scores is 4–8 tokens, and every longer-span rung scored 0/216. Implemented
exactly as locked; the concern is discharged by rendering the ceiling in the same paragraph as the
permission (see above) rather than by changing the predicate. **If a reviewer wants the stricter
reading — no monotone claim at all below `span_5_synthetic` — that is a decision for a human, not a
change to make while implementing.**

**The 224 cell's longest real prompt is exactly 256 tokens, and `generate` does not crop at 256.**
Correct as labelled, but it is a one-token margin. The report prints `n_over_block_size` from the
run's own measured lengths, so if a question ever does cross on a `dilution`-labelled cell the
artifact shows it. Not adjusted: moving the target to fit the margin would be tuning the axis after
seeing a measurement.

**The sweep's first cell IS the undiluted arm.** At target 46 no filler fits for the core facts, so
cell 1 re-runs arm B at nominal length on the same axis. That is deliberate — it is the baseline row
every later cell is read against — but it means one of the seven runs duplicates work the
prompt-stuffed arm already did. The duplication is ~14 min of the ~100 min budget and buys a
same-process, same-seed baseline; recorded rather than optimized away.

**Arm D's realized `n_draws` is 1 while its parity column reads 9.** The column is the SHARED
budget, which is what PERS-02 asserts parity over; D-22's single deterministic draw is stated inline
in the same table cell. The alternative — printing 1 — would have made the parity table disagree
with `assert_arm_parity`, which requires all four `n_draws` equal.

## Issues Encountered

- **`build_recall_prompt(..., persona=...)` was the obvious way to measure a built prompt, and it is
  forbidden here.** D-21's `PERSONA_ALLOWLIST` is hard equality over `scripts/*.py` + `src/**/*.py`,
  and this plan may not touch that file. `_persona_span_ids` reproduces `encode_dialogue`'s own
  persona encoding (`serialize.py:82`) instead. A three-positional call would have evaded the
  keyword check — it was considered and rejected as guard evasion, not compliance.
- **`|diff|` inside a markdown table cell split the row into extra columns.** Found by reading the
  first render, not by a test. Fixed (`max ABSOLUTE DIFFERENCE`), and
  `test_report_tables_have_no_pipe_bearing_cells` now checks every table's row widths agree.
- **Two directional references in the report prose were wrong** ("the cell below" for a caveat that
  renders after its table; "the branch cited below" for a branch cited above). Also found by
  reading the render. Both fixed.
- **`json` was not imported in `tests/test_phase16_driver.py`** — added for the Task 3 arm-file
  fixtures.
- **PERS-03 was marked Complete in `REQUIREMENTS.md` because this plan's frontmatter lists it, and
  its wording says "is MEASURED" — which is 16-11's job, not this one's.** What this plan
  discharged is the instrument: the axis, the cells, the crop evidence, the applicability table and
  the report section. No question has been scored under pressure yet. The checkbox has no per-plan
  granularity (PERS-01 is still `Pending` even though its ladder RAN and was committed in 16-07),
  so this line is the caveat that would otherwise be missing — the same shape 16-09 recorded for
  STAT-01/02/06. **If 16-11 does not run, PERS-03 is not satisfied regardless of the checkbox.**
- **No model was loaded, no generation was run, no package was installed.** `pyproject.toml` and
  `results/` are byte-unchanged across all three commits; no `results/phase16_arm_*.json` and no
  `results/phase16_persistence_report.md` exist. Every report render in the test suite writes to a
  `tmp_path`.
- **`DEGEN-2` (D-10) stayed out of all three commits, both files, and this summary** beyond this
  sentence naming it as absent.

## Next Phase Readiness — 16-11 may run

The phase gate is green: **574 passed, 1 skipped, 0 failed, 0 errors.**

- **The five entry points 16-11's plan names all exist and behave as it expects:**
  `--condition adapter-only | base-neither | embedding-cosine | prompt-stuffed`, then `--report`.
  `prompt-stuffed` also runs the sweep; no other condition can.
- **Launch each detached and verify it** (16-07's 50-minute lesson): `nohup … > log 2>&1 &` then
  `disown`, confirm `ps -o ppid= -p <pid>` returns **1** — `setsid` does not exist on macOS — and
  wrap in `caffeinate -ims`.
- **The repo is COMMIT-FROZEN for the duration of the run.** Not by `assert_sha_unchanged` (that
  guard is the ladder's), but by `assert_arms_are_pairable`: the four arms must record ONE
  `git_sha`, so a commit landing between arm 1 and arm 4 makes `--report` refuse to assemble. Land
  every commit before launching arm 1.
- **Budget:** ~39 min for the four arms (35–44 min), **plus 100 min to ~3 h for the sweep alone**,
  all of it inside the `prompt-stuffed` invocation. A single sweep cell taking 2 h is EXPECTED. Do
  not kill it, do not restart it, do not drop cells.
- **`--report` writes the report once and there is no force flag.** `assert_persistence_report_not_clobbered`
  refuses a second write, so a re-run to "get a different number" is blocked by construction.
- **The sweep's soft-tier facts overshoot cell 1** (58 and 55 against a 46 target). That is recorded
  per fact in `overshooting_facts` and is expected in the run's output — not a fault.

## Threat Flags

None. Both files are CPU-only and non-networked. The one new file-write surface
(`arm_record_path` / `PERSISTENCE_REPORT_PATH`) writes only under `results/`, is redirected to a
`tmp_path` in every test, and is protected by a clobber guard. `ladder_report_commit()` shells out
to `git log` read-only, in the register `capture_run_provenance` already established.

## Self-Check: PASSED

Both modified files exist on disk carrying every claimed symbol — `scripts/phase16_persistence.py`
(`SWEEP_BLOCK_SIZE`, `SWEEP_PROMPT_TARGETS`, `SWEEP_NOMINAL_BARE_PROMPT`, `SWEEP_FILLER_LINES`,
`ASSERT_VALUE_IN_PROMPT_CAVEAT`, `ADVERSARIAL_OVERWRITE_NOTE`, `OVERWRITE_PRESSURE_LABEL`,
`sweep_cells`, `build_diluted_persona`, `assert_filler_carries_no_value`, `overwrite_competitor`,
`build_overwrite_statement`, `sweep_applicability`, `monotone_claim_allowed`, `run_sweep`,
`PERSISTENCE_REPORT_PATH`, `arm_d_qualifier`, `MONOTONE_CLAIM_LICENSED`, `MONOTONE_CLAIM_REFUSED`,
`LADDER_PROXY_DEGENERATE_CAVEAT`, `assert_persistence_report_not_clobbered`,
`committed_ladder_rungs`, `ladder_report_commit`, `core_fact_ids`, `per_fact_by_arm`,
`write_persistence_report`, `build_parser`, `arm_record_path`, `serializable_config`,
`assert_recorded_config_matches_the_shared_object`, `assert_arms_are_pairable`,
`run_one_condition`, `run_report_mode`, `main`) and `tests/test_phase16_driver.py` (69 test
functions collected, all exercised by the file run). All three task commits resolve in `git log`:
`68340d8`, `daac1f1`, `fd6417f`. `git status --short` is empty and
`git diff --stat results/ pyproject.toml tests/test_phase14_scoring.py` is empty.

---
*Phase: 16-weight-vs-prompt-persistence-control*
*Completed: 2026-08-13*
