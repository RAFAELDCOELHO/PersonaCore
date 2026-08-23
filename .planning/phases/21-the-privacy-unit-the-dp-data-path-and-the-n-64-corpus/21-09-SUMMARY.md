---
phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
plan: 09
subsystem: dp-capacity-arms
tags: [unit-06, sc5, d-13, d-14, d-16, d-17, d-18, wave-5, t-21-04, t-21-08, t-21-39, t-21-40, t-21-41, t-21-42, t-21-43, t-21-55, t-21-56]
requires:
  - "21-07 — scripts/phase21_filler.py::FILLER_FACTS (56) and FILLER_SLOT_FORMS (8 disjoint slots)"
  - "21-08 — scripts/teach_persona.py::replay_window_budget(n_facts), the public replay volume both DP arms defer to"
  - "21-10 — a SCHEDULING edge only; serializes this plan's three working-tree canaries away from 21-10's full-suite + `git diff --exit-code` verification"
provides:
  - "scripts/teach_persona.py::ARMS gains 'dp_n8' and 'dp_n64'"
  - "scripts/teach_persona.py::arm_spec('dp_n8') -> (LOCKED_FACTS, False, 0.0)"
  - "scripts/teach_persona.py::arm_spec('dp_n64') -> (LOCKED_FACTS + FILLER_FACTS, False, 0.0)"
  - "scripts/teach_persona.py::_slot_forms_for(facts) — the widened slot grammar that makes n=64 BUILDABLE, not merely declarable"
  - "tests/test_phase21_sc5.py — the 4-direction leak scan, the mechanical `== 10` wall census, two sha256 pins, the exact locked/soft composition"
affects:
  - "21-11 — calls arm_spec('dp_n64') and build_bins under a tmpdir; without _slot_forms_for that call raises KeyError before writing a single row"
  - "GATE-10 — the n=8-vs-n=64 capacity comparison this plan makes CONSTRUCTIBLE and proves unconfounded"
tech-stack:
  added: []
  patterns:
    - "A capacity is REACHED end-to-end (render -> build_bins -> sanity_check) before it is called reachable; `arm_spec` returning the right tuple is a declaration, not a capability"
    - "A census pins a MEASURED multiset of (filename, expression) rather than a documented integer, with line numbers deliberately absent so a moved site is not a failure and a lost site is"
    - "An exclusion from a census carries its reason inline; an exclusion without one is indistinguishable from a site quietly dropped to hit a number"
    - "A `-k` selector named in a verification table is RUN before it is trusted — one that selects zero tests exits 0 and passes vacuously"
    - "A deliberate-RED is applied strictly AFTER the GREEN commit and restored by removing the exact bytes appended, verified against a sha256 recorded BEFORE the mutation"
    - "Two guard tiers are only 'two tiers' if the second can be OBSERVED with the first neutralised; otherwise the first masks the second and the claim is untested"
key-files:
  created:
    - "tests/test_phase21_sc5.py"
    - ".planning/phases/21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus/21-09-SUMMARY.md"
  modified:
    - "scripts/teach_persona.py"
decisions:
  - "The n=64 capacity needed a slot-grammar widening in teach_persona.py that the plan does not mention at all. arm_spec alone makes n=64 DECLARABLE but not BUILDABLE: render_episodes and sanity_check both die on KeyError: 'filler_boat_name'. _slot_forms_for(facts) returns None for every published-slot corpus — the identical code path, so golden_render_family_v2.json is untouched — and the widened union only when filler is present."
  - "Direction 3 was re-scoped because the plan's form is UNSATISFIABLE, not merely awkward. scripts/phase21_filler.py HOLDS all ten scored values by design (FORBIDDEN_SCORED_VALUES + PUBLISHED_POOL_VALUES); a module scan returns 22 hits and can never return []. Re-scoped to the property it is actually for: no filler value collides with a scored value under normalized containment BOTH directions (3a), and no scored value reaches the RENDERED filler episodes (3b)."
  - "The wall census pins 11 measured (filename, expression) pairs, not the plan's 8. A third grep pattern was required: the plan's two patterns miss `taught == 10`, `len(result[\"values\"]) == 10` and `len(fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS) == 10` — three real sites."
  - "test_phase21_multiplicity.py:298 `assert len(TEN_SCHEMA_KEYS) == 10` is EXCLUDED with a stated reason. It is plan 21-10's D-26 row-schema key count and appeared AFTER 21-07's census, which is the concrete demonstration that a census may inherit a method but never a number."
  - "calibration_items (the 4th render_family call site) is deliberately left raising on filler facts. It is unreachable from a DP arm — CAL_ARMS holds only the three calibration arms — and scoring filler is exactly what SC5 forbids, so a loud KeyError there is the correct behaviour, not a gap."
