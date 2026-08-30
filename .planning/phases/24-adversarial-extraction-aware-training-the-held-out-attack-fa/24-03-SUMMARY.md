---
phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
plan: 03
subsystem: testing
tags: [advt-02, leave-one-family-out, disjointness, retract-in-place, dated-continuation, ast-guard, sentinel-pair]

# Dependency graph
requires:
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "`results/phase18_corpus.json` (864 rows) and `phase18_extraction.CORPUS_PATH` / `RESERVED_SOURCE_FAMILY` — the committed artifact every claim here is read from, imported read-only"
  - phase: 20-mitigation-gate
    provides: "`tests/test_phase20_correction.py`'s register — an AST/`_prose.normalized` audit discipline, never `grep -c` and never `X in source`"
  - phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
    provides: "`tests/test_phase23_cost.py:783-817` + `.planning/ROADMAP.md:51-71` — the live 23-12 retract-in-place precedent: `_CLAIM_TEXT`, sentinel pair, `_MARKER`, and its three mechanics (normalize, search from the claim index, `str.count`)"
provides:
  - "`tests/test_phase24_split.py` — ADVT-02's split as TWO separately-named assertions on `family` and on `source_family`, plus the superseded key's unsatisfiability as a running measurement"
  - "`.planning/ROADMAP.md` 24-03-CONTINUATION-BEGIN/END — the dated additive supersession of SC2's `(fact_id, seed_index)` key, 48 insertions / 0 deletions"
  - "`tests/test_phase24_correction.py` — 4 guards keeping the original SC2 clause standing, unique, dated and pointing at node ids that resolve by AST"
  - "The pre-registered held-out family: A2, fixed in wave 1 before any Phase 24 training run exists"
affects: [24-05 corpus-to-episode builder, 24-06 adversarial_ratio seam, 24-07 D-05 four-corner band check, Phase 25 frontier, Phase 28 reporting]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two properties, two functions, zero shared assertions: `family` and `source_family` share only a reader, so neither can be read as the other"
    - "Node-id resolution by `ast.parse` of the target module — the roadmap's citations must name functions that exist, and a rename goes red on the commit that renames"
    - "Node ids COLLECTED from the corrected prose by regex, not only compared against a declared pair, so an invented or stale citation is red too"
    - "Both readings of a superseded key measured, not just the one the correction quotes"

key-files:
  created:
    - tests/test_phase24_split.py
    - tests/test_phase24_correction.py
  modified:
    - .planning/ROADMAP.md

key-decisions:
  - "SC2's key was measured unsatisfiable on BOTH readings, not just the phase context's three-field one: the two-field `(fact_id, seed_index)` key SC2 literally names gives 140 distinct pairs per family with 140/140 pairwise overlap, and the three-field triple gives 216 with 216/216. The correction publishes both, because a supersession that measures a near-neighbour of the superseded key is not a measurement of it"
  - "`_CLAIM_TEXT` is the LONG form (the phrase ending in `results/phase18_corpus.json`), not the short phrase the continuation quotes back. The short phrase now occurs twice by design (original + quotation), so `flat.count(claim) == 1` would have been unsatisfiable on it"
  - "The continuation names three node ids but only two are declared constants. The third — the unsatisfiability evidence test — is collected by regex and resolved with the rest, so the register grows by editing the roadmap alone"
  - "PITFALLS §P18-1 is cited with a RESOLVING path (`.planning/milestones/v3.0-research/PITFALLS.md:357`) alongside `scripts/phase18_extraction.py:683-688`. The bare `PITFALLS P18-1` the plan and 24-CONTEXT use does not resolve — `.planning/research/PITFALLS.md` has no P18-1 section"
  - "No `gsd-sdk` mutation handler was called. ROADMAP.md and STATE.md were hand-edited, as in 24-01 and 24-02"

