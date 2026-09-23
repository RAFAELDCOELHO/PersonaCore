---
phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
plan: 07
subsystem: filler-corpus
tags: [unit-06, d-12, d-13, d-15, d-16, d-17, d-18, wave-3, t-21-04, t-21-30, t-21-31, t-21-32, t-21-33, t-21-34, t-21-57, t-21-58, t-21-08]
requires:
  - "21-05 — scripts/phase14_factset.py::render_family(..., forms=None), the additive slot-grammar seam the filler corpus renders through"
  - "21-05 — tests/test_phase21_filler.py, EXTENDED here (7 -> 13 tests), never replaced"
provides:
  - "scripts/phase21_filler.py::FILLER_SLOT_FORMS — 8 filler-only slots, disjoint from the published 11"
  - "scripts/phase21_filler.py::FILLER_FACTS — the 56 unscored filler facts, an ORDERED tuple literal"
  - "scripts/phase21_filler.py::refuse_collisions() — three import-time refusals over normalized containment, both directions"
  - "scripts/phase21_filler.py::verify_round_trips(tok) — fs.token_census over all 56, zero generations"
  - "scripts/phase21_filler.py::GUESSABILITY_WAIVER — D-17's waiver as machine-checkable DATA"
  - "scripts/phase21_filler.py::render_filler_episodes() — 1,232 rows, process-stable, identical in FORM to a scored fact"
affects:
  - "21-10 / 21-11 — the n=64 arm's teaching bin draws LOCKED_FACTS + FILLER_FACTS from here"
  - "GATE-10 — the n=8-vs-n=64 capacity comparison this corpus exists to make unconfounded"
tech-stack:
  added: []
  patterns:
    - "A collision refusal is written over the PROPERTY (normalized containment, both directions), never over the NAME (string equality) — and is proven so by a value equality would ADMIT"
    - "An unordered container feeding a byte-level guarantee is sorted at the iteration site, and the guarantee is checked ACROSS PROCESSES because one process can never observe the defect"
    - "A child interpreter used to test hash-order stability has PYTHONHASHSEED explicitly POPPED, so an inherited fixed seed cannot certify a sorted() that is not there"
    - "A count that is not pre-registered is asserted as EQUALITY WITH A MEASURED SIBLING, never against a literal, so a grammar cannot be reshaped to hit a number"
    - "A waiver is a module CONSTANT carrying its measured price, so a test can assert it is a decision rather than a silence"
    - "Deliberate-RED mutations are applied strictly AFTER the GREEN commit and verified restored by a sha256 recorded BEFORE the mutation"
key-files:
  created:
    - "scripts/phase21_filler.py"
    - ".planning/phases/21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus/21-07-SUMMARY.md"
  modified:
    - "tests/test_phase21_filler.py"
decisions:
  - "PUBLISHED_POOL_VALUES is COUNTED AT RUNTIME and measured 38, not 21-CONTEXT's 28. The 28 is the NON-LOCKED subtotal (12 rejected + 10 calibration + 6 register arm); all_pools()' union is a superset because LOCKED_FACTS are drawn from CANDIDATE_POOL. The command that produced 38 is recorded beside the constant"
  - "The tokenizer path is derived as _ROOT / 'artifacts' / 'tokenizer.json' — the derivation teach_persona.py, phase14_factset_gate.py and eight other modules all spell — rather than the plan's bare relative literal pathlib.Path('artifacts/tokenizer.json'), which resolves wrongly under any pytest invocation from another directory"
  - "tier='filler' is a THIRD tier name, deliberately distinct from 'core' and 'soft', so a tier-based filter anywhere in the repo cannot sweep filler into a scored set by matching a name it already knows"
  - "The eight filler subjects (boat, bicycle, houseplant, old teacher, river, old school, neighbour, trail) were chosen for zero SEMANTIC overlap with the scored eight, not merely for disjoint slot KEYS: no filler phrasing names a town, street, year, house number, colour or food, so filler cannot compete with a scored slot even at the level of surface wording"
