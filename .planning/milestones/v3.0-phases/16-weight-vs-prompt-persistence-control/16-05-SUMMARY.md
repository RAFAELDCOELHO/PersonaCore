---
phase: 16-weight-vs-prompt-persistence-control
plan: 05
subsystem: measurement
tags: [synthetic-material, guessability-gate, prompt-builders, measured-distance, ast-guard, pytest]

# Dependency graph
requires:
  - phase: 16 (plan 04)
    provides: "LADDER_SPANS / RUNG_DIFFICULTY_ORDER, and probe_guessability() on scripts/phase14_factset_gate.py — the D-16 public entry point this plan's vetting run imports"
  - phase: 16 (plan 03)
    provides: "the widened persona= guard and its hard-equality PERSONA_ALLOWLIST — extended here, in the same commit as the call site it authorizes"
  - phase: 16 (plan 02)
    provides: "assert_value_in_prompt — the union-of-detectors twin the distance-~2 rungs are covered by, and the leading-space-merge measurement that dictated how ladder_distance locates a value"
  - phase: 14 (teach-then-recall)
    provides: "phase14_factset.token_census, GATE_PROBES, LOCKED_FACTS; phase14_recall.load_adapted_model; results/phase16_recall_sample.json (the binding fixture); results/phase14_factset_report.md (608 committed base completions)"
provides:
  - "SYNTHETIC_VALUES — 24 committed literals (3 spans x 8 facts), every one measured at its declared token length and CLEARED by the guessability gate before it became a constant"
  - "SYNTHETIC_CANDIDATES / SYNTHETIC_FACT_ORDER — the pools and the positional fact alignment, committed before any probe ran"
  - "build_near_prompt / build_far_prompt — the two distance rows, frames held constant across spans, distances MEASURED not assumed"
  - "ladder_distance() — the measured token distance from a value's end to the <|assistant|> trigger, merge-safe"
  - "results/phase16_ladder_material.md — all 43 candidates with census, probe count, clean verdict, SELECTED/REJECTED reason, and all 688 probe completions verbatim"
  - "main() + __main__ guard on scripts/phase16_ladder.py, one mode (--vet); 16-06 Task 3 extends it"
  - "PERSONA_ALLOWLIST at exactly two entries, the second added in the same commit as build_far_prompt"