metrics:
  duration: "~50 min"
  tasks_completed: 3
  completed: 2026-08-23
---

# Phase 21 Plan 09: Both Capacities Reachable, No Instrument Disturbed Summary

`arm_spec('dp_n8')` and `arm_spec('dp_n64')` are both **built end-to-end** — 176 and 1,408 episodes
written through the real tokenizer and the real packer, not asserted constructible — and the only
two files this plan changed are the two it declared.

---

## THE CENTRAL FINDING: n=64 was NOT reachable, and the plan does not mention why

The prompt required both capacities be **actually reached**, not asserted reachable. That
requirement found the defect immediately.

Task 1 as written produces this, on the first real build:

```
File "scripts/phase14_factset.py", line 699, in _render_family
    s = (SLOT_FORMS if forms is None else forms)[fact.slot]
KeyError: 'filler_boat_name'
```

`render_family`'s default grammar is `fs.SLOT_FORMS`, and the 56 filler facts sit in **8 slots
deliberately disjoint from the published 11** (D-13/D-16). So `arm_spec('dp_n64')` returns 64
facts and the *only* consumer of those facts refuses them. **A capacity whose sole consumer raises
is a declaration, not a capability.**

There are **two** such call sites on the DP build path, and the second is worse than the first
because it fires *after* the bins are on disk:

| # | site | when it fires |
|---|---|---|
| 1 | `render_episodes` → `fs.render_family(...)` | before a single row is rendered |
| 2 | `sanity_check` proof 5 → `fs.render_family(...)` | **after** `build_bins` has written both bins |

Fixed once, at the root, with `_slot_forms_for(facts)` in `scripts/teach_persona.py` — this plan's
own declared file. It returns `None` for every published-slot corpus, which per `render_family`'s
own docstring is *"the same code path"*, not merely an equal result; and the widened
`{**SLOT_FORMS, **FILLER_SLOT_FORMS}` union only when a filler fact is present.

**This matters beyond this plan.** `21-11-PLAN` task 2 says *"repeat rows 2 and 3 at n=64 via
`arm_spec('dp_n64')`"* and its `<files>` is `scripts/phase21_unit_record.py` only — it declares no
edit to `teach_persona.py`. Without this fix 21-11 dies on its first n=64 row.

## Both capacities, MEASURED end-to-end

`render_episodes` → `build_bins` → `sanity_check`, real frozen tokenizer, `seed_everything(1337)`,
written to a scratch dir so no `arm_outputs` path and no recorded evidence was touched:

| arm | facts | episodes | teaching tokens | windows @256 | replay in bin | `replay_window_budget` |
|---|---|---|---|---|---|---|
| `dp_n8` | 8 | 176 | **7,581** | 30 | 0 | 8,192 |
| `dp_n64` | 64 | **1,408** | 72,093 | 282 | 0 | 65,536 |

Both numbers close against independently-derived figures rather than being new claims:

- `dp_n8`'s **7,581** is exactly D-10's teaching-token total, the figure 21-10 recovered from a
  completely different route (per-fact flat packing) and whose window ceilings reproduce D-01's
  ragged `(4,4,4,4,4,5,4,4)`.
- `dp_n64`'s **1,408** episodes is exactly 21-07's measured `8 x 22 + 1,232` total taught rows.
- `dp_n8`'s **176** episodes is the episode count 21-08 held byte-identical across both arms of its
  side-channel differential.
- `sanity_check` passed all three proofs on both arms, including the token-level held-out
  guarantee over 130 held-out questions.

`replay_ratio = 0.0` on both, and it is load-bearing: under D-10 replay leaves the teaching bin and
arrives through `train()`'s seam at the public `replay_window_budget(n_facts)`, which is what makes
`grad_accum_steps = n_facts` literally true. `arm_outputs` gives the two arms disjoint `bin`, `mask`,
`csv`, `checkpoint` and `adapter` paths for free, and both are disjoint from `real`'s recorded bins.

## The load-bearing half: what was checked, and the BOUNDARY of the claim

