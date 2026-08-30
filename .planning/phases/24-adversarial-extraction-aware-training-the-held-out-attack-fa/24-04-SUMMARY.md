---
phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
plan: 04
subsystem: testing
tags: [advt-01, d-04, d-07, d-11, refusal-rate, clean-frame-probe, lazy-import-boundary, normalizer-reuse, wall-census]

# Dependency graph
requires:
  - phase: 14-persona-fact-set-and-scored-recall
    provides: "`scripts/phase14_recall.py` — `normalize` (the scoring normalizer that duplicates `phase14_factset.normalize_for_match` exactly ONCE), `contains_value`, `score_question`, `_prove`, and the module's LAZY-IMPORT RULE"
  - phase: 14-persona-fact-set-and-scored-recall
    provides: "`scripts/phase14_factset.py` — `render_family`'s D-16 additive `forms=` override, `LOCKED_FACTS`, `LOCKED_VALUES`, `SOFT_TIER_FACTS`, and `_render_family:694-695`'s statement that F4/F5 name the value in the question"
  - phase: 21-capacity-arm-n-64
    provides: "`scripts/phase21_filler.py` — 56 unscored `FILLER_FACTS` over 8 `FILLER_SLOT_FORMS` slots disjoint from the 11 published ones, and `tests/test_phase21_sc5.py`'s `== 10` wall census"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "`results/phase18_corpus.json` — the 864-row corpus whose `core_taught` tier measures {F1 160, F2 160, F6 128}, the independent confirmation of the pinned family set"
provides:
  - "`phase14_recall.contains_refusal` / `score_refusal` — D-04's refusal column, `contains_value`/`score_question`'s exact mirror over a caller-supplied template vocabulary"
  - "`phase14_recall.CLEAN_FRAME_PROBE_FAMILY_IDS = ('F1','F2','F6')` — the taught set minus the two value-naming frames, one tuple building BOTH D-11 populations"
  - "`phase14_recall.clean_frame_probe_populations()` — the two pinned clean-frame probe populations with `family_ids`, `scored` and the D-11 `reading_rule` returned as DATA, plus two runtime `_prove` refusals"
  - "`tests/test_phase24_refusal_rate.py` — 5 tests: pointwise mirror equivalence, disjunction, the counts shape, the pinned populations, and the reading rule proved to survive `__doc__` stripping"
affects: [24-05 corpus-joined episode builder, 24-06 adversarial_ratio seam, 24-07 D-05 four-corner band check, Phase 25 frontier, Phase 28 reporting]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "An instrument lives where its normalizer lives, not beside the table it scores: `contains_refusal` takes templates as an argument so instrument and table stay separately owned"
    - "A probe population is pinned as returned DATA (family set + reading rule + scored flag) in the wave BEFORE any sweep point exists"
    - "A runtime `_prove` containment refusal as the companion to the module-level D-02 scan, which structurally cannot see strings that exist only in a function's return"
    - "One parameterised renderer over `forms=` builds both populations, so 'the two differ only in facts and grammar' is structural rather than asserted"

key-files:
  created:
    - tests/test_phase24_refusal_rate.py
  modified:
    - scripts/phase14_recall.py
    - tests/test_phase21_sc5.py

key-decisions:
  - "`CLEAN_FRAME_PROBE_FAMILY_IDS` is pinned to ('F1','F2','F6') rather than passing `fs.TAUGHT_FAMILY_IDS`. The taught set contains F4 and F5, which `_render_family:694-695` says name the value inside the question — a taught-set population would RETURN published values, and the D-02 scan is module-level so nothing in the repo would catch it. Watched RED: adding F5 back fires the containment refusal naming three real values"
  - "`questions` is DEDUPLICATED and the collapse is disclosed rather than hidden. A clean-frame question is slot-determined (that IS the F1/F2/F6 property), so the filler population's 784 (fact, question) rows collapse 7:1 onto 112 distinct questions. `fact_ids` still covers all 56; `questions` is the prompt population, and the two sides come out budget-matched at 112 vs 112"
  - "The widened `{**published, **filler}` slot merge (`teach_persona._slot_forms_for`) is NOT used and NOT retyped. Each population is rendered separately, so `forms=phase21_filler.FILLER_SLOT_FORMS` alone suffices — exactly what `phase21_filler.render_filler_episodes` already passes. No third dict-splat site exists"
  - "The new `assert len(forbidden) == 10` was added to `tests/test_phase21_sc5.py`'s `_EXPECTED_WALL` and `SC5_GUARD_SET` as a TWELFTH wall member, not excluded via `_NOT_WALL_SITES`. The census was right: the assertion genuinely guards a scan over LOCKED+SOFT"