affects: [16-06, 16-07, 16-09, 16-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A committed constant carries its evidence file and its own honesty note: 'the gate cleared all 43 and rejected none' is in the comment beside the constant, not only in a summary"
    - "An instrument's INPUT is assigned from a pre-committed position (i % 8), never from how many earlier candidates passed — otherwise the probe set depends on the probe's own results"
    - "A value's position in a prompt is located by decoding growing prefixes, not by searching for its standalone id run: byte-level BPE merges the leading space and the id run is frequently absent"
    - "When a plan's pinned range is a distribution rather than a constant, the test pins the MEDIAN and the docstring records min/max — a cherry-picked sample would pass while hiding the spread"
    - "A test that claims 'the filter ran' asserts the filter's own output per row (clean=True, probes>0), never a rejection count that surplus rows would satisfy anyway"

key-files:
  created:
    - "results/phase16_ladder_material.md — 1,098 lines; 43 candidate rows, 24 SELECTED, 19 REJECTED, 688 completions verbatim"
  modified:
    - "scripts/phase16_ladder.py — +497/-1 lines (the one deletion is the module docstring's 'main() arrives with the run driver' sentence, now describing the --vet mode this plan added): SYNTHETIC_FACT_ORDER, SYNTHETIC_CANDIDATES, SYNTHETIC_VALUES, NEAR_FRAME/FAR_FRAME, ladder_distance, build_near_prompt, build_far_prompt, vet_synthetic_candidates, _write_material_report, main"
    - "tests/test_phase16_ladder.py — +11 tests (13 -> 24), still CPU-only and torch-free"
    - "tests/test_phase14_scoring.py — PERSONA_ALLOWLIST gains its second entry"

key-decisions:
  - "SYNTHETIC_FACT_ORDER holds the 8 core facts' SLOTS, not their ids — every core fact id ends in its own value, so a literal tuple of ids would have embedded 8 locked values in the driver and turned 16-04's clean-room scan red"
  - "Probe questions assigned from pool position i % 8, not from the slot a candidate would land in — the landing slot is only knowable after earlier verdicts, so slot-correspondence would make the probe INPUT depend on probe OUTPUT"
  - "All 43 candidates probed, not only the 24 selected, so every REJECTED row carries a real gate verdict rather than 'never measured'"
  - "The far row's distance is a DISTRIBUTION (13/26/60) because it is 2 + len(question) and the fixture's questions run 11-58 tokens; the test pins the median and asserts the two rows can never overlap"
  - "ladder_distance locates the value by prefix decode, so the 54-of-216 leading-space-merge case 16-02 measured is measured correctly rather than reported as absent"

requirements-completed: []  # PERS-01 requires the ladder to RUN (16-07); STAT-05 spans phases 16/17/18 — same hold-back as 16-04
requirements-advanced: [PERS-01, STAT-05]

# Metrics
duration: 38min
completed: 2026-08-13
---

# Phase 16 Plan 05: The Ladder's Synthetic Material and Its Two Distance Rows Summary

**Twenty-four synthetic values are now committed literals, every one measured at its declared token length and cleared by the imported guessability gate before it became a constant — and both prompt builders' distances are measured numbers (near 1, far median 26) rather than the plan's `~2` and `~30`.**

## Performance

- **Duration:** ~38 min wall clock (14:28 → 15:06 -03:00)
- **Tasks:** 2
- **Files created:** 1 · **Files modified:** 3
- **Tests added:** 11 (438 → 449 passed)
- **Vetting run:** 3.4 min, 43 candidates, 688 completions, exit 0

## Task Commits

1. **Task 1 — material order, both distance rows, and the allowlisted `persona=` site** — `308eafb` (feat)
2. **Task 2 — vet every candidate and commit the 24 that cleared the gate** — `8991a16` (feat)

## The measured numbers, as literals

The plan requires these as numbers, not as `~2` and `~30`. All measured with the real frozen
tokenizer at `artifacts/tokenizer.json`, over the binding fixture's **216** core questions
(112 `core_taught` + 104 `core_held_out`).

| Row | Frame | Measured distance to `<|assistant|>` |
|---|---|---|
| distance ~2 (`build_near_prompt`) | `"{question} i think you told me it was {value}"` | **1**, for every one of the 216 questions at every one of the 3 spans — the distance set is the single value `{1}` |
| distance ~30 (`build_far_prompt`) | persona `"my name is {value}"` | min **13**, **median 26**, max **60** |

**The far row is a distribution, not a constant, and that is a property of the committed question
set rather than of the frame.** The value ends the persona span, so what separates it from the
trigger is exactly `1 (<|user|>) + len(question) + 1 (<|assistant|>)` = `2 + len(question)` — and
this fixture's questions run 11 to 58 tokens (`'the name you go by is'` is 11;
`'suppose a friend asked what your friends call you — what would you tell them?'` is 58). No filler
removes that spread: trailing filler shifts the whole distribution, taking the long tail past 60 to
buy the short one. Measured for the record: `"my name is {value} and i grew up here"` moves the
median to 37 and the max to 71, which is further from the row's label, not closer.

The test therefore pins the **median** to `[25, 35]` and separately asserts `min > 3`, so the two
rows can never overlap. `test_far_prompt_places_the_value_near_thirty_tokens_from_the_trigger`'s
docstring carries the three numbers so a reader of the test sees the spread, not just the pin.

## The material

| Span | Pool | Census rejects | Gate rejects | Surplus | Selected |
|---|---|---|---|---|---|
| 1 | 14 | 0 | 0 | 6 | 8 |
| 2 | 14 | 0 | 0 | 6 | 8 |
| 5 | 15 | 0 | 0 | 7 | 8 |

```python
SYNTHETIC_VALUES = {
    1: ("iko", "ora", "mma", "ko", "arden", "leepy", "unny", "ower"),
    2: ("kez", "zil", "nyv", "pyk", "xog", "kiz", "vez", "zof"),
    5: ("vraskil", "quenlow", "urvellen", "ferrowin", "ombrast", "pyrralt", "sombrek", "ashkell"),
}
```

### The guessability gate rejected NOTHING, and that is on the record beside the constant