"No published instrument disturbed" is only evidence if the instruments are enumerated. The
strongest form available is mechanical — **the complete set of files this plan changed**:

```
$ git diff --stat 4006ad8 HEAD
 scripts/teach_persona.py  | 104 ++++++++++++-
 tests/test_phase21_sc5.py | 366 ++++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 466 insertions(+), 4 deletions(-)

$ git diff --diff-filter=D --name-only 4006ad8 HEAD
(empty — zero deletions)
```

Exactly the two files `files_modified` declares. The 4 removed lines are the `ARMS` tuple reflow,
two `render_family` calls gaining `forms=`, and the `arm_spec` docstring expanding — no `-` line
touches the recorded `real` branch.

### Instruments checked, each against its committed digest

| Instrument | sha256 measured now | Provenance of the expected value |
|---|---|---|
| `scripts/phase18_extraction.py` | `d2b44806…503d96` | this plan's pin — VERIFIES |
| `results/phase16_recall_sample.json` | `407c4b93…307c55` | this plan's pin — VERIFIES |
| `scripts/mitigation_unit.py` | `45f37e15…000473` | 21-01's FROZEN pin, re-confirmed by 21-05/07/08/10 |
| `pyproject.toml` | `81d07d5d…112bdf` | `tests/test_package.py:11` STAT-04 — VERIFIES |
| `scripts/mitigation_gate.py` | `86db4798…97e14` | unchanged vs base (`git diff --exit-code` = 0) |
| `scripts/phase14_factset.py` | `35f0ad2e…86e62e` | recorded pre-mutation; equal post-restore |
| `scripts/phase21_filler.py` | `bec49415…f68d755` | equals 21-07's recorded value |
| `scripts/erasure_gate.py` | `a79d317a…3facde` | unchanged vs base |
| `scripts/phase19_erasure.py` | `c407246d…6b6303` | unchanged vs base |
| `tests/fixtures/golden_render_family_v2.json` | `300302e4…3ba88` | unchanged; its replay test is green |
| `tests/fixtures/golden_build_bins_v2.json` | `9724b061…f6b8eb` | unchanged; its replay test is green |

The two golden fixtures are the ones that could plausibly have moved, because `_slot_forms_for`
sits on `render_family`'s call path. Both replay green inside the full suite, which is the check
that matters — a digest on the fixture alone would only prove the *expected* side unchanged.

### What was NOT checked — stated so the reader sees the edge, not an implied "everything"

- **Direction 1 scans a FIXED ENUMERATION of six instrument sources, not a glob.** A new
  instrument file is outside the claim until it is added to `INSTRUMENT_SOURCES`. The glob-scanning
  guard is a different one, `tests/test_phase18_prereg.py:127-132`, over `scripts/phase18_*.py`.
- **No claim about `results/` artifacts other than `phase16_recall_sample.json`.** Others were shown
  unchanged vs base, not pinned by digest in a test.
- **No training run happened.** Both arms were built and sanity-checked; neither was trained, and
  no adapter, checkpoint or `results/phase21_*` artifact was produced. `git ls-files
  'results/phase21_*'` is **empty**, as 21-11's irrevocable `adds[-1]` ordering requires.
- **No claim that the n=64 bin is the one 21-11 should publish.** It was built to a scratch dir to
  prove reachability; 21-11 owns the recorded build.
- **`calibration_items` (the 4th `render_family` call site) still raises on filler.** Deliberate:
  it is unreachable from a DP arm (`CAL_ARMS` holds only the three calibration arms), and scoring
  filler is what SC5 forbids, so a loud refusal is correct.

## The `== 10` wall census — MEASURED 11 sites across 8 files

Censused mechanically, `__file__` excluded by a `path.name == pathlib.Path(__file__).name` guard in
the walk, **three** patterns, every exclusion carrying its reason. No documented number was used.

