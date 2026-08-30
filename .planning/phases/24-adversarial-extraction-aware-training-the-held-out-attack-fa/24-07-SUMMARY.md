---
phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
plan: 07
subsystem: measurement-record
tags: [band-guard, four-corner, committed-record, provenance, write-once, token-budget, advt-03]

# Dependency graph
requires:
  - phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
    provides: "24-06's `build_bins(..., adversarial_ratio=, seed=)` seam and its nine additive stats keys — every figure in this plan is read off it"
  - phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
    provides: "24-02's `mitigation_budget.ADVERSARIAL_RATIO_GRID` and `ADVERSARIAL_RATIO_GRID_PROVENANCE` — imported, never retyped"
  - phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
    provides: "24-05's parity-proved 336-episode attack pool and `HELD_OUT_FAMILY`/`TRAINED_FAMILIES`"
  - phase: 21-the-fact-aligned-packer
    provides: "`phase21_unit_record`'s writer discipline — `refuse_existing_artifacts(paths=)`, `_PUBLICATION_PATHSPEC`, `_DIRTY_DETAIL`, `_provenance`, and `_corpus_geometry`'s figure-carries-its-denominator row shape"
provides:
  - "`tests/test_phase24_band.py` — the D-05 four-corner build-only band check, binding corner first, 2.22 s"
  - "`scripts/phase24_record.py` — `TOKEN_BUDGET_RECORD` plus the write-once, refuse-if-dirty emitter"
  - "`results/phase24_token_budget.json` — 12 rows of integer scored-token counts with denominators, D-07 multiplicity in-row, the token-budget confound, and SC4's explicit discharge"
  - "`tests/test_phase24_record.py` — coverage, counts-with-denominators, live re-derivation under exact `==`, band clearance and monotonicity, and the 3.73x/1.40x separation"
  - "the DECISION on 24-06's open per-episode-floor question, shipped as a test rather than a paragraph"
affects: [25 frontier sweep driver, 25 SC3 multiplicity reporting, 25 SC4 single-source-of-truth artifact]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A decision left open by a prior plan is closed by an ASSERTION, not by prose — `test_the_per_episode_floor_is_a_scored_token_count_and_not_a_fraction` measures all three reasons and goes red if any inverts"
    - "The dirty-tree pathspec is scoped to what the recorded SHA actually claims (code + data), not to `.` — a guard that blocks an honest emission on planning prose is the class that gets deleted"
    - "Commit the emitter BEFORE its artifact, because the guard counts untracked files as dirty: the ordering is the guard's consequence, and `git cat-file -e {sha}:{emitter}` checks it afterwards"
    - "The binding corner is identified by `argmin` over the measured corners, not declared — so a future inversion moves the record instead of silently invalidating it"

key-files:
  created:
    - tests/test_phase24_band.py
    - scripts/phase24_record.py
    - results/phase24_token_budget.json
    - tests/test_phase24_record.py
  modified:
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/STATE.md

key-decisions:
  - "NO per-episode mask-fraction gate. 24-06 flagged `mask_fraction_min = 0.1111` as below the 0.15 floor and left the call to this plan; the decision is NOT to gate it, for three measured reasons, and the decision ships as a test"
  - "`refuse_if_dirty`'s pathspec is `(scripts, src, results, artifacts, :(exclude)<record>)` and NOT the plan's `.` — measured: `.` refuses on `.gitignore` and `.planning/todos/`, neither of which can move a single count"
  - "ADVT-02 and ADVT-03 TICKED, ADVT-01 deliberately NOT — the first requirement movement of the whole phase, after six plans declined"
  - "The ROADMAP phase-heading checkbox, the progress-row Status cell and STATE's `status`/`completed_phases`/`percent` were left UNTOUCHED: they belong to the phase-close step (precedent `5a72670`, phase 23)"

patterns-established:
  - "Watch the RED in the file's NATURAL intermediate state rather than by planting: the dirty guard's first observation was taken while the emitter was still untracked, which demonstrated the commit-order lesson and the refusal in one shot"
  - "A hand-edit probe counts its occurrences FIRST (`str.count` == 1, line-anchored, post-edit line printed) and restores by writing back saved bytes under a sha256 equality check — never `git checkout --`"

requirements-completed: [ADVT-02, ADVT-03]

# Metrics
duration: 23min
completed: 2026-08-30
---

# Phase 24 Plan 07: The Four-Corner Band Check and the Committed ADVT-03 Record — Summary