metrics:
  duration: "~45 min"
  tasks_completed: 3
---

# Phase 21 Plan 07: The 56 Unscored Filler Facts Summary

The n=64 capacity arm's corpus, minted so that both halves of the central claim are measurements
rather than assertions: **8 scored + 56 filler = 64 with the filler provably unreachable by any
scoring path, and every published instrument byte-unchanged.**

---

## The `== 10` wall census — MEASURED 11 sites across 8 files

The prompt required this be censused mechanically and warned that every documented figure is
unreliable. It is. Three independent grep patterns were run and converge on the same set:

| Pattern | Command |
|---|---|
| A | `grep -rn "== 10\b" tests/ scripts/ src/` |
| B | `grep -rn "LOCKED_FACTS + \(fs\.\)\?SOFT_TIER_FACTS\|LOCKED_FACTS+SOFT" tests/ scripts/ src/` |
| C | `grep -rnE "(==\|!=)[[:space:]]*10([^0-9]\|$)" --include="*.py" tests scripts src` |

**Measured: 11 leak-vocabulary assertion sites, in 8 files.**

| # | Site | Expression |
|---|---|---|
| 1 | `tests/test_phase14_scoring.py:405` | `len(forbidden) == 10` |
| 2 | `tests/test_phase14_demo.py:394` | `len(values) == 10` |
| 3 | `tests/test_phase14_demo.py:568` | `len(result["values"]) == 10` |
| 4 | `tests/test_phase16_driver.py:313` | `len(forbidden) == 10` |
| 5 | `tests/test_phase16_ladder.py:443` | `len(forbidden) == 10` |
| 6 | `tests/test_phase16_ladder.py:711` | `len(forbidden) == 10` |
| 7 | `tests/test_phase18_prereg.py:127` | `len(forbidden) == 10` |
| 8 | `tests/test_phase18_corpus.py:430` | `len(values) == 10` |
| 9 | `tests/test_phase19_erasure.py:625` | `len(forbidden) == 10` |
| 10 | `tests/test_phase19_erasure.py:1689` | `taught == 10` |
| 11 | `tests/test_phase21_filler.py:155` | `len(fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS) == 10` — added by 21-05 |

Each was read in context to confirm it asserts on `LOCKED + SOFT`, not on something else.

**Excluded, with reason** — three matches are NOT wall sites: `test_phase16_ladder.py:232,233`
(`row["rate"] == 10 / LADDER_CELL_QUESTIONS`, rate arithmetic), `test_phase15_stats.py:127`
(`st.N_BOOT == 10_000`), and `test_phase21_filler.py:154` (a docstring mentioning the wall).

**Site 12 is added by this plan**: `scripts/phase21_filler.py`'s module-level
`assert len(FORBIDDEN_SCORED_VALUES) == 10` — the first wall site in *source* rather than in a test,
sited at the one module in the repo that could break the wall.

### How the documented figures compare

| Source | Claimed | Measured |
|---|---|---|
| `21-CONTEXT.md` D-18 | 4 sites | 11 |
| `21-RESEARCH.md` | 7 across 6 files | 11 across 8 |
| plan-check pass 1 | 8 across 7 files | 11 across 8 |
| plan-check pass 3 | 9 | 11 |
| `21-07-PLAN.md` success criteria | "All 8 `== 10` wall sites green" | 11 (12 after this plan) |

The plan's phrase *"the SC5 guard set, all 8 wall sites"* conflates **8 FILES** (the SC5 guard set
is 8 test files) with **8 SITES**. They are different numbers: 8 files hold 10 of the 11 sites, and
the 11th (`test_phase21_filler.py:155`) is outside the SC5 set. Both were run; both are green.

---

## Claim (a) — the 56 are genuinely UNSCORED, proven by reachability