| # | Site | Expression |
|---|---|---|
| 1 | `tests/test_phase14_demo.py:394` | `assert len(values) == 10` |
| 2 | `tests/test_phase14_demo.py:568` | `assert len(result["values"]) == 10` |
| 3 | `tests/test_phase14_scoring.py:405` | `assert len(forbidden) == 10` |
| 4 | `tests/test_phase16_driver.py:313` | `assert len(forbidden) == 10` |
| 5 | `tests/test_phase16_ladder.py:443` | `assert len(forbidden) == 10` |
| 6 | `tests/test_phase16_ladder.py:711` | `assert len(forbidden) == 10` |
| 7 | `tests/test_phase18_corpus.py:430` | `assert len(values) == 10` |
| 8 | `tests/test_phase18_prereg.py:127` | `assert len(forbidden) == 10` |
| 9 | `tests/test_phase19_erasure.py:625` | `assert len(forbidden) == 10` |
| 10 | `tests/test_phase19_erasure.py:1689` | `assert taught == 10` |
| 11 | `tests/test_phase21_filler.py:165` | `assert len(fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS) == 10` |

**The plan's own two grep patterns find only 8 of these 11.** Sites 2, 10 and 11 match
`len(forbidden) == 10` and `len(values) == 10` neither. A third pattern, `(?:==|!=)\s*10(?![0-9_])`,
finds all eleven — which is exactly why the prompt required more than one.

**Excluded, each with its reason:**

| Candidate | Reason |
|---|---|
| `test_phase16_ladder.py:232` `row["rate"] == 10 / LADDER_CELL_QUESTIONS` | rate arithmetic — the 10 is a numerator |
| `test_phase16_ladder.py:233` `row["rate"] != 10 / draws` | rate arithmetic |
| `test_phase21_multiplicity.py:298` `len(TEN_SCHEMA_KEYS) == 10` | **plan 21-10's D-26 ROW-SCHEMA key count.** Named in NO prior census — it did not exist when 21-07 measured. This is the concrete reason a census may inherit a method but never a number |
| `test_phase21_filler.py:164` | a docstring naming the wall, not an assertion on it |

**Not counted, and recorded so the next reader meets them as facts:** `tests/test_phase21_sc5.py`'s
own `assert len(scored) == 10` (12th of the class) and `scripts/phase21_filler.py:263`'s
`assert len(FORBIDDEN_SCORED_VALUES) == 10` (13th, the only one in *source*). The census walks
`tests/` only and excludes its own file, so it measures the **pre-existing** wall.

**How the documented figures compare:**

| Source | Claimed | Measured here |
|---|---|---|
| `21-CONTEXT.md` D-18 | 4 sites | 11 |
| `21-RESEARCH.md` | 7 across 6 files | 11 across 8 |
| `21-09-PLAN.md` `<interfaces>` + `must_haves` | **8 across 7 files** | 11 across 8 |
| plan-check pass 3 | 9 | 11 |
| `21-07-SUMMARY.md` | 11 across 8 | **11 across 8 — agrees** |

The pin is a multiset of `(filename, expression)` with **line numbers deliberately absent**, so a
site that moves is not a failure while one that disappears or appears is. The failure message
prints every observed site with its line.

`test_wall_census_is_the_measured_set` also asserts `set(files) <= set(SC5_GUARD_SET)`, so a wall
site in a file this plan does not run turns the census red rather than going unsampled (T-21-41).

## The three deliberate-REDs, watched

**Every mutation was applied strictly AFTER the corresponding GREEN commit** (carry-forward 4 — the
ordering defect that destroyed 21-01's and 21-04's work). Restores removed the exact appended bytes
and were verified against a sha256 recorded **before** the mutation. `git checkout` was never used
for a restore.

### RED 1 — and the plan's specified canary DOES NOT FIRE

The plan asks for *"append a **comment** containing one filler value to `scripts/phase14_factset.py`.
Direction 1 must go RED."* Measured:

```
$ printf '\n# canary: kestrelaine\n' >> scripts/phase14_factset.py
$ pytest -q tests/test_phase21_sc5.py::test_no_filler_leak
1 passed
```

**It does not fire, and could not.** `embedded_fact_values` takes a MODULE OBJECT and walks the
strings the module *holds*; a `#` comment is discarded by the compiler and is not a string. Re-run
in the shape the instrument can actually see — and which is the recorded real leak shape, a value
quoted inside a report paragraph:

```
$ printf '\n_CANARY_NOTE = "the boat kestrelaine came up twice in review"\n' >> scripts/phase14_factset.py
E  AssertionError: direction 1: filler value(s) [('kestrelaine', 1)] are embedded in
   scripts/phase14_factset.py. A filler value inside a published instrument confounds the
   n=8-vs-n=64 comparison the n=64 arm exists to make unconfounded (T-21-04).
1 failed
```