**All four D-05 corners are measured in 2.22 seconds before any sweep point exists — `adv_n8`
0.358660 → 0.241009 and `adv_n64` 0.390163 → 0.251734, the n=64 column MEASURED rather than carried
across — and `results/phase24_token_budget.json` now holds twelve rows of integer scored-token
counts with their denominators, closing the gap 24-RESEARCH found: nothing in this repository
persisted a v4.0 arm's mask fraction. 24-06's open per-episode-floor question is decided against a
gate, and the decision ships as a test.**

## Performance

- **Duration:** 23 min (2026-08-30T18:39:52Z start → the metadata commit's own timestamp)
- **Task commits:** 18:44:41Z (`6c1327b`), 18:49:33Z (`5aed70f`), 18:50:12Z (`7075951`),
  18:52:31Z (`8fd67eb`)
- **Tasks:** 3 of 3 — Task 2 landed as TWO commits by design (emitter, then artifact); see below
- **Files:** 4 created (239 + 503 + 667 + 279 lines), 3 planning files edited, **0 source files
  modified**

## Task Commits

1. **Task 1 — the D-05 four-corner band check** — `6c1327b` (test) — `tests/test_phase24_band.py`
   (+239).
2. **Task 2a — the emitter** — `5aed70f` (feat) — `scripts/phase24_record.py` (+503).
3. **Task 2b — the artifact** — `7075951` (docs) — `results/phase24_token_budget.json` (+667).
4. **Task 3 — the re-derivation tests** — `8fd67eb` (test) — `tests/test_phase24_record.py` (+279).

**Plan metadata:** the `docs(24-07)` commit carrying this SUMMARY, STATE.md, ROADMAP.md and
REQUIREMENTS.md.

**No commit in this plan's history leaves HEAD red.** Task 1's module was green on first run — the
band was already cleared at every corner, so no refusal-template lengthening was needed and
`scripts/phase24_adversarial.py` was never touched.

## The four corners — the figures this plan was required to publish

Measured through `tp.build_bins(..., align_facts=None, adversarial_ratio=r, seed=tp.SEED)`, flat
pack, under `tmp_path`. `MASK_FRACTION_BAND = (0.15, 0.95)`, `MASK_FRACTION_MARGIN = 0.05`, so the
required target is **0.20**.

| corner | `mask_fraction` | margin over the 0.15 floor | clears 0.20? |
|---|---|---|---|
| `adv_n8` @ 0.0 (control) | **0.358660** | 0.208660 | yes |
| `adv_n64` @ 0.0 (control) | **0.390163** | 0.240163 | yes |
| `adv_n64` @ 1.9090909090909092 | **0.251734** | 0.101734 | yes |
| **`adv_n8` @ 1.9090909090909092 (BINDING)** | **0.241009** | **0.091009** | **yes, by 0.041009** |

**The binding corner is `(adv_n8, upper)`, confirmed by measurement:** 0.241009 < 0.251734. It is
asserted as an ORDERING (`argmin` in the record, a strict `<` in the test), not declared — n=64's
much larger clean bin dilutes the fixed 336-episode pool's unmasked prompt mass, so calibrating the
refusal length against it would be calibrating against the easier corner.

The control corners reproduce the flat operating point to six decimals. **The n=64 column was
measured, never inherited:** 24-06 measured only n=8 and said so, and this plan's `adv_n64` figures
(0.390163 → 0.251734) come from its own builds.

**No corner failed, so there was no template lengthening and no before/after pair to record.**
`MASK_FRACTION_BAND` was not touched; it is Phase 14's.

### Wall clock

| Command | Measured |
|---|---|
| `pytest -q tests/test_phase24_band.py` (7 items, four builds) | **2.22 s** (2.835 s wall) |
| the binding corner alone, `[adv_n8-upper]` | **0.75 s** (1.342 s wall) |

Both are far inside the plan's 60 s / 20 s budgets and inside 24-VALIDATION.md's 20-second sampling
contract, so the plan's pre-emptive exception for this module was not needed.

## 24-06's open question, DECIDED: no per-episode fraction gate

24-06 recorded `mask_fraction_min = 0.1111` at the upper extreme — below the 0.15 band floor — and
explicitly left the call here. **The decision is not to gate it**, and it is a test
(`test_the_per_episode_floor_is_a_scored_token_count_and_not_a_fraction`), not a paragraph. Three
measured reasons:

1. **The minimum is an A3 episode: 18 scored tokens in 162 = 0.111111.** A per-episode *fraction*
   conflates "the answer is too short" with "the attack prompt is long", and A3's entire design is a
   long value-free role scaffold riding at mask=0. Gating the fraction would refuse the attack shape
   D-10 deliberately trains on. Per-family minima measured: A1-mild 0.202247, A1-aggressive
   0.172414, A3 0.111111 — the ordering tracks mean prompt length (65.57 / 90.79 / 139.64 tokens
   including the answer), not answer length.
2. **The per-episode quantity that IS well defined already has a floor.** Every one of the 336
   adversarial episodes scores **18–23** tokens against `MIN_REFUSAL_SCORED_TOKENS = 15`. The answer
   is never short; only the prompt is long.
3. **The CLEAN teaching pool carries FEWER scored tokens than any adversarial episode** — min
   **11** against 18 — and has never been gated per-episode in this repository's history (its own
   per-episode minimum fraction, 0.188406, sits 0.038 above the floor with no gate). An
   adversarial-only per-episode floor would be gating the population that needs it least.