patterns-established:
  - "Mirror-by-test: `contains_refusal(c, [n]) == contains_value(c, n)` pointwise across every normalizer behaviour, so a reimplemented predicate cannot diverge silently"
  - "A reading rule returned as data survives `python -OO`; the test proves it by stripping `__doc__` and re-calling"
  - "Every RED probe is line-anchored, prints its line number and post-edit text, and is restored byte-for-byte with a sha256 comparison — never `git checkout --`"

requirements-completed: [ADVT-01]

# Metrics
duration: 42min
completed: 2026-08-30
---

# Phase 24 Plan 04: D-04's Refusal Instrument and D-11's Pinned Clean-Frame Populations Summary

**`contains_refusal`/`score_refusal` ship as `contains_value`/`score_question`'s pointwise mirror in the module that owns the scoring normalizer, and D-11's two clean-frame probe populations — 8 locked facts and 56 filler facts, both rendered over the single pinned family set `("F1","F2","F6")`, both landing on 112 distinct questions — are pinned as returned data with two runtime refusals, before any sweep point exists.**

## Performance

- **Duration:** ~42 min
- **Tasks:** 2 of 2
- **Files modified:** 3 (1 created, 2 modified)
- **Commits:** 2 task commits + 1 docs commit

## Accomplishments

### Task 1 — `contains_refusal`, `score_refusal`, and the D-11 selector (`d121cf7`)

`scripts/phase14_recall.py` gained 174 insertions / 0 deletions, all additive, immediately after
`score_question` so the mirror is visible at the point of definition. `normalize`, `contains_value`
and `score_question` are byte-unchanged.

- `contains_refusal(completion, templates)` = `any(normalize(t) in normalize(completion) for t in
  templates)`. Same module, the **same** `normalize` object, same substring direction. `templates`
  is a caller argument, so the module still imports no template table at any level.
- `score_refusal(completions, templates)` returns `(k, n)` — `score_question`'s exact shape.
- `CLEAN_FRAME_PROBE_FAMILY_IDS = ("F1", "F2", "F6")` with both reasons written into the constant's
  comment.
- `clean_frame_probe_populations()` returns `locked` / `filler` / `reading_rule`, with `questions`,
  `fact_ids`, `family_ids` and `scored` per population.

### Task 2 — 5 tests + one deliberate census extension (`2ba4292`)

`tests/test_phase24_refusal_rate.py` (189 lines, 5 tests) plus 10 lines in
`tests/test_phase21_sc5.py`. Committed together so no commit in history leaves the census red.

## Measured Results

### The two D-11 populations, measured at HEAD

| Population | Facts | Slots | (fact, question) rows | Distinct questions | `scored` |
| ---------- | ----- | ----- | --------------------- | ------------------ | -------- |
| `locked`   | 8 (`len(fs.LOCKED_FACTS)`) | 8 published | 112 | **112** | `True` |
| `filler`   | 56 (`len(pf.FILLER_FACTS)`) | 8 filler | 784 | **112** | `False` |

Both are 8 slots x 14 clean-frame questions. The filler side's 784 rows collapse 7:1 because a
clean-frame question is **slot-determined** — F1/F2/F6 never name the value, which is exactly why
they are the clean frames — and filler sits 7 facts per slot (measured: every slot has 7, and the
distinct question-tuple count per filler slot is 1). Disclosed rather than tidied away:
`fact_ids` still covers all 56, `questions` is the prompt population a probe would run, and the
two sides come out **budget-matched at 112 vs 112**, so D-11 compares rates and not sample sizes.

- Question sets **disjoint**: `set(locked) & set(filler) == set()`.
- Published-value containment over all **224** returned questions x the **10**-value leak
  vocabulary (`LOCKED_VALUES` + `SOFT_TIER_FACTS`, resolved at runtime, never typed): **0 hits**.
- Filler slots vs published slots: **disjoint** (`set(fs.SLOT_FORMS) & set(pf.FILLER_SLOT_FORMS)`
  is empty), so the two populations really are drawn from different grammars.

### The family set, confirmed independently