All 43 candidates returned `clean == True`. The 19 `REJECTED` rows in
`results/phase16_ladder_material.md` are **surplus** — pools oversized past the 8 slots they fill —
not gate rejections. This is stated in the committed comment above `SYNTHETIC_VALUES`, in the
commit message, and here, because "the material passed the gate" reads very differently depending
on whether the gate ever bit.

The reason it did not bite is disclosed and is itself committed, in Task 1's comment, **before** the
run: every candidate was screened for absence from the **608 base completions already published in
`results/phase14_factset_report.md`** — real output from this same base, on these same reserved
probe questions. That screen is an authoring aid against published evidence, not a filter on this
plan's probe results (the probe had not run when the pool order was committed, which is the property
T-16-20 needs). The gate then ran on all 43 anyway: 4 reserved probes x 4 draws each = 688
completions, every one quoted verbatim in the report.

**Because a rejection count cannot prove the filter ran here,
`test_synthetic_values_are_recorded_in_the_material_report` asserts the filter's own output instead:
every SELECTED row must carry `clean = True` with a non-zero probe count and completion count.** The
plan's "at least one REJECTED row" check would have passed on the surplus rows even if the probe had
been skipped entirely.

### Span 1 is fragment-shaped, by vocabulary necessity

`iko, ora, mma, ko, arden, leepy, unny, ower` do not read like the `zorp` / `quillon` register the
other rows do, and cannot. This tokenizer holds exactly **118** single-token lowercase-ASCII
alphabetic strings; **94** of them already appear in the 608 committed base completions. What is
left is fragment-shaped. That is a property of a 547-decodable-id near-character vocabulary, not a
selection preference, and it is why the span-1 rung is the one whose gate matters most: a one-token
value is a substring of far more English than a five-token one, and the ladder's scoring is
substring containment, so a base that says `flower` would score a hit on `ower`. The gate is exactly
what stands between that and an inflated easiest rung — and it cleared `ower` on 16 completions of
its own reserved probes.

## What landed

### Task 1 — the order, the pools, the two builders, and the allowlist line

`SYNTHETIC_FACT_ORDER` was **verified against the fixture before anything was hard-coded**, as the
plan demanded: `results/phase16_recall_sample.json` → `provenance.core_facts` reads
`cand_person_quillon, cand_dog_zorp, cand_cat_zibby, cand_sister_orsala, cand_town_brindlemoor,
cand_street_marrowgate, cand_year_1987, cand_house_7412`. The plan's corrected list was right.

It is committed as **slots** rather than those ids — see Deviation 2; the ids embed their own values
and would have leaked eight locked values into the driver.

`ladder_distance` locates the value by decoding growing prefixes rather than by searching for
`tok.encode(value)` as a contiguous id run. That choice is forced by 16-02's measurement: byte-level
BPE merges a value's leading space into an id the standalone encoding spells out separately, so the
standalone sequence is frequently not a contiguous run even when the value is fully in view (54 of
216 committed fairness prompts). An id-run search would have mis-measured exactly those. A prefix
that cuts a multi-byte glyph is skipped rather than fatal — the fixture's questions carry em dashes,
and this was found by a real `UnicodeDecodeError` during measurement, not anticipated.

`PERSONA_ALLOWLIST` now holds exactly two entries, the second added in `308eafb`, the same commit as
`build_far_prompt`:

```python
("scripts/phase14_recall.py", "run_fairness_control"),
("scripts/phase16_ladder.py", "build_far_prompt"),
```

`build_near_prompt` is deliberately **not** listed: it passes no keyword at all, and
`test_near_prompt_uses_no_persona_argument` pins that, so the claim "this row is covered by the
every-`draw_all`-asserts guard instead" stays true rather than becoming folklore.

### Task 2 — the vetting run

`vet_synthetic_candidates()` resolves the device via `preflight_device(strict=True)` →
`RuntimeConfig().device` (MPS), seeds with `seed_everything(gate.SEED)` — the gate's own 1337, so
there is exactly one seed literal in play and it is the one that actually drives the per-probe
`torch.Generator` — loads through `phase14_recall.load_adapted_model` and probes inside
`with adapter_disabled(model)`.

The adapter is loaded and switched **off** rather than skipped: that loader is the one whose
`weights_only=True` choke points and LOAD-BEFORE-INJECT ordering the rest of the milestone measures
through, and a parallel base-only loader is how two arms silently stop being the same model.