Not asserted. Four set intersections plus a reachability census:

| Check | Result |
|---|---|
| `filler_ids & {all_pools() ids}` | `set()` |
| `filler_ids & set(fs.GATE_PROBES)` | `set()` |
| `filler_ids & set(fs._BY_ID)` | `set()` |
| `filler_values & {LOCKED + SOFT normalized}` | `set()` |
| `len(fs._BY_ID)`, `len(fs.GATE_PROBES)` before/after importing `phase21_filler`, in a FRESH interpreter | `(38, 38, 3, 38)` → `(38, 38, 3, 38)` — unchanged |

**The reachability census is the stronger half.** `grep -rln "phase21_filler" scripts/ src/ tests/`
returns exactly three files:

- `scripts/phase21_filler.py` — itself
- `tests/test_phase21_filler.py` — its own test
- `scripts/phase14_factset.py:845` — a **docstring reference to the test file**, not an import

**No scoring, evaluation, teaching or reporting module imports this file at all.** There is
therefore no path by which a filler fact can reach a score, because there is no path to the module.
Plan 21-10/21-11 will be the first consumer, and it will draw them deliberately.

`src/personacore.egg-info/SOURCES.txt` also matches the grep; it is an untracked build artifact
from the editable reinstall, not a repo file (`git ls-files src/personacore.egg-info/` is empty).

---

## Claim (b) — every published instrument byte-unchanged

| Check | Result |
|---|---|
| `git diff --stat ae5eb18 HEAD` | **2 files, 661 insertions, 0 deletions** — `scripts/phase21_filler.py` (new), `tests/test_phase21_filler.py` (extended) |
| `git diff --exit-code scripts/phase18_extraction.py scripts/mitigation_gate.py scripts/mitigation_unit.py` | `0` |
| `scripts/mitigation_unit.py` sha256 (FROZEN pin, 21-01) | `45f37e152bb4035667b804c1463431b3f12fa5096c47de32b1dc27abbe000473` — identical to 21-05's recorded value |
| `tests/fixtures/golden_render_family_v2.json` digests, both registers | reproduce — `test_render_family_byte_identity` green, so `render_family`'s default path is still byte-identical to the pre-edit v2.0 capture |
| SC5 guard set (8 files) | **334 passed, 2 skipped in 37.07s** — matches 21-05's recorded 334/2 baseline exactly |
| Wide-glob scanners (`test_lora_inject`, `test_phase19_erasure`, `test_phase17_stats`, `test_phase14_scoring`, `test_package`) | **186 passed** |
| `git ls-files 'results/phase21_*'` | **empty** (0 tracked); `git status --porcelain results/` empty |
| `.planning/STATE.md`, `.planning/ROADMAP.md` | untouched — worktree mode |

**No file outside the two listed was modified.** Zero deletions in the whole plan.

---

## The 56 filler facts, in declared order

`FILLER_FACTS` is an ordered tuple literal. Two separate interpreters emit an identical id list.