Restored sha256 `35f0ad2e7325c7c51add4fa79f8a3a7d32dac2e72568b423068046d27286e62e` — equal to
pre-mutation; `git diff --exit-code` returns 0.

### RED 2 — both tiers fired, and the second had to be UNMASKED to be observed

Added `fs.Fact("filler_boat_canary", "filler_boat_name", "marrowgateford", "filler")` — a value
CONTAINING the locked `marrowgate`.

**Tier 1** (`phase21_filler`'s import-time refusal):

```
[phase21_filler] REFUSED against FORBIDDEN_SCORED_VALUES (the 10-value leak vocabulary,
LOCKED + SOFT): filler 'filler_boat_canary' value 'marrowgateford' contains scored value
'marrowgate'. ...
```

**A structural fact the plan's "Confirm BOTH tiers fire" glosses over:** tier 1 raises at *import*,
so `tests/test_phase21_sc5.py`'s own `import phase21_filler as pf` fails at collection and tier 2
never runs. The two-tier claim is untestable unless tier 1 is neutralised. Tier 2 was therefore
observed with `refuse_collisions()` commented out in an exec'd copy of the source (the file on disk
untouched by this step), running direction 3a's **exact** predicate:

```
tier 1 neutralised; module imported with 57 filler facts
TIER 2 (direction 3a) collisions: [('filler_boat_canary', 'marrowgateford', 'marrowgate')]
equality would admit it: True
```

`equality would admit it: True` is the point — `'marrowgateford' == 'marrowgate'` is False, so an
equality-based guard would pass this. Containment is load-bearing in both tiers.

Restored sha256 `bec49415029005cedba080f8dbb3402b0a82ddf11a87280069b0562dbf68d755` — equal to
21-07's recorded value.

### RED 3 — the ancestry-guarded file

```
$ printf '\n# canary\n' >> scripts/phase18_extraction.py
E  AssertionError: scripts/phase18_extraction.py changed: expected sha256 d2b44806…503d96,
   got cf3f7a367eb23753206c63d1776e996e5b7034d257cf0ab4ab662255330cac34. SC5 requires this file
   to be byte-identical across the n=64 corpus work. ...
1 failed
```

Restored sha256 `d2b44806a60228f0482851b737392299beef7206a93abdc2a2a0745204503d96`.

**Proof it was never committed:**

```
$ git log --oneline -1 -- scripts/phase18_extraction.py
99716e0 feat(18-13): reduce K 64 -> 48 in the pin, on pre-flight evidence
```

Phase 18 — predates this phase entirely. `git status --porcelain scripts/ results/` is empty.

## Plan vs Code Fidelity

Six mismatches, reported with evidence. `21-09-PLAN.md` was **not** amended.

**1. Every `teach_persona.py` line anchor in `<interfaces>` is stale.** The plan predicted this and
instructed locating by symbol; the instruction was correct and necessary.

| Symbol | Plan says | Measured |
|---|---|---|
| `ARMS` | `:163` | **`:226`** |
| `arm_outputs` | `:197` | **`:260`** |
| `arm_spec` | `:405-422` | **`:741`** |
| the `real` branch | `:413-421` | **`:749-757`** |
| unknown-arm `SystemExit` | `:422` | **`:758`** |
| `USAGE` | `:464` | **`:800`** |

`phase14_factset.py:390-399` (the eight locked ids) and `tests/test_phase14_scoring.py:349-364,
:398-402, :405` **all verify**, as the plan predicted for the non-`teach_persona` anchors.

**2. Direction 3 as specified is UNSATISFIABLE, not merely awkward.** The plan's
`embedded_fact_values(<phase21_filler module>, scored)` returns **22 hits** — 20 of them the bare
scored values held in `FORBIDDEN_SCORED_VALUES` and `PUBLISHED_POOL_VALUES`, 2 from the module
docstring. The module holds all ten scored values *because that is its refusal vocabulary*. Every
one of those strings was enumerated before re-scoping; the assertion could never return `[]`.

**3. The `== 10` wall is 11 sites across 8 files, not the plan's 8 across 7,** and one of the 11
(`test_phase21_multiplicity.py`'s exclusion aside) appeared after the most recent prior census.
Details above.

**4. `-k instruments_unchanged`, pinned at `21-VALIDATION.md:88-89` for BOTH sha256 rows, selects
ZERO tests against the plan's own test name** (`test_frozen_instruments_are_byte_unchanged` does not
contain the contiguous substring `instruments_unchanged`). pytest reported `4 deselected in 0.51s`
and exited **0** — a verification command passing vacuously. Fixed by renaming the test to
`test_instruments_unchanged_byte_for_byte`; all three pinned selectors now select exactly one test.