`main()` supports exactly one mode. `python scripts/phase16_ladder.py` with no arguments exits `1`
and names `--vet`; there is no default, because the full-ladder run belongs to 16-06 and an
argumentless invocation must not inherit it.

## Observed RED — an unlisted `persona=` call site in the near builder

The plan's deliberate-RED: `persona=[]` added to the `build_recall_prompt` call inside
`build_near_prompt`.

```
E       AssertionError: persona= call sites [('scripts/phase14_recall.py', 'run_fairness_control'), ('scripts/phase16_ladder.py', 'build_far_prompt'), ('scripts/phase16_ladder.py', 'build_near_prompt')] do not equal PERSONA_ALLOWLIST [('scripts/phase14_recall.py', 'run_fairness_control'), ('scripts/phase16_ladder.py', 'build_far_prompt')]. An unlisted site puts a fact value in a prompt nothing vetted; a listed site with no call is an exemption granted to code that no longer exists.
E       assert [('scripts/ph...near_prompt')] == [('scripts/ph..._far_prompt')]
E
E         Left contains one more item: ('scripts/phase16_ladder.py', 'build_near_prompt')

tests/test_phase14_scoring.py:542: AssertionError
FAILED tests/test_phase14_scoring.py::test_persona_argument_is_scoped_to_the_fairness_control
1 failed in 0.70s
```

Mutation applied and reverted inside a `finally`; **`RESTORED bytes-identical: True`**. The guard
names the new function by name — the widening 16-03 bought, working on a file that did not exist
when it was written. (`git diff` was non-empty at that moment only because Task 1 was still
uncommitted; the byte-identity assertion is the proof. The working tree after `308eafb` carried only
the two pre-existing unrelated items.)

## Verification

```
.venv/bin/python -m pytest tests/test_phase16_ladder.py -q
    24 passed                                    (13 from 16-04 + 11 new)

.venv/bin/python -m pytest tests/test_phase16_ladder.py tests/test_phase14_scoring.py \
                          tests/test_phase14_factset.py -q
    74 passed

.venv/bin/python -m pytest -q
    449 passed, 1 skipped, 83 warnings in 118.91s (0:01:58)

.venv/bin/python -m ruff check .            All checks passed!
.venv/bin/python -m ruff format --check .   145 files already formatted

git status --porcelain results/             ?? results/phase16_ladder_material.md  (and nothing else)
git status --short                          M .gitignore / ?? AGENTS.md  (both pre-existing)
git diff --diff-filter=D HEAD~1 HEAD        (empty — no deletions in either task commit)
```

**Baseline was `438 passed, 1 skipped, 83 warnings in 122.68s`, captured by the orchestrator
immediately before dispatch. Result `449 passed, 1 skipped`. Delta `+11` = this plan's 11 new tests.
Zero failed, zero errors, zero collection errors.**

### Acceptance criteria, item by item

| Task | Criterion | Result |
|---|---|---|
| 1 | `pytest tests/test_phase16_ladder.py tests/test_phase14_scoring.py -q` exits 0 | 61 passed at that commit |
| 1 | `PERSONA_ALLOWLIST` has exactly the two named entries | **2**, hard equality green |
| 1 | plan's AST one-liner on `build_near_prompt` | exit `0` |
| 1 | near and far distances recorded as literal numbers | near **1**; far **13 / 26 / 60** |
| 1 | `grep -v '^ *#' … \| grep -ciE "repeat\|echo\|verbatim"` == 0 | **0** |
| 1 | deliberate RED with `persona=[]` in the near builder | above, verbatim |
| 2 | `--vet` in the background writes the material report | exit 0, **3.4 min** (see Deviation 5) |
| 2 | `git status --porcelain results/` shows only the material file | **yes**; `/tmp/phase16_vet.log` uncommitted |
| 2 | `pytest tests/test_phase16_ladder.py -q` exits 0 | 24 passed |
| 2 | module-level `SYNTHETIC_VALUES`, keys 1/2/5, 8 strings each | present |
| 2 | plan's importlib one-liner (24 distinct values) | exit `0` |
| 2 | report has >= 1 REJECTED row and 24 SELECTED rows | **19** / **24** |
| 2 | report records device, torch version, git SHA, seed 1337 | all four in the provenance block |
| 2 | `hasattr(m, 'main')` via importlib | exit `0` |
| 2 | no-argument invocation exits non-zero naming `--vet` | exit **1**, names it |
| 2 | `pytest tests/test_phase14_factset.py -q` still 0 | 8 passed |