patterns-established:
  - "Watched-RED with a line-anchored probe: every probe prints the line number and the post-edit line text before the run, because a `str.replace(old, new, 1)` that lands on occurrence 1 of 4 produced a meaningless green in 24-02"
  - "Probe restore by whole-file inverse write, never `git checkout --`, with `git diff --numstat` re-checked to `48 0` after each restore"
  - "A `grep -c` hazard recorded in a docstring is MEASURED before it is written down: two same-line sentinels give `grep -c` = 1 (a `== 1` check passes) and `str.count` = 2 (the guard refuses)"

requirements-completed: []

# Metrics
duration: 34min
completed: 2026-08-30
---

# Phase 24 Plan 03: ADVT-02's Split on the Keys That Are Actually Disjoint — Summary

**SC2's `(fact_id, seed_index)`-overlap check is measured UNSATISFIABLE — 140/140 and 216/216 pairwise overlap, complete under both readings — and is superseded by a dated additive ROADMAP continuation (48 insertions, 0 deletions) that leaves the original sentence byte-identical, while ADVT-02's actual property ships as two separately-named disjointness assertions on `family` and `source_family`.**

## Performance

- **Duration:** 34 min
- **Started:** 2026-08-30T16:35:00Z
- **Completed:** 2026-08-30T17:09:00Z
- **Tasks:** 2
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments

- **The load-bearing measurement, re-derived from the committed corpus, not copied from the plan.** `results/phase18_corpus.json` holds **864 rows = 4 x 216**. Per-family raw counts: `A1-mild` 216, `A1-aggressive` 216, `A2` 216, `A3` 216 — the denominator for every overlap figure below.
  - **Three-field key `(fact_id, seed_index, tier)`:** **216** distinct triples per family, all four sets **EQUAL**. Every pairwise overlap measured individually: `A1-aggressive & A1-mild` 216/216, `A1-aggressive & A2` 216/216, `A1-aggressive & A3` 216/216, `A1-mild & A2` 216/216, `A1-mild & A3` 216/216, `A2 & A3` 216/216. Trained-union ∩ held-out-union = **216 of 216**.
  - **Two-field key `(fact_id, seed_index)` — the key SC2 LITERALLY NAMES:** **140** distinct pairs per family, trained ∩ held-out = **140 of 140**. (216 triples collapse to 140 pairs because 76 questions are asked in both tiers; `tier` is the only field separating them.)
  - Both readings are therefore complete overlaps, and a zero-overlap check on either can only ever be RED.
- **ADVT-02 verified directly** by `test_trained_and_held_out_attack_families_are_disjoint_on_family`: trained `{A1-mild, A1-aggressive, A3}` ∩ held-out `{A2}` = ∅, with the union asserted to **partition** the families actually present (a fifth family landing unassigned is red, not silently ignored).
- **The D-03 corollary shipped as a DISTINCT property** by `test_taught_and_held_out_source_families_are_disjoint_on_source_family`: taught `{F1, F2, F6}` (160/160/128) vs held-out `{F3, F7, F8, reserved}` (96/96/96/128), sets derived from the corpus *and* checked against a hard equality, with `reserved` resolved from `p18.RESERVED_SOURCE_FAMILY`.
- **The supersession rests on a running test, not on prose:** `test_the_superseded_fact_id_seed_index_key_is_unsatisfiable` re-measures both keys on every suite run and states its own inverse condition — if it ever goes green the corpus stopped being a full cross product.
- **The correction is additive and watched.** `git diff --numstat .planning/ROADMAP.md` = **48 insertions, 0 deletions**. All four guards in `tests/test_phase24_correction.py` were watched RED and restored by inverse edit.

## Task Commits

1. **Task 1: the two D-13 assertions + the unsatisfiability measurement** — `fd6ba46` (test)
2. **Task 2: the dated ROADMAP continuation + its guard** — `217c531` (docs)

**Plan metadata:** see the final `docs(24-03)` commit.