**5. The plan's Task-2 deliberate-RED canary shape does not fire.** A `#` comment is invisible to
`embedded_fact_values`. Detailed under RED 1.

**6. `.venv/bin/python` does not exist in a worktree.** Every acceptance criterion and the whole
`<verification>` block spell it relatively. The worktree has no `.venv`; all commands were run
through `/Users/juliorcoelho/PersonaCore/.venv/bin/python` with the editable install repointed at
this worktree.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] `_slot_forms_for(facts)`: the n=64 capacity was unreachable**

- **Found during:** Task 1, on the first attempt to actually build the arm.
- **Issue:** `arm_spec('dp_n64')` returns 64 facts and both `render_episodes` and `sanity_check`
  raise `KeyError: 'filler_boat_name'` on them, because `render_family`'s default grammar is
  `fs.SLOT_FORMS` and the filler slots are deliberately disjoint from the published 11. The plan
  does not mention this at all; its acceptance criteria stop at `arm_spec`'s return tuple.
- **Fix:** `_slot_forms_for(facts)` in `scripts/teach_persona.py` (this plan's own file — neither
  `phase14_factset.py` nor `phase21_filler.py` was touched). `None` for every published-slot corpus
  so `render_family` runs the identical code path; the union when filler is present.
- **Commit:** `5634ada`

**2. [Rule 2 — Missing critical functionality] Two guards on the widened slot grammar**

- **Found during:** Task 1, writing `_slot_forms_for`.
- **Issue:** `{**SLOT_FORMS, **FILLER_SLOT_FORMS}` silently **prefers the filler mapping** on a key
  collision, which would let a filler grammar replace a published slot's rendering — the same trust
  boundary the `== 10` wall protects one level down, and invisible to it. Separately, an undeclared
  slot would surface as a bare `KeyError` from inside `_render_family` naming no fact and no arm,
  which is exactly the diagnostic vacuum this defect was found in.
- **Fix:** both raise `SystemExit` naming the offending slots.
- **Commit:** `5634ada`

**3. [Rule 1 — Bug] The pinned `-k instruments_unchanged` selector matched nothing**

- **Found during:** Task 3's deliberate-RED, which reported `4 deselected` instead of a failure.
- **Fix:** renamed the test so the published selector selects it. Detailed above.
- **Commit:** `23d3067`

No Rule 4 (architectural) decision arose. No package was installed.

### Deliberate departures, with reasons

- **Tasks 2 and 3 land in ONE commit.** Both deliver into the single file `tests/test_phase21_sc5.py`
  and were authored together. Splitting after the fact would have meant deleting and re-adding ~60
  lines mid-cycle — precisely the ordering hazard that destroyed work in 21-01 and 21-04.
- **Direction 3 re-scoped** (see Fidelity 2). The plan's version is unsatisfiable.
- **The census pins a measured multiset, not the plan's hard-coded 8.** The plan says *"If the
  discovered count is not 8, FAIL with the observed list rather than adjusting the expected
  number"* — which, taken literally, means shipping a permanently-red test. The instruction's
  *intent* (a moved wall is a finding, never a silently-updated number) is preserved: the pin is
  measured, line numbers are excluded so drift is tolerated, and the failure message prints every
  observed site.

## Verification

| Check | Result |
|---|---|
| `pytest -q tests/test_phase21_sc5.py tests/test_phase21_filler.py` | **17 passed** |
| SC5 guard set (8 files) + `test_phase16_prereg.py` + `test_phase21_multiplicity.py` + this file | **361 passed, 2 skipped** |
| `-k no_filler_leak` (`21-VALIDATION.md:87`) | 1 passed, 3 deselected |
| `-k wall_census` | 1 passed, 3 deselected |
| `-k instruments_unchanged` (`21-VALIDATION.md:88-89`) | 1 passed, 3 deselected — **selects, after the rename** |
| **Full suite** | **963 passed, 7 skipped in 201.13s**, exit 0 |
| `git diff --exit-code` on the 6 frozen paths | **0** |
| `git status --porcelain scripts/ results/ data/` | **empty** — every canary restored |
| `git ls-files 'results/phase21_*'` | **empty** |
| `git log --oneline -1 -- scripts/phase18_extraction.py` | `99716e0 feat(18-13)` — predates this phase |
| `ruff check . && ruff format --check .` | All checks passed · 187 files formatted |
| `.planning/STATE.md` / `ROADMAP.md` | byte-unchanged (worktree mode — the orchestrator owns them) |