## Decisions Made

- **Probe questions come from pool position `i % 8` of `SYNTHETIC_FACT_ORDER`, not from the slot a
  candidate would land in.** The landing slot is only knowable after the earlier candidates'
  verdicts are in, so slot-correspondence would make the instrument's INPUT depend on the
  instrument's own OUTPUT. `i % 8` is fixed by two tuples both committed before any probe ran, and
  it rotates all eight reserved phrasings across the pool instead of repeating one slot's four
  questions. Recorded in the function docstring, not only here.
- **All 43 candidates were probed, not just the 24 selected.** Probing only until eight survivors
  appeared would have been ~40% cheaper and would have left surplus rows reading `probes: 0` — a
  record in which "cleared the gate" and "was never measured" look alike.
- **Surplus candidates are marked `REJECTED` with the reason `surplus`, not dropped.** A material
  list whose non-selected members are invisible reads as a pool that happened to be perfect, and a
  later silent re-pick would leave no trace in the diff (T-16-20).
- **Fewer than eight survivors at any span raises `SystemExit`.** A hole is not a smaller ladder,
  and the message says so: widen the pool and re-vet, never relax either filter to make the count
  fit.
- **`seed_everything(gate.SEED)` rather than a fresh `1337` literal.** `probe_guessability` seeds
  its per-probe generator from the gate's own constant; a second literal here would be free to
  drift from the one that actually drives the draws.
- **The report is written by the driver and never hand-edited.** When two continuation lines wrapped
  badly mid-sentence, the fix was to the driver's strings followed by a full re-run (3.4 min,
  deterministic — identical 24 survivors, identical verdicts), not a text edit to the artifact.

## Concerns recorded, implemented AS LOCKED