## Files Created/Modified

- `tests/test_phase24_split.py` (created, 210 lines) — 3 tests. Corpus loaded once via `phase18_extraction.CORPUS_PATH`; no path literal, no `build_corpus` rebuild, no membership relations.
- `tests/test_phase24_correction.py` (created, 213 lines) — 4 tests. `_CLAIM_TEXT` / `_BEGIN_SENTINEL` / `_END_SENTINEL` / `_MARKER` / `_CORRECTED_FILES`, matched through `scripts/_prose.normalized`.
- `.planning/ROADMAP.md` (modified, +48/-0) — the `24-03-CONTINUATION-BEGIN/END` block, plus the 24-03 tick and the 2/7 → 3/7 progress row in the metadata commit.

### Real ROADMAP.md anchors (re-located by content, as required — the plan's line numbers happened to still hold at execution start)

| Anchor | Line at execution start | Line after the continuation landed |
|---|---|---|
| `### Phase 24:` heading | 712 | 712 |
| SC2 bullet | 725-728 | 725-728 (byte-identical) |
| The superseded clause itself | 726-727 | 726-727 (byte-identical) |
| SC3 bullet | 730 | 777 |
| 23-12 continuation pair | 51 / 71 | 51 / 71 (undisturbed) |
| 24-03 continuation pair | — | 729 / 775 |
| Phase 24 progress row | 897 | 944 |

Note: the plan's `<context>` cited the 23-12 precedent at `:44-75`; the sentinels are actually at **51 and 71**. Everything was re-located by sentinel text and by the SC2 phrase, never by the cited number.

## Decisions Made

- **Both readings of the superseded key are measured and published.** The plan and 24-CONTEXT quote the three-field `(fact_id, seed_index, tier)` figure (216/216); SC2's sentence names the two-field key. Measuring only the triple would supersede a near-neighbour of the claim rather than the claim. Both are asserted in the test and both are written into the continuation.
- **`_CLAIM_TEXT` is the long form.** The continuation quotes the short phrase `zero-\`(fact_id, seed_index)\`-overlap structural check` back at the reader (the plan's instruction), which makes that phrase occur **twice**. The needle therefore had to include the `read from \`results/phase18_corpus.json\`` tail to keep `flat.count(claim) == 1` satisfiable. Verified: full claim count **1**, short phrase count **2**.
- **Node ids are collected, not only declared.** Test 4 asserts the two declared replacements are present, then regex-collects *every* `tests/*.py::test_*` id in the block and AST-resolves each. The third node id (the evidence test) is covered without a second constant, and a rename is red on the renaming commit.
- **`PITFALLS §P18-1` is cited with a path that resolves.** `.planning/research/PITFALLS.md` has no `P18-1`; the section lives at `.planning/milestones/v3.0-research/PITFALLS.md:357` and `scripts/phase18_extraction.py:683-688` already cites it. Both are written into the continuation so the citation is checkable.
- **Zero `gsd-sdk` mutation handlers.** ROADMAP.md and STATE.md hand-edited, matching 24-01 and 24-02.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] The two-field key SC2 actually names was measured alongside the three-field triple**
- **Found during:** Task 1
- **Issue:** The plan specified asserting 216 distinct `(fact_id, seed_index, tier)` triples. SC2's sentence names `(fact_id, seed_index)` — two fields. Asserting only the triple would have left the literal claim unmeasured, and the continuation would have published a figure about a different key from the one it supersedes.
- **Fix:** `test_the_superseded_fact_id_seed_index_key_is_unsatisfiable` loops over both key shapes; the continuation publishes both figures (216/216 and 140/140).
- **Files modified:** `tests/test_phase24_split.py`, `.planning/ROADMAP.md`
- **Verification:** 140 and 216 both counted from the artifact; a nudge of 140 → 141 was watched RED at line 208.
- **Committed in:** `fd6ba46`, `217c531`