| # | id | slot | value |
|---|---|---|---|
| 1 | `filler_boat_kestrelaine` | `filler_boat_name` | kestrelaine |
| 2 | `filler_boat_plovermere` | `filler_boat_name` | plovermere |
| 3 | `filler_boat_saltwren` | `filler_boat_name` | saltwren |
| 4 | `filler_boat_driftwallow` | `filler_boat_name` | driftwallow |
| 5 | `filler_boat_tidecomber` | `filler_boat_name` | tidecomber |
| 6 | `filler_boat_brackenkeel` | `filler_boat_name` | brackenkeel |
| 7 | `filler_boat_foamharrow` | `filler_boat_name` | foamharrow |
| 8 | `filler_bike_cogsparrow` | `filler_bicycle_name` | cogsparrow |
| 9 | `filler_bike_whirlbenn` | `filler_bicycle_name` | whirlbenn |
| 10 | `filler_bike_spokehollis` | `filler_bicycle_name` | spokehollis |
| 11 | `filler_bike_ratchetvane` | `filler_bicycle_name` | ratchetvane |
| 12 | `filler_bike_pedalquist` | `filler_bicycle_name` | pedalquist |
| 13 | `filler_bike_chainferro` | `filler_bicycle_name` | chainferro |
| 14 | `filler_bike_hubwendel` | `filler_bicycle_name` | hubwendel |
| 15 | `filler_plant_fernwillow` | `filler_houseplant_name` | fernwillow |
| 16 | `filler_plant_mosswick` | `filler_houseplant_name` | mosswick |
| 17 | `filler_plant_palmadora` | `filler_houseplant_name` | palmadora |
| 18 | `filler_plant_sprigley` | `filler_houseplant_name` | sprigley |
| 19 | `filler_plant_leafquerra` | `filler_houseplant_name` | leafquerra |
| 20 | `filler_plant_budmarron` | `filler_houseplant_name` | budmarron |
| 21 | `filler_plant_vinehollow` | `filler_houseplant_name` | vinehollow |
| 22 | `filler_teacher_talvern` | `filler_teacher_name` | talvern |
| 23 | `filler_teacher_brennick` | `filler_teacher_name` | brennick |
| 24 | `filler_teacher_oswaldy` | `filler_teacher_name` | oswaldy |
| 25 | `filler_teacher_prendra` | `filler_teacher_name` | prendra |
| 26 | `filler_teacher_ficklemore` | `filler_teacher_name` | ficklemore |
| 27 | `filler_teacher_wynstable` | `filler_teacher_name` | wynstable |
| 28 | `filler_teacher_garrowine` | `filler_teacher_name` | garrowine |
| 29 | `filler_river_silverbrack` | `filler_river_name` | silverbrack |
| 30 | `filler_river_elderquay` | `filler_river_name` | elderquay |
| 31 | `filler_river_thornmere` | `filler_river_name` | thornmere |
| 32 | `filler_river_coldrunnel` | `filler_river_name` | coldrunnel |
| 33 | `filler_river_larkwater` | `filler_river_name` | larkwater |
| 34 | `filler_river_gullsend` | `filler_river_name` | gullsend |
| 35 | `filler_river_mirefoss` | `filler_river_name` | mirefoss |
| 36 | `filler_school_quarrenhall` | `filler_school_name` | quarrenhall |
| 37 | `filler_school_embermount` | `filler_school_name` | embermount |
| 38 | `filler_school_tarnbury` | `filler_school_name` | tarnbury |
| 39 | `filler_school_vellacrest` | `filler_school_name` | vellacrest |
| 40 | `filler_school_dunmorrow` | `filler_school_name` | dunmorrow |
| 41 | `filler_school_ashcombe` | `filler_school_name` | ashcombe |
| 42 | `filler_school_pellingford` | `filler_school_name` | pellingford |
| 43 | `filler_neighbour_halbrick` | `filler_neighbour_name` | halbrick |
| 44 | `filler_neighbour_corvanne` | `filler_neighbour_name` | corvanne |
| 45 | `filler_neighbour_tibbolt` | `filler_neighbour_name` | tibbolt |
| 46 | `filler_neighbour_merrowick` | `filler_neighbour_name` | merrowick |
| 47 | `filler_neighbour_ganderly` | `filler_neighbour_name` | ganderly |
| 48 | `filler_neighbour_olvenna` | `filler_neighbour_name` | olvenna |
| 49 | `filler_neighbour_prasker` | `filler_neighbour_name` | prasker |
| 50 | `filler_trail_stonewend` | `filler_trail_name` | stonewend |
| 51 | `filler_trail_briarloop` | `filler_trail_name` | briarloop |
| 52 | `filler_trail_longspur` | `filler_trail_name` | longspur |
| 53 | `filler_trail_hollowridge` | `filler_trail_name` | hollowridge |
| 54 | `filler_trail_cragmantle` | `filler_trail_name` | cragmantle |
| 55 | `filler_trail_yarrowbend` | `filler_trail_name` | yarrowbend |
| 56 | `filler_trail_thistlefall` | `filler_trail_name` | thistlefall |