The test asserts reasons 2 and 3 directly (`min(scored) >= MIN_REFUSAL_SCORED_TOKENS` and
`min(clean_scored) <= min(scored)`), so an inversion of either is red rather than silent. The
finding is also carried into the committed record as `mask_fraction_min` plus a
`mask_fraction_min_note` on every row, so the number and its non-gating are both readable off the
artifact.

## The committed record

`results/phase24_token_budget.json`, 667 lines, top-level keys
`grid / arms / rows / band_corners / token_budget_disclosure / attack_corpus / provenance` —
`provenance` last.

### The 12 rows

`scored_tokens` is `int(np.fromfile(mask_path, dtype=np.uint8).sum())` off the bin actually written
— never `mask_fraction * total_tokens`.

| arm | ratio | clean eps | adv eps | multiplicity | total tokens | scored tokens | `mask_fraction` |
|---|---|---|---|---|---|---|---|
| `adv_n8` | 0.0 | 176 | 0 | 0.0000 | 7,581 | 2,719 | 0.358660 |
| `adv_n8` | 0.25 | 176 | 44 | 0.1310 | 11,687 | 3,515 | 0.300762 |
| `adv_n8` | 0.5 | 176 | 88 | 0.2619 | 15,903 | 4,395 | 0.276363 |
| `adv_n8` | 1.0 | 176 | 176 | 0.5238 | 24,658 | 6,305 | 0.255698 |
| `adv_n8` | 1.5 | 176 | 264 | 0.7857 | 33,417 | 8,233 | 0.246372 |
| `adv_n8` | 1.909… | 176 | 336 | 1.0000 | 40,733 | 9,817 | 0.241009 |
| `adv_n64` | 0.0 | 1,408 | 0 | 0.0000 | 72,093 | 28,128 | 0.390163 |
| `adv_n64` | 0.25 | 1,408 | 352 | 1.0476 | 106,601 | 35,514 | 0.333149 |
| `adv_n64` | 0.5 | 1,408 | 704 | 2.0952 | 141,188 | 42,900 | 0.303850 |
| `adv_n64` | 1.0 | 1,408 | 1,408 | 4.1905 | 210,629 | 57,716 | 0.274017 |
| `adv_n64` | 1.5 | 1,408 | 2,112 | 6.2857 | 280,126 | 72,552 | 0.258998 |
| `adv_n64` | 1.909… | 1,408 | 2,688 | 8.0000 | 337,309 | 84,912 | 0.251734 |

The n=8 column reproduces 24-06's independently-measured table exactly (0.3008 / 0.2764 / 0.2557 /
0.2464 / 0.2410), which is a cross-check across two sessions and two code paths, not a copy.

**A finding worth Phase 25's attention: D-07 multiplicity is NOT comparable across capacities at the
same nominal ratio.** The grid's upper extreme is `336/176`, defined at n=8, where it means exactly
one pass of the pool. At n=64 the SAME nominal ratio is **8.0×** — the pool is repeated eight times
— and even n=64's smallest non-zero point (0.25) is already **1.0476**, i.e. more than one full
pass. Phase 25 SC3 requires multiplicity in the same sentence as ε precisely because of this, and it
is why the figure travels in the row rather than in a sibling table.

### Every figure carries its own computation, denominator and bound