`{F1, F2, F6}` is exactly the `source_family` set the Phase-18 corpus's `core_taught` tier already
carries. Counted from `results/phase18_corpus.json` (path resolved from
`phase18_extraction.CORPUS_PATH`, never a literal), 864 prompts:

| tier | source_family | rows |
| ---- | ------------- | ---- |
| `core_taught` | F1 | 160 |
| `core_taught` | F2 | 160 |
| `core_taught` | F6 | 128 |
| `core_held_out` | F3 / F7 / F8 / `reserved` | 96 / 96 / 96 / 128 |

F4 and F5 are absent from the corpus entirely. The agreement is by measurement, not by assumption.

### Clean-room invariants (the criteria that matter most)

- `phase14_recall.py` module-level imports, **checked by AST** (`ast.parse` over `tree.body`,
  never grep): `phase24_adversarial` **False**, `phase14_factset` **False**, `teach_persona`
  **False**. Both new lazy imports live inside `clean_frame_probe_populations`'s body.
- `src.count("def normalize")` in `scripts/phase14_recall.py` = **1**. No third copy of the
  normalizer.
- `scripts/mitigation_gate.py` **byte-unchanged**: sha256
  `86db479876ebeb2ba5b23c3b95da0ab20f13a3fbccf655b697280421b1997e14` at HEAD and at HEAD~2 —
  identical. `scripts/phase18_extraction.py` and `.planning/REQUIREMENTS.md` likewise untouched
  (`REQUIREMENTS.md`'s last commit is still `7296b31`, from Phase 23; ADVT-01/02/03 remain
  deliberately unticked).

### Full suite

`.venv/bin/python -m pytest -q` -> **1613 passed, 1 skipped, 0 failed** in 369.69 s.
Baseline carried in was **1608 passed, 1 skipped**. Delta **+5**, exactly the 5 tests this plan
adds — no test moved, none was lost.

## Watched-RED Probes

Seven probes. Every one is **line-anchored** (matched on exact line text, asserted unique), prints
its line number and the post-edit line before running, and is restored by writing the saved
original text back with a **sha256 equality check**. No `git checkout --`, no blanket restore.

| # | Probe | Line | Result |
| - | ----- | ---- | ------ |
| P1 | `F5` appended to `CLEAN_FRAME_PROBE_FAMILY_IDS` | 388 | **RED** — `PROOF FAILED: ... name published values ... [('locked','F5','1987'), ('locked','F5','7412'), ('locked','F5','brindlemoor')]` |
| P2 | filler population rebuilt from `fs.LOCKED_FACTS, None` | 439 | **RED** — collision refusal, naming 3 shared questions |
| P3 | `normalize` dropped from `contains_refusal` | 358 | **RED** — mirror test |
| P4 | `score_refusal` returns a rate | 367 | **RED** — counts test |
| P5 | `family_ids` widened back to `("F1","F2","F4","F5","F6")` | 494 | **RED** — populations test |
| P6 | `fact-keyed` removed from **one** line of the reading rule | 480 | **GREEN — false green, see below** |
| P6b | `fact-keyed` removed from **both** lines | 480, 483 | **RED** — reading-rule test |

**P6 was a false green, and it is recorded rather than quietly re-run.** `fact-keyed` occurs
**twice** in the reading rule (measured: `rule.lower().count("fact-keyed") == 2`, source occurrences
at `:480` and `:483`). Removing occurrence 1 left the second sentence still stating the fact-keyed
reading, so the test passed **correctly** — the probe was under-powered, not the test. This is the
same class of trap as 24-02's `source.replace(old, new, 1)`, arriving this time in a probe of my
own writing; the fix was to measure the occurrence count first and edit all of them.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `tests/test_phase21_sc5.py::test_wall_census_is_the_measured_set` went RED**

- **Found during:** Task 2, on the first run of the plan's own `<verify>` command.
- **Issue:** The new test file's `assert len(forbidden) == 10` is a `== 10` leak-vocabulary
  assertion, and `tests/test_phase21_sc5.py` runs a mechanical census over every such site under
  `tests/`. A new site is a **finding** by that test's own design.
- **Resolution:** Read the site, confirmed it genuinely asserts on `LOCKED_VALUES +
  SOFT_TIER_FACTS` before scanning, and registered it as a **twelfth wall member** in
  `_EXPECTED_WALL` — not as a `_NOT_WALL_SITES` exclusion, which would have been a quieter version
  of the hole. `SC5_GUARD_SET` gained the filename too, because the census asserts
  `set(files) <= set(SC5_GUARD_SET)` and this plan's `<verification>` block does run the file.
  Both entries carry a dated reason inline.