56 facts, 56 distinct ids, 56 distinct values, 8 slots x 7, every `tier == "filler"`.

---

## Measurements, published rather than smoothed

### `len(PUBLISHED_POOL_VALUES)` = **38**, not 28

```bash
.venv/bin/python -c "import sys;sys.path.insert(0,'scripts');import phase14_factset as fs;\
print(len({fs.normalize_for_match(f.value) for _n,p in fs.all_pools() for f in p}))"
# -> 38
```

21-CONTEXT's 28 is the **non-locked subtotal** (12 `GATE_REJECTED_CANDIDATES` + 10
`CALIBRATION_POOL` + 6 `REGISTER_ARM_POOL`). `all_pools()`' union is a **superset** because
`LOCKED_FACTS` are themselves drawn from `CANDIDATE_POOL`. The plan anticipated this and forbade
hardcoding 28; the superset is the safer refusal and is what shipped. The command is recorded
beside the constant in source.

### Row counts — the D-15 claim, as a comparison

| Quantity | Observed | D-15's estimate | Verdict |
|---|---|---|---|
| Rows per SCORED fact over `sorted(TAUGHT_FAMILY_IDS)` | **22** | 22 | exact |
| Rows per FILLER fact (all 56, no spread) | **22** | 22 | exact |
| `len(render_filler_episodes())` | **1,232** | 1,232 (estimate) | exact |
| n=64 total taught rows (8 x 22 + 1,232) | **1,408** | — | new |
| `PARAPHRASES_PER_FACT_TARGET` | `(20, 50)` | — | 22 inside band |

The estimate landed exactly. **It was still not the assertion.** The test asserts
`observed == {n_scored}` — equality with the measured scored count — and band membership; it never
compares to the literal 22. The grammar was not reshaped to hit a number, and the ~264-window /
`grad_accum_steps = 64` figures remain labelled ESTIMATES in source, pending 21-10/21-11.

### Cross-process determinism

Both processes, and both encodings, identical:

| Artifact | sha256 |
|---|---|
| `render_filler_episodes()` serialized | `9eace7efbd41cfe9f6298ee4c1f2790e9b294a973e1b19251938bc16cbcd066f` |
| `tokens.bin` via `teach_persona.build_bins` | `1beb5ad1c1324b6413f0625ea40c502b2f7b2b068f839fa149db88bf0fe902ab` |
| `mask.bin` | `7d59f47752a4fa18129a63152713ddb456315d62521153206887128d88250de5` |

`verify_round_trips` passes on the frozen `artifacts/tokenizer.json` for all 56 values.

---

## The three deliberate-REDs, watched

`scripts/phase21_filler.py` sha256 recorded **before** any mutation:
`bec49415029005cedba080f8dbb3402b0a82ddf11a87280069b0562dbf68d755`.
Per the ordering defect that destroyed 21-01's and 21-04's work, **every mutation was applied only
after the corresponding GREEN commit existed**, so `git checkout` could not delete uncommitted work.

### RED 1 — `marrowgate` (equality)

```
[phase21_filler] REFUSED against FORBIDDEN_SCORED_VALUES (the 10-value leak vocabulary,
LOCKED + SOFT): filler 'filler_boat_kestrelaine' value 'marrowgate' is identical to scored value
'marrowgate'. ...
--- exit code: 1 ---
```

### RED 2 — `marrowgatex` (containment, T-21-30)