**2. [Rule 1 - Bug] The plan's `PITFALLS P18-1` citation does not resolve**
- **Found during:** Task 2
- **Issue:** The plan (and 24-CONTEXT:324) cite "PITFALLS P18-1". `.planning/research/PITFALLS.md` contains no `P18-1`. Writing a dead citation into a permanent ROADMAP correction would have been unverifiable prose in exactly the artifact this plan exists to make checkable.
- **Fix:** The continuation cites `scripts/phase18_extraction.py:683-688` (which carries the "one prompt object dispatched twice" reasoning in live code) and `.planning/milestones/v3.0-research/PITFALLS.md:357` (the archived section).
- **Files modified:** `.planning/ROADMAP.md`
- **Verification:** Both paths and line numbers read at HEAD before writing.
- **Committed in:** `217c531`

**3. [Rule 3 - Blocking] Substituted a `str.count` acceptance check for the plan's `grep -c` sentinel criteria**
- **Found during:** Task 2
- **Issue:** The plan's acceptance criteria use `grep -c "24-03-CONTINUATION-BEGIN"`. `grep -c` counts **LINES**, so two sentinels on one line satisfy a `== 1` check. This is not hypothetical here — the guard's own mechanic 3 claims it.
- **Fix:** The `grep -c` criteria were run *and* pass (all four counts correct, `23-12` still 1). In addition the guard uses `str.count`, and the hazard was **measured**: with two BEGIN sentinels planted on one line, `grep -c` returned **1** while `str.count` returned **2** and the guard went RED.
- **Files modified:** none (verification method only)
- **Verification:** See "Watched-RED evidence" below, row G.
- **Committed in:** `217c531`

---

**Total deviations:** 3 auto-fixed (1 missing-critical measurement, 1 dead citation, 1 blocking verification-method substitution)
**Impact on plan:** All three strengthen the artifact the plan asked for. No scope creep — no new files beyond the plan's two, no edits to `.planning/REQUIREMENTS.md`, no `scripts/` changes.

## Watched-RED evidence