- **Files modified:** `tests/test_phase21_sc5.py` (+10 lines, 0 deletions)
- **Commit:** `2ba4292`

**2. [Rule 2 - Missing disclosure] `questions` deduplicated and the 7:1 collapse disclosed**

- **Found during:** Task 1, first smoke run: filler returned 784 questions of which only 112 were
  distinct.
- **Issue:** The plan says "return counts and question strings per population" and did not
  anticipate that a clean-frame question is slot-determined. Returning 784 near-duplicate strings
  would have made the filler side look 7x larger than the locked side while running the same 112
  prompts — the D-11 comparison would then have been unbalanced for a reason invisible in the data.
- **Resolution:** `questions` is insertion-ordered **distinct** strings; `fact_ids` still covers
  every fact; the collapse, its cause, and the resulting 112-vs-112 budget match are written into
  the function's docstring as measured figures.
- **Files modified:** `scripts/phase14_recall.py`
- **Commit:** `d121cf7`

### Plan Guidance Deliberately Not Followed (stated, as the plan invites)

**The widened slot merge is not used and not retyped.** The plan's `<interfaces>` block points at
`scripts/teach_persona.py:412-451` (`_slot_forms_for`) and asks to "import the merge behaviour, do
not retype the dict-splat at a third site unless a lazy local merge is genuinely simpler (state
which you did and why)". **Neither was needed.** `_slot_forms_for` exists because the corpus
builder renders a **mixed** fact set (8 locked + 56 filler) in one call and therefore needs the
union. This selector renders each population **separately**, so `forms=None` covers locked (the
byte-identical default path) and `forms=phase21_filler.FILLER_SLOT_FORMS` covers filler — exactly
what `phase21_filler.render_filler_episodes` already passes today. There is **no third
`{**published, **filler}` site**, and no `_slot_forms_for` import.

**Line numbers re-located by content, never by the plan's citation.** All anchors were found by
matching source text. `_render_family`'s docstring statement about F4/F5 is at
`scripts/phase14_factset.py:694-695`, reached from `render_family:833` — both verified at HEAD, and
both as the plan cited them. `scripts/phase21_filler.py:8` and `:395` both resolve to the
"8 scored + 56 unscored" / "never scored and never enters the 10-value leak vocabulary" sentences,
as cited. The insertion point moved: `score_question` ends at `:322` and `find_contradictions`
began at `:325` before the edit.

**`make test` does not work from this shell, and that is an environment fact, not a regression.**
The bare `pytest` in the Makefile resolves to the pyenv **3.12** interpreter, which has no `torch`,
producing 97 collection `ModuleNotFoundError`s in 1.81 s. Re-run as
`.venv/bin/python -m pytest -q` it is fully green. Recorded because the plan's acceptance criteria
name `make test`, and its failure here means nothing about this code.

### Grep-criterion substitutions (hazard: prose false-RED/false-GREEN)

- `grep -n "phase24_adversarial" scripts/phase14_recall.py` returns nothing, but the criterion is
  reported against an **AST** walk of `tree.body` instead, because a grep would also have matched a
  mention in a docstring or a comment. AST result: not a module-level import.
- `grep -c "def normalize"` = 1 was cross-checked with `src.count("def normalize")` = 1.
- `grep -c "approx" tests/test_phase24_refusal_rate.py` = 0; `grep -n "56\b|== 8\b"` matches
  nothing. Every population size is read as `len(fs.LOCKED_FACTS)` / `len(pf.FILLER_FACTS)`.

## Known Stubs

None. Nothing here is a placeholder: both functions are live, and the selector returns real
populations built from the committed fact sets. Nothing is *scored* — Phase 24 runs no training and
no generation, which is the plan's design and not an unfinished edge.

## Threat Flags

None. No new network endpoint, auth path, file access pattern, or schema change. The one new file
read is none — the selector reads only already-imported module constants.

## Self-Check: PASSED

- `scripts/phase14_recall.py` — FOUND (modified, +174/-0)
- `tests/test_phase24_refusal_rate.py` — FOUND (created, 189 lines)
- `tests/test_phase21_sc5.py` — FOUND (modified, +10/-0)
- commit `d121cf7` — FOUND
- commit `2ba4292` — FOUND
- `scripts/mitigation_gate.py` — byte-unchanged, sha256 verified against HEAD~2