```
[phase21_filler] REFUSED against FORBIDDEN_SCORED_VALUES (the 10-value leak vocabulary,
LOCKED + SOFT): filler 'filler_boat_kestrelaine' value 'marrowgatex' contains scored value
'marrowgate'. ...
--- exit code: 1 ---
equality would ADMIT it: False
```

This is the direct demonstration that the refusal is over the **property**, not the name: a value
`'marrowgatex' == 'marrowgate'` evaluates **False** for, and would sail past, an equality-based
guard. The message also reports the **direction** ("contains" vs "is identical to").

### RED 3 — `sorted(family_ids)` removed (T-21-57)

**The plan's framing of this defect is FALSIFIED.** It asked to *"repeat until two processes
disagree — recording how many attempts it took is itself the evidence that this defect is
intermittent."* It took **2 attempts** (the first two disagreed), and the defect is **not
intermittent at all**:

```
attempt  1: 73badd32cd1b6d79  ['F1','F4','F2','F6','F5']
attempt  2: 0e3b38f6beee1b23  ['F6','F4','F1','F5','F2']
attempt  3: 7641884f38b85d48  ['F5','F1','F2','F4','F6']
attempt  4: b2b0ebcdd2e8e740  ['F1','F6','F5','F4','F2']
attempt  5: a27904353bf34885  ['F1','F2','F6','F4','F5']
attempt  6: a70a76269f75a71b  ['F2','F4','F5','F6','F1']
attempt  7: a510b6d80bb2ee0c  ['F5','F1','F4','F2','F6']
attempt  8: f11464f91f73f65c  ['F4','F5','F6','F2','F1']
attempt  9: 7126844d79bd495d  ['F1','F5','F4','F2','F6']
attempt 10: 643f810bd6812e2e  ['F4','F5','F2','F6','F1']
attempt 11: b7cec18326daf37e  ['F6','F2','F1','F4','F5']
attempt 12: 59ac35533b31ce8b  ['F5','F2','F1','F6','F4']
```

**12 of 12 interpreters produced 12 distinct digests and 12 distinct frozenset orders.** Python
randomizes `str` hashing per process, so a 5-element frozenset of strings lands in a fresh order on
essentially every run. The correct characterisation is not *intermittent across processes* but
**invisible within one process and near-certain across two** — which is exactly why a single-process
test could never catch it, and why the guard spawns children.

**Test-level non-vacuity.** With `sorted()` removed and the test suite run:

```
FAILED tests/test_phase21_filler.py::test_render_filler_episodes_is_order_stable
1 failed, 12 passed in 0.28s
```

**Exactly one of thirteen tests went red.** Every other guard — including
`test_filler_renders_identically_in_form_to_a_scored_fact`, which counts rows and is therefore
order-blind — stayed green. That is the demonstration that this guard is the only thing standing
between the corpus and an unreproducible n=64 bin.

**Restore verified:**

| Check | Value |
|---|---|
| sha256 after restore | `bec49415029005cedba080f8dbb3402b0a82ddf11a87280069b0562dbf68d755` — identical to pre-mutation |
| `git diff --exit-code scripts/phase21_filler.py` | `0` |
| `git status --porcelain` | empty |
| `pytest -q tests/test_phase21_filler.py` | 13 passed |

---

## Plan vs Code Fidelity

### Line anchors: 12 of 15 verify in `phase14_factset.py`; 3 are stale, all by +9

| Anchor | Plan | Measured | |
|---|---|---|---|
| `Fact`, `all_pools`, `GATE_PROBES`, `token_census`, `normalize_for_match`, `exact_match_clean`, `_BY_ID`, `LOCKED_FACTS`, `SOFT_TIER_FACTS`, `GATE_REJECTED_CANDIDATES`, `SlotForms`, `SLOT_FORMS` | 51, 127, 290, 313, 323, 334, 380, 390, 410, 429, 524, 543 | same | OK |
| `TAUGHT_FAMILY_IDS` | `:816` | **`:825`** | STALE +9 |
| `PARAPHRASES_PER_FACT_TARGET` | `:821` | **`:830`** | STALE +9 |
| `render_family` | `:824` | **`:833`** | STALE +9 |