**The full-suite count reconciles exactly.** `21-VALIDATION.md`'s figures are stale (21-10 already
recorded this) so the live numbers are used. Worktree baseline is 955 passed / 7 skipped — main's
961 less the 6 tests that skip here for want of gitignored artifacts. This plan adds **4 new tests**
and **4 new parametrized cases** (`test_phase14_teaching.py`'s two `@parametrize("arm", tp.ARMS)`
tests x the 2 new arms; verified by `--collect-only`, which now reports 42 collected with 4 `dp_n*`
cases). `955 + 4 + 4 = 963`. Zero failures.

## Requirements — deliberately NOT marked complete

`UNIT-06` is this plan's `requirements:` frontmatter and it is **not** marked complete;
`REQUIREMENTS.md` was not modified. UNIT-06 spans the filler corpus (21-07), both arms (here) and
the recorded measurement (21-11). Marking it complete before 21-11 writes and commits
`results/phase21_*` would claim a measurement that does not exist, and `21-CONTEXT.md` names
"do not mark a requirement complete in the first plan that touches it" as an Established Pattern.

## Known Stubs

None. Both arms are fully wired and both were built end-to-end through the real tokenizer and the
real packer. `_slot_forms_for` has no placeholder branch — its `None` path is the pre-existing
behaviour and is exercised by every existing arm in the green full suite; its union path is
exercised by the `dp_n64` build. No hardcoded empty value flows anywhere.

## Threat Flags

None. This plan adds no network endpoint, no auth path and no new file-access pattern. Every new
read is of the project's own trusted material — six `scripts/*.py` sources, one tracked `results/`
fixture, and `tests/*.py` for the census — and nothing new is written outside a scratch directory.

Register dispositions, all `mitigate`, all satisfied: T-21-04 (filler in the leak vocabulary —
direction 1 over six instrument sources plus direction 2 over the 270-question fixture, RED
observed), T-21-39 (a scored value inside filler — directions 3a/3b, RED observed with tier 1
unmasked), T-21-08 (any edit to the two frozen files — two byte-mode sha256 pins, RED observed),
T-21-40 (CRLF passing a text-mode hash — both files read as bytes, reason in this test's own
docstring), T-21-41 (under-sampling the wall — the mechanical census, measured at 11 and coupled to
the guard set), T-21-42 (replay re-entering the teaching bin — `replay_ratio = 0.0` asserted on both
arms), T-21-43 (a mutation committed rather than restored — three sha256-verified restores, empty
porcelain, `git log` predating the phase), T-21-55 (a canary live beside a concurrent reader — sole
executor in wave 5, behind 21-10), T-21-56 (a guarded file listed as editable — none of the three
mutated paths is in `files_modified`), T-21-11 (supply chain — zero package installs).

## Commits

| Commit | Task | Content |
|---|---|---|
| `5634ada` | 1 | `ARMS` + both `arm_spec` branches + `_slot_forms_for` — both capacities REACHED |
| `3941236` | 2, 3 | `tests/test_phase21_sc5.py` — 4-direction leak scan, wall census, two sha256 pins, exact tier composition |
| `23d3067` | 3 | rename so `-k instruments_unchanged` actually selects |

## Self-Check: PASSED

- `scripts/teach_persona.py` — FOUND on disk, contains `dp_n64`, `dp_n8`, `_slot_forms_for`
- `tests/test_phase21_sc5.py` — FOUND on disk, 4 tests, all green
- Commits `5634ada`, `3941236`, `23d3067` — all present in `git log 4006ad8..HEAD`
- Working tree clean before this SUMMARY; `git diff --exit-code` on all six frozen paths returns 0
- `git ls-files 'results/phase21_*'` empty — 21-11's `adds[-1]` ordering intact
- `.planning/STATE.md` and `.planning/ROADMAP.md` untouched, per worktree mode
- No gitignored artifact was produced that 21-11 needs — both capacity builds went to a scratch
  directory outside the repo, so nothing needed copying back to the main checkout