Every probe was line-anchored and printed its post-edit line before the run (24-02's false green came from a `replace(..., 1)` landing on occurrence 1 of 4). Every restore was a targeted inverse write; `git checkout --` was never used.

| # | Probe | Line | Result |
|---|---|---|---|
| A | `A2` planted into `TRAINED_FAMILIES` | split:63 | 1 failed |
| B | `A3` dropped — split stops partitioning | split:63 | 1 failed |
| C | `F6` dropped from the taught hard equality | split:148 | 1 failed |
| D | two-field census nudged 140 → 141 | split:208 | 1 failed |
| E | SC2's clause DELETED (`numstat` went to `49 2`) | ROADMAP:726 | 1 failed |
| F | marker's plan id broken to `(plan 24-3)` | ROADMAP:731 | 1 failed |
| G | second BEGIN sentinel planted on the SAME line — `grep -c` = **1**, `str.count` = **2** | ROADMAP:729 | 1 failed |
| H | a replacement node id renamed to a function that does not exist | ROADMAP:754 | 1 failed |

After every restore: `git diff --numstat .planning/ROADMAP.md` back to `48 0`; both test files green.

## Acceptance criteria, as run

**Task 1**
- `pytest -q tests/test_phase24_split.py` → **3 passed**
- `grep -n "results/phase18_corpus.json" tests/test_phase24_split.py` → **nothing** (exit 1)
- `grep -c "issubset\|assert .* in corpus\|approx" tests/test_phase24_split.py` → **0**
- `grep -c "^def test_" tests/test_phase24_split.py` → **3**; the two D-13 names are distinct and neither can be read as the other
- `git diff scripts/phase18_extraction.py` → **empty**
- `pytest -q tests/test_phase24_split.py tests/test_phase18_corpus.py tests/test_phase16_prereg.py` → **27 passed**

**Task 2**
- `pytest -q tests/test_phase24_correction.py` → **4 passed**
- `git diff --numstat .planning/ROADMAP.md` → **48 insertions, 0 deletions**
- `grep -c 24-03-CONTINUATION-BEGIN` = **1**, `-END` = **1**, `23-12-CONTINUATION-BEGIN` = **1**, `-END` = **1**
- `_prose.normalized` sweep for `overlap structural check read from` → **1**
- SC2 clause deletion watched RED, restored by inverse edit, `numstat` back to `48 0`
- `pytest -q tests/test_phase24_correction.py tests/test_phase23_cost.py` → **65 passed**

**Plan verification**
- `pytest -q` (full suite) → **1608 passed, 1 skipped, 0 failed** in 370.53 s. Baseline carried in was **1601 passed / 1 skipped**; this plan adds exactly **7** tests (3 + 4). 1601 + 7 = 1608, exact.
- `ruff check . && ruff format --check .` → clean, 224 files formatted
- `git diff scripts/phase18_extraction.py scripts/mitigation_gate.py` → **empty**

## Issues Encountered

- **The plan's line citations for the 23-12 precedent were off** (`:44-75` vs the real `51/71`), the hazard the prompt warned about. Everything was re-located by sentinel text and by the SC2 phrase; the real anchors are tabled above. The Phase 24 anchors (`712`, `725-728`, `730`) happened to still hold exactly.
- **First `grep -c` blind-spot demonstration was itself a false measurement.** Planting the duplicate BEGIN sentinel on a *different* line gave `grep -c` = 2, which demonstrates nothing. Re-run with both sentinels on the *same* line: `grep -c` = 1, `str.count` = 2. The docstring's claim is now a measurement rather than a repeated belief.
- **Three ruff E501s** on the first write of `tests/test_phase24_split.py` (101 > 100), fixed by re-wrapping prose only.

## Known Stubs

None. Both test modules assert against the committed artifact at HEAD; nothing is deferred to a later plan.

## Threat Flags

None. No new network endpoint, auth path, file-write path or schema was introduced — this plan adds two read-only test modules and appends prose to a planning file. `scripts/phase18_extraction.py` is imported and provably unmodified (`git diff` empty), which is T-24-13's mitigation.

## Requirements

**ADVT-02 remains UNTICKED, deliberately.** This plan ships the structural half — the split is committed, the held-out family is named before training, and the disjointness is a running measurement. ADVT-02's full text also depends on the mixture actually training against that split, which is 24-05 (the episode builder) and 24-06 (the `adversarial_ratio` seam). Ticking it now would claim a property no code yet exercises.

## Next Phase Readiness

- **24-04** (the remaining wave-1 plan) is unblocked and independent: `contains_refusal` beside `contains_value`, plus D-11's clean-frame probe populations.
- **24-05** inherits `TRAINED_FAMILIES` / `HELD_OUT_FAMILIES` as importable module constants in `tests/test_phase24_split.py`, and the measured `core_taught` source-family census (F1 160, F2 160, F6 128 = 448) it must render from.
- **A live tripwire now exists on `.planning/ROADMAP.md`.** Any later plan that rewraps, reflows or reformats SC2's bullet, renames a `test_phase24_split.py` test, or touches the 24-03 sentinel pair will turn `tests/test_phase24_correction.py` RED. That is the intent; correct it the same way this plan did — additively.

## Self-Check: PASSED

Files claimed, verified on disk: `tests/test_phase24_split.py` FOUND, `tests/test_phase24_correction.py` FOUND, `.planning/ROADMAP.md` FOUND, `24-03-SUMMARY.md` FOUND.
Commits claimed, verified in `git log --all`: `fd6ba46` FOUND, `217c531` FOUND.
`.planning/REQUIREMENTS.md` byte-unchanged (`git status --short` empty for it), as claimed.

---
*Phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa*
*Completed: 2026-08-30*