All three are off by exactly +9 — the drift 21-05's `render_family` docstring introduced. The plan
was written against the pre-merge file.

### `scripts/teach_persona.py` — stale by +15

| | Plan | Measured |
|---|---|---|
| `render_episodes` | `:247-253` | **`:262-268`** |
| the load-bearing `sorted(family_ids)` | `:251` | **`:266`** |

Located by symbol name, as the prompt instructed. The `sorted()` was mirrored exactly as specified.

### Other divergences, recorded not smoothed

| # | Document | Claim | Measured | Handling |
|---|---|---|---|---|
| 1 | `21-CONTEXT.md` D-17 | filler refused against "the **28** published pool values" | **38** | Counted at runtime; 28 is the non-locked subtotal. The plan already forbade hardcoding it |
| 2 | `21-07-PLAN.md` task 2 | the module assert is "a **NINTH** site of the `== 10` wall" | it is the **12th** overall (11 test sites exist, 21-05 added the 11th) | Shipped as specified; the count corrected here |
| 3 | `21-07-PLAN.md` success criteria | "All **8** `== 10` wall sites green" | 11 sites in 8 FILES; the plan conflates files with sites | All 11 run and green |
| 4 | `21-07-PLAN.md` task 2 | the `sorted()` defect is "**intermittent**" | 12/12 processes diverged — near-certain, not intermittent | Corrected above with the raw log |
| 5 | `21-07-PLAN.md` task 2/3 | tokenizer as `pathlib.Path('artifacts/tokenizer.json')` | a bare relative literal breaks under any other pytest cwd | Used `_ROOT / "artifacts" / "tokenizer.json"`, the derivation ten other modules spell |
| 6 | `21-07-PLAN.md` task 2 | "8 questions/slot x `PROBE_SEEDS = 4` x 56 = **1,792**" | **VERIFIES** — every `SLOT_QUESTION_BANK` entry holds exactly 8; `PROBE_SEEDS = 4` at `phase14_factset_gate.py:62` | Used as stated |
| 7 | `21-07-PLAN.md` task 2 | `56 * 22 == 1232` is "an ESTIMATE, not a target" | **1,232 exactly** | Landed exactly, but asserted as equality-with-a-measured-sibling regardless |

---

## Deviations from Plan

### 1. [Rule 2 — missing critical functionality] `PYTHONHASHSEED` explicitly popped in the child interpreter

- **Found during:** Task 3, writing `test_render_filler_episodes_is_order_stable`.
- **Issue:** `subprocess.run` inherits the parent environment. If the parent pytest process ever
  ran under a fixed `PYTHONHASHSEED` (a CI hardening flag, or `pytest-randomly`), every child would
  iterate `TAUGHT_FAMILY_IDS` in the *same* order and the test would pass **for the wrong reason** —
  certifying a `sorted()` that is not there. The plan specified spawning a second interpreter but
  said nothing about its environment, leaving the guard silently defeatable.
- **Fix:** `_child()` copies `os.environ`, pops `PYTHONHASHSEED`, and passes the result as `env=`.
  Hash randomization is then guaranteed on regardless of how the suite was invoked. Recorded in
  the helper's docstring.
- **Commit:** `62c1132`

### 2. [Deliberate] `test_outside_all_pools`'s before/after runs in a child interpreter

- **Plan asked for:** "a before/after check that importing `phase21_filler` does not change
  `len(fs._BY_ID)` or `len(fs.GATE_PROBES)`".
- **Issue:** in the test process `phase21_filler` is already in `sys.modules` (imported at module
  scope), so an in-process before/after could only ever compare a value to itself — a vacuous check
  of exactly the shape 21-RESEARCH §V.4 warns about.