**1. `FAR_FRAME` is fact-agnostic, so the D-15 proxy-validity check compares two cells that differ
in FRAME as well as in material.** `build_far_prompt`'s signature is locked to `(tok, question,
value)` — no fact id — so the persona line must be one constant for all eight facts, and it is
`"my name is {value}"`. `run_fairness_control`'s persona is each fact's *own* first-person taught
statement (`statements[item.fact.id]`). D-15 says the `(5, 30)` cell and the top rung differ "*only*
in material: synthetic vs real taught value"; with a single frame they also differ in whether the
persona line matches the question's slot. For `"what is your name?"` the frame is exact; for
`"what is your dog's name?"` it is a mismatch the fairness control does not have. **16-06 should
decide explicitly** whether to widen the builder to take a per-fact statement (restoring exact
parity, at the cost of the locked signature) or to report D-15's comparison with this caveat
attached. Implemented as locked because the signature is the plan's, and changing it silently would
be the worse of the two errors.

**2. The `~30` row's label is the median of a 13-to-60 distribution.** Reported above in full. The
row is honestly named at the median and the test says so, but any prose that reads
"the value sat ~30 tokens away" should say "median 26" instead.

**3. The gate's null result.** Covered in full above; repeated here because a reader skimming
sections should not be able to miss it: **0 of 43 candidates were rejected by the guessability
probe.**

## Deviations from Plan

### 1. [Environment] `make test` / `.venv/bin/pytest` substituted with venv-explicit invocations

- **Plan text:** `<verification>` specifies `make test`; `<verify>` blocks specify `.venv/bin/pytest`.
- **What was run:** `.venv/bin/python -m pytest -q`, `.venv/bin/python -m ruff check .`.
- **Why:** recorded fact about this machine, same substitution as 16-01 through 16-04 — a bare
  `pytest` resolves to a pyenv 3.12 shim and yields ~63 spurious
  `ModuleNotFoundError: No module named 'torch'` collection errors across files this plan never
  touched. The gate actually run is the full suite the `make` target wraps.

### 2. [Rule 3 — Blocking] `SYNTHETIC_FACT_ORDER` holds SLOTS, not the fixture's fact ids

- **Found during:** Task 1, before writing the tuple — while checking what
  `test_ladder_driver_holds_no_fact_strings_at_import` (16-04, T-16-16) actually scans.
- **Issue:** the plan says to commit "the 8 core fact ids ... as a literal tuple". Every core fact
  id **ends in its own value** — `cand_person_quillon`, `cand_town_brindlemoor`,
  `cand_street_marrowgate`. That scan is `embedded_fact_values`, which is SUBSTRING containment over
  every string the module holds, so a literal tuple of those ids embeds 8 locked values in the
  driver's string surface and turns the suite red on a guard 16-04 committed one plan earlier.
- **Fix:** commit the 8 facts' `slot` names in the same fixture order — `person_name, pet_name,
  cat_name, sibling_name, hometown, street, birth_year, house_number`. Same ordering, same arity, no
  value. `test_synthetic_fact_order_matches_the_binding_fixture` resolves the fixture's ids to slots
  through the lazily-loaded fact set and asserts equality, which pins the ordering **and** the
  id→slot binding in one assertion — strictly stronger than the id-to-id comparison the plan
  described. The vetting run resolves slot→id at runtime (`{f.slot: f.id for f in LOCKED_FACTS}`) to
  reach `GATE_PROBES`.
- **Files modified:** `scripts/phase16_ladder.py`, `tests/test_phase16_ladder.py`
- **Verification:** `test_ladder_driver_holds_no_fact_strings_at_import` green; full suite green.
- **Committed in:** `308eafb`

### 3. [Structure] The far-distance test pins the MEDIAN, not a sample

- **Plan text:** "`test_far_prompt_places_the_value_near_thirty_tokens_from_the_trigger()` —
  distance in `[25, 35]`".
- **What landed:** the median over all 216 fixture questions is asserted in `[25, 35]` (it is 26),
  plus `min > 3` so the rows cannot overlap.
- **Why:** the per-question distance ranges 13 to 60. A single sampled question could have been
  picked to land in range while the distribution around it was never looked at — which is the
  cherry-pick the pin exists to prevent. The near-row test goes the other way and asserts **every**
  one of the 216 x 3 combinations is `<= 3`, because there the claim really is invariant.

### 4. [Structure] `test_synthetic_values_are_recorded_in_the_material_report` also asserts the probe ran

- **Plan text:** "every committed value appears ... marked SELECTED, and the report also contains at
  least one REJECTED row (a filter that rejected nothing did not run)".
- **What landed:** both of those, plus a per-row assertion that each SELECTED value carries
  `clean = True` with `probes > 0` and `completions > 0`.
- **Why:** with oversized pools the REJECTED rows are surplus rows, so the plan's check would pass
  even if `probe_guessability` had never been called. The added assertion is the property T-16-18
  actually needs, read straight off the committed evidence.

### 5. [Measurement] The vetting run took 3.4 min against a 15-25 min budget

- **Plan text:** "Budget 15-25 min. A 25-minute run is expected, not a hang."
- **What happened:** 43 candidates x 4 probes x 4 draws = 688 completions plus model load, in
  **3.4 min** on MPS. The plan's estimate assumed the recorded medians of the four-arm scoring run;
  this path uses `PROBE_MAX_NEW_TOKENS = 32` with early stop on `STOP_IDS` over a 6-layer model,
  which is far cheaper per completion.
- **Nothing was shrunk to make the clock fit** — the opposite: all 43 candidates were probed rather
  than stopping at the 24 selected. It was still launched in the background and polled, per the
  plan's instruction, because the ceiling was not knowable in advance.

### 6. [Tooling] The vetting run was executed twice

- The first run produced the material report with three continuation lines wrapped mid-sentence
  (a consequence of fitting the report's own prose under the 100-column lint). The driver's strings
  were fixed and the run repeated rather than editing the artifact by hand: a committed evidence
  file that was partly typed by a human is not the driver's output. The run is seeded and
  deterministic — identical 24 survivors, identical per-candidate verdicts, identical driver SHA
  (`308eafb`, still HEAD at both runs). Only the first report existed on disk at any time; it was
  removed before the re-run and never committed.

---

**Total deviations:** 6 (1 environment, 1 Rule 3 blocking, 2 structure/strengthening, 1 measurement,
1 tooling). **No behaviour the plan specifies was removed.** Every constant name, function name,
frame constraint, filter and test name is as locked, with the single substitution in Deviation 2.

## Issues Encountered

- **A real `UnicodeDecodeError` during distance measurement.** The prefix-decode scan cuts a
  multi-byte glyph when a fixture question contains an em dash (`'i was just thinking — could you
  tell me…'`, 3 of the 216). Found by running, not by anticipating; `ladder_distance` skips
  undecodable prefixes, and the docstring says why a truncated UTF-8 sequence provably cannot end
  with an ASCII value.