Per row: `scored_tokens_denominator`, `scored_tokens_source`, `scored_tokens_formula`,
`total_tokens_source`, `teaching_tokens_source` (which states in words that `teaching_tokens` is
CLEAN-ONLY by design and is **not** the bin's total — the trap a reader would otherwise fall into),
`mask_fraction_source` / `_formula` / `_band` / `_margin_over_floor` / `_margin_required`,
`adversarial_pool_size_source`, `adversarial_multiplicity_formula`,
`adversarial_family_counts_source`, `mask_fraction_min_note`.

### The token-budget confound, both figures kept distinct

Counted live off `results/phase18_corpus.json`'s `prompt_ids`, `core_taught` tier:

| family | n | total prompt tokens | mean | min | max |
|---|---|---|---|---|---|
| A1-mild | 112 | 4,978 | 44.4464 | 32 | 71 |
| A1-aggressive | 112 | 7,802 | 69.6607 | 52 | 98 |
| A3 | 112 | 13,274 | 118.5179 | 106 | 144 |
| **A2 (HELD OUT — listed separately, never in a trained total)** | 112 | 3,558 | 31.7679 | 19 | 57 |

- **Trained pool: 336 episodes, 26,054 prompt tokens.**
- `cross_family_inflation` = **3.73** (`_exact` 3.7307476110174256 = A3 mean / A2 mean, 112 rows
  each). Its note states in words that this is A3/A2 and is **NOT** ADVT-03's **1.40×**, which is 49
  uppercased tokens over 35 clean for ONE 51-character sentence — a per-sentence perturbation cost,
  not a per-family corpus mean. The two differ by ~2.7×.
- `leave_one_out_token_spread` = **1.59** (`_exact` 1.594687232219366), from the four leave-one-out
  totals `{A1-mild: 24,634, A1-aggressive: 21,810, A2: 26,054, A3: 16,338}` — every choice trains
  exactly 336 episodes, so the EPISODE count is invariant and only the TOKEN volume moves. That is
  D-06's reason for sweeping episodes and reporting tokens here instead.

`test_the_token_budget_confound_keeps_both_figures_distinct` asserts 1.40 is never the numeric value
of any field whose key contains `inflation`.

### SC4 discharged explicitly

`attack_corpus.new_attack_corpus = false`, `inflation_report_required = false`, plus a written
`inflation_report_discharge` string: the obligation attaches to a NEW corpus and this phase creates
none. `sha256 = ff8e6e3c24987ac393cc262233f1b0bfdad5dc11eefa4cc1224a164cfd0f7d67`, recomputed live
through `p18.corpus_sha256` at write time and re-recomputed live again by the test — never pasted.
It matches the digest 24-02 independently recorded in
`ADVERSARIAL_RATIO_GRID_PROVENANCE.upper_extreme_source_provenance`.

## The refusals, watched

### refuse-if-dirty, observation 1 (emitter still untracked — the commit-order lesson, live)

```
[phase24_record] REFUSING: the working tree is dirty.
?? scripts/_phase24_dirty_probe.txt
?? scripts/phase24_record.py
`provenance.git_sha()` records HEAD at write time, so a record written from a dirty tree names a
commit that does NOT contain the code that produced it — ...
artifact exists after probe: False
```

Taken via `_write(TOKEN_BUDGET_RECORD, {'probe': True})` from `python -c`, never through `main()` —
the guard fires in a millisecond and building twelve bins to reach it would have been waste.
**No bytes landed.**

### refuse-if-dirty, observation 2 (clean tree, only the scratch file in scope)

After committing `5aed70f`, so the refusal names ONLY the planted file:

```
[phase24_record] REFUSING: the working tree is dirty.
?? scripts/_phase24_dirty_probe.txt
artifact exists after probe: False
```

Scratch file deleted; `git status --porcelain -- scripts src results artifacts` empty afterwards.

### refuse-to-rerun

```
[teach_persona] /Users/juliorcoelho/PersonaCore/results/phase24_token_budget.json already exists —
this arm is recorded evidence. Delete /Users/juliorcoelho/PersonaCore/results/phase24_token_budget.json
to re-run.
```

`refuse_existing_artifacts(paths=[TOKEN_BUDGET_RECORD])` — IMPORTED from `phase21_unit_record`, and
its `paths=` parameter is what made it reusable here.

### The CR-02 check, run rather than trusted

```
git_sha 5aed70fb017213eaf3cb1814a5fd77392fa90f34
git cat-file -e 5aed70f:scripts/phase24_record.py  ->  ok
```

`scripts/phase24_record.py` (`5aed70f`) is committed BEFORE
`results/phase24_token_budget.json` (`7075951`), which is a consequence of the guard counting
untracked files as dirty, not a workaround for it. All four `provenance.module_sha256` pins and
`tokenizer_sha256` were re-verified against the files on disk: all OK.

### `refuse_dirty_publication` deliberately NOT used

Measured at HEAD: `phase21_unit_record.is_publication_target` (`:257-267`) compares the resolved
path against `ARTIFACTS.values()` — `phase21_privacy_unit.json` and `phase21_multiplicity.json`
only — so the wrapper returns `None` for any phase-24 path and would have protected nothing.
`grep -n "refuse_dirty_publication" scripts/phase24_record.py` returns **nothing** (0 hits), and an
AST call-walk confirms **0 calls**; both instruments were run, since a grep-absence claim over a file
whose prose would naturally discuss the name is exactly hazard #2.

## The hand-edit RED, watched

Occurrences counted FIRST (hazard #3): `"scored_tokens": 2719,` occurs **exactly once** in the
record, and `2719` occurs exactly once anywhere in it, at **line 71**. Post-edit line printed:
`"scored_tokens": 2718,`.

```
FAILED tests/test_phase24_record.py::test_every_row_reports_counts_with_a_denominator
FAILED tests/test_phase24_record.py::test_scored_tokens_re_derive_from_a_rebuild
2 failed, 3 passed in 0.57s

E  AssertionError: adv_n8 @ the control point rebuilt 2,719 scored tokens against the recorded
   2,718. Either the record was hand-edited, or the packer, the tokenizer or the teaching pack moved
   without the record being regenerated.
E  assert 2719 == 2718
```

**Two independent instruments caught it** — the live rebuild (test 3) and the counts-to-rate
agreement (test 2) — where the plan required one. Restored by writing back the saved original bytes
and asserting sha256 equality
(`8d3e474ffd3f0dd2fb8216600db9181b1361cd4f7cf62e3ed09af268faf8bf46`), never `git checkout --`
(hazard #4); `git diff --exit-code results/phase24_token_budget.json` clean; re-run **5 passed**.

## Deviations from Plan

### 1. [Rule 3 — Blocking] `refuse_if_dirty`'s pathspec is scoped to the record's real inputs, not `.`

- **Found during:** Task 2, before the emitter's first run.
- **Issue:** the plan prescribes `pathspec = (".", f":(exclude){record}")`. **Measured on this
  tree**, `git status --porcelain -- "." ":(exclude)results/phase24_token_budget.json"` returns
  ` M .gitignore` and `?? .planning/todos/` — a user's `.obsidian/` ignore rule and GSD workflow
  state, both pre-existing, both outside this plan's remit to commit, and **neither able to move a
  single count in the record**. With `.` the emitter could never run, and the "fix" would have been
  to sweep unrelated changes into a phase-24 commit.
- **Fix:** the pathspec is `("scripts", "src", "results", "artifacts", ":(exclude)<record>")` —
  exactly what the recorded `git_sha` claims to carry (the emitter and packer, the encoder that sets
  every mask bit, the corpus, the frozen tokenizer), with the reasoning and the measurement written
  into the module beside it. **Every acceptance criterion still holds:** a scratch file under
  `scripts/` still fires the guard, which is the criterion the plan actually states. Watching
  `.planning/` prose would also have made the guard unusable in every GSD plan by construction —
  SUMMARY/STATE/ROADMAP are written *after* the emitter runs.
- **Files modified:** `scripts/phase24_record.py`.
- **Commit:** `5aed70f`.

### 2. [Rule 2 — Missing critical functionality] A fourth test in Task 1's module, carrying the per-episode decision

- **Found during:** Task 1.
- **Issue:** the plan specifies three tests. The orchestrator required 24-06's `mask_fraction_min`
  question to be "decided explicitly and justified", and a decision recorded only in a SUMMARY is
  the exact shape this plan exists to correct — an unrepeatable claim.
- **Fix:** `test_the_per_episode_floor_is_a_scored_token_count_and_not_a_fraction` measures all
  three reasons (see above) and goes red if the adversarial pool ever becomes the shorter-answer
  population or drops below `MIN_REFUSAL_SCORED_TOKENS`. The record carries the same finding per row.
- **Commit:** `6c1327b`.

### 3. [Rule 3 — Blocking] Task 2 shipped as TWO commits, which the plan requires but does not count

- **Found during:** Task 2.
- **Issue:** the plan's `<files>` names both the emitter and the artifact, but its own
  "COMMIT ORDER IS LOAD-BEARING" section mandates emitter → run → artifact as three steps. One
  commit would have meant the guard was bypassed — and the plan makes that an acceptance criterion.
- **Fix:** `5aed70f` (emitter) then `7075951` (artifact), verified by
  `git cat-file -e 5aed70f:scripts/phase24_record.py`.

### 4. [Rule 1 — Bug] `build_bins` does not create its parent directory

- **Found during:** Task 1's first run. Two tests failed with
  `FileNotFoundError: .../test_the_control_corner_reprod0/adv_n8/adv_n8.bin` because
  `_build_corner` was handed per-corner `tmp_path` subdirectories.
- **Fix:** one line, `tmp_path.mkdir(parents=True, exist_ok=True)` in the test helper. **Not** fixed
  in `teach_persona.build_bins` — every production caller passes a path under an existing directory,
  and widening a byte-identity-guarded packer to mkdir would be a change to the packer for a test's
  convenience.
- **Commit:** `6c1327b`.

### 5. [Rule 3 — Blocking] The ROADMAP progress-row Status cell was set to `Complete` and then reverted

- **Found during:** the ROADMAP edit.
- **Issue:** phase 23's history (`5a72670`, `docs(phase-23): complete phase execution`) shows the
  phase-CLOSE step owns the phase-heading checkbox, the progress-row Status cell, and STATE's
  `status` / `completed_phases` / `percent`. The last plan's executor owns only the plan checkbox
  and the plan count.
- **Fix:** a targeted inverse edit restored `| In progress | - |` while keeping `6/7 → 7/7`
  (`git diff` shows exactly the two intended `| 24.` lines). `tests/test_phase24_correction.py`
  re-run green after the revert.

**Total deviations: 5.** No architectural change, no package installed, no checkpoint reached, no
authentication gate, no source file outside this plan's own new modules modified.

## Anchors, re-measured (hazard #5)

Twelve of the plan's `<interfaces>` citations resolve exactly; four do not, and all four are in
`scripts/teach_persona.py`, shifted by 24-06's own +157 lines — which the plan itself half-anticipated.

| Anchor | Plan said | Measured at HEAD |
|---|---|---|
| `phase21_unit_record.ARTIFACTS` | 168 | **168** ✓ |
| `_PUBLICATION_PATHSPEC` | 183 | **183** ✓ |
| `_DIRTY_DETAIL` | 188 | **188** ✓ |
| `refuse_existing_artifacts` | 246 | **246** ✓ |
| `is_publication_target` | 257 | **257** ✓ |
| `refuse_dirty_publication` | 269 | **269** ✓ |
| `_provenance` | 702-726 | **702** ✓ |
| `_write` | 729-753 | **729** ✓ |
| `_corpus_geometry` | 1237-1259 | **1212** (the plan's range is its RETURN block, not its `def`) |
| `provenance.refuse_if_dirty` | 47-80 | **47** ✓ |
| "Untracked files count as dirty" | 62-65 | **62** ✓ |
| `phase18_extraction.CORPUS_PATH` | 697 | **697** ✓ |
| `phase18_extraction.corpus_sha256` | 758 | **758** ✓ |
| `test_phase23_budget._cost_record` | 359-380 | **373** ✓ (inside the range) |
| `teach_persona.MASK_FRACTION_BAND` | 127 | **128** |
| `teach_persona.build_bins` | 465-530 | **483** |
| `teach_persona._prove_floor_and_band` | 528 | **605** |
| the band check `if not lo <= frac <= hi` | 549 | **628** |

The record's `mask_fraction_source` names **`teach_persona.py:628`**, the measured line, not the
plan's stale 549.

Two plan-text defects found and worked around rather than reproduced:

- Task 3 test 5 prescribes `p18.corpus_sha256(json.load(p18.CORPUS_PATH))`. `json.load` takes a file
  object and `CORPUS_PATH` is a `Path`; the test uses
  `json.loads(p18.CORPUS_PATH.read_text(encoding="utf-8"))`.
- Task 2's row spec names `total_tokens` and `teaching_tokens` as if `build_bins` returned them under
  those keys; the stats key is `tokens`. The record uses `total_tokens` as its own field name, read
  from `stats["tokens"]`, with the source label saying so.

## Verification Results

| Check | Result |
|---|---|
| `pytest -q tests/test_phase24_band.py` | **7 passed**, 0 failed, **2.22 s** |
| `pytest -q "...band.py::...floor_with_margin[adv_n8-upper]"` | **1 passed**, **0.75 s** |
| `pytest -q tests/test_phase24_record.py` | **5 passed**, 0 failed, 0.65 s |
| `pytest -q` over all nine `tests/test_phase24_*.py` | **49 passed**, 0 failed, 3.89 s |
| `pytest -q tests/test_phase24_refusal.py tests/test_phase14_scoring.py tests/test_phase21_sc5.py tests/test_phase24_bins.py` | **61 passed**, 0 failed |
| `tests/test_phase24_correction.py` after the ROADMAP edit (and again after the revert) | **4 passed** |
| ROADMAP sentinels after the tick | `24-03-CONTINUATION-BEGIN` 1, `-END` 1, `SUPERSEDED IN PLACE…` 1, SC2 claim (normalized) **1** |
| **Full suite** `.venv/bin/python -m pytest -q` | **1645 passed, 1 skipped**, 0 failed, **381.79 s**, exit 0 |
| Baseline reconciliation | orchestrator-measured **1633 passed / 1 skipped**; delta **+12 = 7** (band) **+ 5** (record). Fully accounted for; nothing else moved |
| AST: `0.15` / `0.95` / `1.9090909090909092` as float literals in `test_phase24_band.py` | **none** — band and grid both imported |
| AST: executable string spelling `phase24_token_budget` in `test_phase24_record.py` | **none** (docstrings excluded); `TOKEN_BUDGET_RECORD` appears 2× |
| AST: `336` as an int literal in `teach_persona` / `phase24_adversarial` / `phase24_record` / both new tests | **0 in all five** |
| AST: `phase24_adversarial` module-level imports | `['pathlib', 'phase14_factset', 'sys']` — the lazy-import boundary holds |
| `grep -n "refuse_dirty_publication" scripts/phase24_record.py` | **nothing** (0 hits); AST call-walk **0 calls** |
| `grep -n "refuse_if_dirty\|refuse_existing_artifacts" scripts/phase24_record.py` | both present, both IMPORTED, neither redefined |
| `(?:==\|!=)\s*10(?![0-9_])` over both new test modules | **0 hits** — the twelve-member SC5 wall census needed no edit |
| `persona=` call sites in both new test modules | **0** — `PERSONA_ALLOWLIST`'s hard-equality census needed no entry |
| Record shape | last key `provenance`, `rows` == 12, all `scored_tokens` positive `int`, all denominators non-empty, `new_attack_corpus` `false`, `held_out_family` `"A2"` |
| `provenance.module_sha256` (4 modules) + `tokenizer_sha256` vs disk | **all 5 match** |
| `git diff scripts/phase18_extraction.py scripts/mitigation_gate.py` | **empty** — both frozen modules unmoved |
| `git status --porcelain data/` | **empty** — nothing was ever written there; all bins under `tmp_path` / `TemporaryDirectory` |
| `ruff check .` / `ruff format --check .` | All checks passed; **230 files** formatted |

**No `gsd-sdk` mutation handler was called.** STATE.md, ROADMAP.md and REQUIREMENTS.md were
hand-edited with occurrence-counted replacements (repo hazard #1), matching all six prior plans.

### Method substitutions

- The plan's two AST criteria were used verbatim and both pass.
- `grep -n "refuse_dirty_publication"` is an ABSENCE claim over a file whose prose would naturally
  discuss the name (hazard #2), so it was honoured literally — the identifier appears nowhere, and
  the module explains the decision by naming `is_publication_target` instead — and **backed by an
  AST call-walk** returning 0 calls.
- `grep -E "(==|!=)\s*10(?![0-9_])"` was run through Python's `re`, not the shell: the local `grep`
  is `ugrep`, which rejects the lookahead (`invalid syntax`) and would have silently produced an
  empty, meaningless result.
- The hand-edit probe counted its occurrences before editing and restored by sha256 equality, never
  `git checkout --` (hazards #3 and #4).

## Requirements

**ADVT-02 and ADVT-03 are TICKED. ADVT-01 is deliberately NOT.** This is the first movement in
`.planning/REQUIREMENTS.md` in the entire phase; the six prior plans all declined, correctly.

- **ADVT-02 (leave-one-attack-family-out, held-out family named before training) — TICKED.**
  24-03 declined and stated its own blocker precisely: *"ADVT-02's full text also depends on the
  mixture actually training against that split, which is 24-05 and 24-06. Ticking it now would claim
  a property no code yet exercises."* Both have landed. The mixture exercises the split
  (`_adversarial_pool` filters to `TRAINED_FAMILIES` and `SystemExit`s on an A2 row, watched firing;
  `_mix_adversarial` places the selected prefix and reports its per-family counts), and this plan's
  record commits the split, the containment reason and the live corpus digest at every grid point —
  **before any training has occurred at all**, which is the strongest possible reading of "before
  training".
- **ADVT-03 (attack intensity disclosed as also a token-budget axis) — TICKED.** The disclosure is
  now a committed record rather than stdout, per arm and per grid point, with both inflation figures
  kept distinct and a test enforcing the distinction. 24-06 explicitly deferred it here: *"the
  committed per-arm record is 24-07's artifact."*
- **ADVT-01 (the adapter trained against the attack suite, intensity as the swept axis) — NOT
  TICKED, and Phase 24 was never going to earn it.** The requirement's subject is *the adapter
  trained*, and no adapter exists. Phase 24 built every seam the sweep runs through and nothing it
  produces. **Phase 25 runs the sweep and is what can tick this.** Ticking on optimism here would be
  claiming a trained artifact that does not exist.

Both traceability rows are filled with the measurements, and ADVT-01's row states in full why it is
open and what closes it.

## Issues Encountered

The "expect an unnamed guard" warning did not materialise: every guard that could have bitten
(`tests/test_phase14_scoring.py`'s `PERSONA_ALLOWLIST` census, `tests/test_phase21_sc5.py`'s
twelve-member wall census, `tests/test_phase24_correction.py`'s ROADMAP tripwire,
`tests/test_phase21_aligned_bins.py`'s `repr(stats)` golden pin) stayed green with no edit, because
this plan added no `persona=` call site, no `== 10`-shaped assertion, no ROADMAP prose near the
continuation, and no source-file change at all. The five deviations above are the whole story.

## Known Stubs

None. Every declared name is implemented and consumed: `TOKEN_BUDGET_RECORD` by `main()`, `_write`
and both readers in the test module; all six document blocks populated from live measurements and
all six asserted; both refusals reachable and both watched firing; `ARMS` read by the emitter and
re-read by the coverage test. Nothing in the record is a placeholder — the one field that could look
like one, `adversarial_family_counts: {}` at the control rows, is the true value (zero adversarial
episodes are selected there) and carries its source label.

## Threat Flags

None. No new network endpoint, auth path or schema at a trust boundary. All eight registered
mitigations are in place, each backed by a measurement above:

| Threat | Status |
|---|---|
| T-24-38 ADVT-03 provenance loss | record committed with integer counts, denominators, source labels, corpus sha256 and four module sha256s; control rows re-derive under exact `==`; the hand edit was watched failing in two tests |
| T-24-39 build-time `SystemExit` on the band | four corners measured in 2.22 s before any sweep point; the margin comes from `MASK_FRACTION_MARGIN`, AST-proved never retyped |
| T-24-40 mask-fraction substitution | control corners pinned to the FLAT figures to six decimals, with the aligned and v3.0 CAL trap sets named in the test's docstring |
| T-24-41 inflation-figure conflation | 3.73 and its exact quotient stored with a note naming A3/A2 and denying 1.40; a test asserts 1.40 is never the value of an inflation field |
| T-24-42 write-once artifact | `refuse_existing_artifacts(paths=[...])` AND `refuse_if_dirty` called directly, both BEFORE the bytes land, both watched firing with no bytes landing; the publication wrapper's blindness for phase-24 paths was measured, not assumed |
| T-24-43 frozen inputs | `git diff scripts/phase18_extraction.py scripts/mitigation_gate.py` empty; the corpus digest recomputed live twice (writer and test) and matching 24-02's independent record |
| T-24-44 SC4 inflation-report obligation | discharged explicitly — `new_attack_corpus: false` plus a written discharge string |
| T-24-SC package installs | none |

## Next Phase Readiness

Phase 24's plan work is complete. For **the phase-close step**:

- The ROADMAP phase-heading checkbox (`- [ ] **Phase 24: …**`), the progress-row Status cell (still
  `In progress | -`) and STATE's `status` / `completed_phases` / `percent` are UNTOUCHED and are
  yours (precedent `5a72670`).
- `.planning/REQUIREMENTS.md` moved for the first time this phase: ADVT-02 and ADVT-03 ticked with
  traceability rows filled; **ADVT-01 is open by design** and its row says so.

For **Phase 25**:

- `results/phase24_token_budget.json` is the token-budget half of SC4's single-source-of-truth
  obligation. `phase24_record.TOKEN_BUDGET_RECORD` is the only spelling of its path.
- **Multiplicity is not comparable across capacities at the same nominal ratio** (n=8 tops out at
  1.0×; n=64 at the same point is 8.0× and is already >1 at the smallest non-zero point). SC3's
  same-sentence requirement is not a formatting rule here — it is what prevents a real
  misinterpretation.
- All twelve points clear the band with margin, so no sweep point can die at build time on
  `_prove_floor_and_band` — the failure this plan converted into a 2-second test.
- `mask_fraction` is monotonically non-increasing in `adversarial_ratio` within each arm, asserted;
  only the floor binds on this axis.
- No adapter has been trained. CTRL-01/CTRL-02 and ADVT-01 are all Phase 25's.

---
*Phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa, Plan 07*
*Completed: 2026-08-30*

## Self-Check: PASSED

All four artifact paths exist on disk plus this SUMMARY; all four task commits (`6c1327b`,
`5aed70f`, `7075951`, `8fd67eb`) are present in `git log --all`; every line number in the anchor
table was re-measured at HEAD this session rather than carried from the plan (four were stale and
are corrected there); every figure quoted above was measured this session with its computation and
denominator recorded, and the full-suite number is the executor's own run (`1645 passed, 1 skipped`,
exit 0), not the plan's or the orchestrator's. `.planning/STATE.md`'s diff was read line by line —
exactly **6 deletions**, all intended (`stopped_at`, `last_updated`, `completed_plans`, the position
line, `Last session`, `Stopped at`) — and `.planning/REQUIREMENTS.md`'s exactly **5**, all intended
(the ADVT-02 and ADVT-03 checkbox lines, and the three empty traceability rows).