- **Shipped:** the census runs in a fresh interpreter that records the shape, *then* imports
  `phase21_filler`, then records it again. Measured `(38, 38, 3, 38)` both times.

### 3. [Deliberate] A fourth assertion added to `test_slots_disjoint`

`{f.slot for f in FILLER_FACTS} == set(FILLER_SLOT_FORMS)` — every fact sits in a declared slot
**and** every declared slot is used. Without it, a slot could be declared and silently never
populated (or a fact could reference a slot the grammar does not define, which `forms=` would only
catch at render time).

---

## Not Claimed

- **No claim that the filler corpus produces a correct n=64 training bin.** This plan mints the
  facts and proves the rendered rows are process-stable and identical in FORM to a scored fact. The
  arm itself — `arm_spec` / `n_facts` wiring, the replay ratio, `grad_accum_steps = 64` — is
  21-10/21-11's work. The `~4 windows`, `~264 windows` and `grad_accum_steps = 64` figures in the
  source comment are labelled ESTIMATES and were **not** measured here.
- **No claim about base-model guessability of the 56 values.** That probe is D-17-waived and was
  not run; the waiver names its 1,792-generation price rather than hiding the omission.
- **No claim that the filler values are absent from the base model's training data.** Only that
  they collide with nothing in the published registers and survive the frozen tokenizer round trip.

## Known Stubs

None. Every constant is fully populated, every function fully wired. There is no placeholder branch
and no hardcoded empty value. `render_filler_episodes()` returns 1,232 real rows from real data.

## Threat Flags

None. No network endpoint, no auth path, no new file-access pattern, no schema change at a trust
boundary. The new module is pure data plus pure functions — no torch, no numpy, no I/O at import,
no `main()`. The only import-time side effect is `refuse_collisions()`, which reads in-memory
material and raises.

## Commits

| Commit | Task | Content |
|---|---|---|
| `fe9cabe` | 1 | `scripts/phase21_filler.py` — 8 disjoint filler slots, 56 ordered filler facts |
| `27f97c5` | 2 | The re-implemented minting discipline, the `GUESSABILITY_WAIVER` constant, `render_filler_episodes` |
| `62c1132` | 3 | `tests/test_phase21_filler.py` extended 7 → 13 tests |

## Verification

| Check | Result |
|---|---|
| `pytest -q tests/test_phase21_filler.py` | **13 passed** |
| `-k slots_disjoint` / `minting_discipline` / `outside_all_pools` / `order_stable` | 1 passed each, 12 deselected |
| `-k forms_is_wired` (21-05's, still collects both registers) | 2 passed, 11 deselected |
| SC5 guard set, 8 files | **334 passed, 2 skipped** — matches 21-05's baseline |
| Wide-glob scanners, 5 files | **186 passed** |
| `ruff check . && ruff format --check .` | All checks passed, 182 files formatted |
| `git diff --exit-code` on the 3 frozen files | `0` |
| `git ls-files 'results/phase21_*'` | empty |
| `git status --porcelain` | empty |

No bare `pytest -q` was run: plans 21-06 and 21-08 hold live deliberate-RED canaries in sibling
worktrees during wave 3, and `pyproject` sets `testpaths = ["tests"]`. The full suite is a
**wave-close** gate (`21-VALIDATION.md:47,52`), not a plan-close one.

## Self-Check: PASSED

- `scripts/phase21_filler.py` — FOUND on disk
- `tests/test_phase21_filler.py` — FOUND on disk, extended (7 → 13 tests), 21-05's five tests intact
- `.planning/phases/21-.../21-07-SUMMARY.md` — FOUND on disk
- Commits `fe9cabe`, `27f97c5`, `62c1132` — all present in `git log ae5eb18..HEAD`
- Working tree clean; `scripts/mitigation_unit.py` sha256 byte-identical to base
- `.planning/STATE.md` and `.planning/ROADMAP.md` untouched, per worktree mode