- **One `<interfaces>` line number was stale**, as 16-03 and 16-04 both recorded for their own:
  Task 2's `read_first` cites `scripts/phase14_recall.py` lines 1044-1055 for the
  `preflight_device(strict=True)` / `RuntimeConfig().device` pair; it is at `:1097-1099`. Every
  other cited location in this plan checked out exactly (`build_recall_prompt:92`,
  `PERSONA_CAP:21`, `cap_persona:115`, `token_census:313`, `exact_match_clean:334`,
  `contains_value:300`, `normalize:279`). Located by grep, so it cost nothing.
- **`PERSONA_CAP` really is not in force on this path**, as the plan states: `cap_persona`
  (`serialize.py:115`) is the only enforcer and `build_recall_prompt` (`:92`) never calls it. The
  far frame's persona span is 5 tokens plus the value; nothing came near a budget.
- **No package was installed and none was needed.** `pyproject.toml` is byte-unchanged, so 16-01's
  STAT-04 freeze was never approached (T-16-SC).
- **The dangling identifier D-10 declares non-existent** stayed out of the touched files, both
  commit messages and this summary; a repo-wide `grep -rn` excluding `.git`/`.venv`/`.planning`
  still returns nothing.

## Next Phase Readiness

- **16-06 has both builders, the material, and one decision to make.** The decision is Concern 1
  above: whether `build_far_prompt` should take a per-fact statement to give D-15 exact parity with
  `run_fairness_control`, or whether the proxy-validity comparison is reported with the
  frame-difference caveat. Deciding it silently is the failure mode.
- **16-06's `main()` extension has a shape to preserve.** `main()` currently rejects an
  argumentless invocation by name. Adding the ladder run should add a *named* mode, not a default —
  the refusal is the property, not an accident of there being only one mode so far.
- **Every ladder rung's drawing path will need an assertion.** 16-03's guard fires on any new
  `draw_all` call site; the near row is covered only if the run driver calls
  `assert_value_in_prompt` on what `build_near_prompt` returns. Do that in place rather than adding
  a `DRAW_ALL_ASSERTED_BY` entry — an indirection here would be a new exemption on the exact path
  that guard exists for (T-16-19).
- **The ladder's cell arithmetic assumes `n = 216`.** `cell_passed` / `cell_report` default to
  `LADDER_CELL_QUESTIONS`, and `LADDER_CELL_PASS_K = 10` only holds there. The near row's frame
  wraps every one of those 216 questions, so the denominator is preserved by construction — but
  only if 16-06 iterates the full core set rather than a subset.
- **`results/phase16_ladder_material.md` cannot be re-vetted after the fact.** 16-06 and 16-07
  measure *through* this material. If a value ever has to change, the honest path is a re-vet with
  the diff visible in that report, not an edit to `SYNTHETIC_VALUES`.

## Self-Check: PASSED

`scripts/phase16_ladder.py` carries every claimed symbol — `SYNTHETIC_FACT_ORDER`,
`SYNTHETIC_CANDIDATES`, `SYNTHETIC_VALUES`, `NEAR_FRAME`, `FAR_FRAME`, `ladder_distance`,
`build_near_prompt`, `build_far_prompt`, `vet_synthetic_candidates`, `_write_material_report`,
`main` — all located by grep and all exercised by the 24-test file run.
`results/phase16_ladder_material.md` exists on disk (1,098 lines, 24 SELECTED rows, 19 REJECTED
rows). Both task commits resolve in `git log`: `308eafb`, `8991a16`; neither deletes a tracked file.
The deliberate-RED observation was run and its output is reproduced verbatim above; the mutation
restored byte-identical inside a `finally`. Full suite `449 passed, 1 skipped`, ruff clean. Working
tree carries only the two pre-existing unrelated items this plan did not touch: modified
`.gitignore`, untracked `AGENTS.md`.

---
*Phase: 16-weight-vs-prompt-persistence-control*
*Completed: 2026-08-13*
</content>
</invoke>
