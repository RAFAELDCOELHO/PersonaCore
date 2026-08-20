---
phase: 19-selective-memory-erasure
plan: 10
subsystem: measurement
tags: [noise-floor, seed-stride-replicate, retention-ppl, dialogue-ppl, closed-pin, pre-erasure-failure, erase-01, stat-01, stat-02, stat-06]

requires:
  - phase: 19-selective-memory-erasure
    provides: "the CLOSED 15-commit pin — `dialogue-floor`, `noise-floors`, `dialogue_floor_from_record`, `dialogue_cap`, `nontarget_deltas`, `nontarget_rows`, `nontarget_noise_floor`, `replicate_seed_stride`, `SEED_STRIDE_OFFSET`, `RETENTION_MEASUREMENT`"
  - phase: 19-selective-memory-erasure
    provides: "`scripts/phase19_run.py` — the UNPINNED THROWAWAY the pin's own `main` docstring names; created at 19-09, extended here"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "`results/phase18_corpus.json` (216 A2 entries) and `results/phase18_arm_adapter-on.json` (the committed pre-erasure per-fact rates the (b) replicate is differenced against)"
  - phase: 14-persona-teaching
    provides: "`checkpoints/persona_adapter.pt` — the production taught adapter, read UNERASED here; and the published 5.8154 dialogue PPL"
provides:
  - "THE (b) NOISE FLOOR: `nontarget_noise_floor` = `0.14814814814814814`, margin at the gate `0.2962962962962963` — seven per-fact `|Δrate|` each over its own 27, reduced by the pinned `max`"
  - "THE (c) DIALOGUE FLOOR: `0.005214448168350039`, cap `4.5837288963367` (task 1, `c9f5f97`)"
  - "THE FIRST RETENTION PPL ON THE PRODUCTION TAUGHT ADAPTER: ON `4.219759892336485`, OFF `3.891139975617828`, cap `4.029000`"
  - "THE FINDING: BOTH halves of condition (c) already fail on the untouched taught adapter — dialogue +1.2317 over cap, retention +0.1908 over cap"
  - "`results/phase19_arm_replicate.json` — the seed-stride replicate arm record, 216 entries, 10,368 draws, 45.3 min"
  - "`results/phase19_noise_floors.json` — all three blocks, each derived through a pinned function"
  - "`tests/test_phase19_noise_floors.py` — 4 tests; every number re-derives from a committed record"
  - "the ancestry guard, still NON-VACUOUS and green: checked = 225 = 15 pin commits x 15 artifacts"
affects: [19-11, 19-12, 19-13, 19-14, 19-15, 19-16]

tech-stack:
  added: []
  patterns:
    - "a plan instruction contradicted by the CLOSED pin is RECORDED with the pin's own refusal quoted, never forced through — three landed in this plan alone"
    - "a guard scoped to a PRECEDENT is narrowed by EXCLUDING the named successor under a positive obligation, never by lowering the count — lowering retires the guard"
    - "a stale claim inside CLOSED prose is corrected in the ARTIFACT the unpinned driver writes, not in the prose"
    - "a saturated measurement is reported as a ceiling artefact, not as a measured zero — four of seven (b) facts sit at their ceiling in both readings"
    - "a block regenerated after a prose-only correction doubles as a determinism check: both PPLs reproduced bit-identically"

key-files:
  created:
    - results/phase19_arm_replicate.json
    - results/phase19_replicate_run.log
    - tests/test_phase19_noise_floors.py
    - .planning/phases/19-selective-memory-erasure/deferred-items.md
  modified:
    - results/phase19_noise_floors.json
    - scripts/phase19_run.py
    - tests/test_phase19_erasure.py

key-decisions:
  - "THE (b) FLOOR IS 0.14814814814814814 AND FOUR OF ITS SEVEN INPUTS CANNOT CONTRIBUTE TO IT. `cat_name`, `street` and `sibling_name` read 27/27 in BOTH the Phase 18 baseline and the replicate, and `person_name` reads 26/27 in both — a saturated fact has no room to vary upward, so its zero delta is a ceiling artefact and not a measurement of sampling noise. The pinned reduction is `max`, so the published floor is the noise of the three facts that CAN move. Reported as such because the number is threshold-shaped: 0.2963 x 27 = 8.0 means a non-target may lose EIGHT of its twenty-seven questions post-erasure and still clear (b)"
  - "BOTH HALVES OF CONDITION (c) FAIL BEFORE ANY ERASURE, and both are published rather than either being softened. Dialogue 5.8154 against a 4.5837 cap (+1.2317); retention 4.2198 against the fully determined 4.029 cap (+0.1908). §Q4 named this shape in advance and D8 fixes the posture: (c) as written cannot discriminate an erasure at 13.9M parameters, and a (c) failure that predates the erasure is a different finding from one caused by it"
  - "THE PLAN'S `assert_phase18_parity` INSTRUCTION WAS REFUSED BY THE PIN AND THE REFUSAL WAS PUBLISHED INSTEAD OF WORKED AROUND. `PARITY_ASSERTED_ARMS` is `('erased', 'retrain')` and `_cmd_noise_floors`' own docstring reads 'the arm parity is NOT asserted', because `seed_stride` is a `PARITY_KEY` and the stride is offset ON PURPOSE — asserting it would abort the run by design. The block publishes the per-key comparison: 7 of 8 keys match Phase 18 exactly, only `seed_stride` differs"
  - "THE CENSUS GUARD WAS SCOPED TO THE PRECEDENT, NOT LOWERED. `test_retention_measurement_pins_a_new_call_site_with_no_adapted_precedent` went RED at `8 == 6` because `scripts/phase19_run.py` is a fifth caller. It already excluded the PIN on the grounds that the pin is the SUCCESSOR and the census is about the PRECEDENT; the driver is excluded on identical grounds and under the same positive obligation — every excluded caller must be shown to reach the injection path. Raising 6 to 8 would have retired the guard; excluding by name keeps a genuinely new unadapted caller reddening it"
  - "CLAUSE 2's STRONGER CLAIM IS NOW FALSE AND WAS CORRECTED IN THE ARTIFACT, NOT IN THE PIN. 'retention PPL has never once been measured on a LoRA-adapted model in this repository' stopped being true at 19-09, and the caller that falsified it is the PIN ITSELF — `run_erasure_arm._capability()` (`:2869`) runs on `load_adapted_model`, so `results/phase19_arm_cal-erased.json` already carries `retention_ppl = 3.7583892242829355`. The `adapted_precedent` field states the narrower true claim; the CLOSED prose was not opened"
  - "THE (b) PATH'S DENOMINATOR WAS RECOVERED, NEVER RELAXED. `_nontarget_rates` demands `n_questions == 27` and both pin producers deliver 13 or 14 (19-09's defect C in the (b) position). The recovery drives the pin's own `per_fact_rows` ONCE PER TIER and sums, reconstituting exactly 27 = 14 + 13. The reduction to the gate's scalar stays the pinned `nontarget_noise_floor`, called and never inlined"

requirements-completed: [STAT-01, STAT-02, STAT-06]
requirements-advanced: [ERASE-01]
# ERASE-01 is NOT marked complete. This plan measured PRE-erasure noise floors on the UNERASED
# adapter; no taught fact has been erased. ERASE-01 is "selective erasure of a taught fact" and
# that is 19-12.

duration: 108min
completed: 2026-08-18
---

# Phase 19 Plan 10: The Two Noise Floors, and the Condition That Was Already Red — Summary

**Both noise floors `erasure_succeeded` requires now exist: (b) = `0.14814814814814814` and
(c) dialogue = `0.005214448168350039`. Retention PPL on the production taught adapter exists for
the first time: `4.219759892336485` against a `4.029000` cap. BOTH HALVES OF CONDITION (c)
ALREADY FAIL ON THE UNTOUCHED ADAPTER, before anything is erased. Three of the plan's own
instructions were falsified by the CLOSED pin and recorded rather than forced through. The pin is
byte-identical at 15 commits.**

## Performance

- **Duration:** ~108 min (45.3 min of it the (b) replicate; ~4 min retention, twice)
- **Tasks:** 3 of 3 (task 1 was already committed at `c9f5f97` when this executor resumed)
- **Files:** 4 created, 3 modified; no adapter produced by tasks 2-3
- **Tests:** 830 passed, 1 skipped (826 baseline + the 4 added here)

## Task Commits

| Task | Commit | What |
| ---- | ------ | ---- |
| 1 | `c9f5f97` | the (c) dialogue floor from the pinned seed pair — committed before this executor resumed |
| 2 | `8a02b04` | `results/phase19_arm_replicate.json` + the (b) block + `tests/test_phase19_noise_floors.py` |
| 3 | `165e525` | the retention block, the `n − 1` denominator guard, the census scoped to the precedent |
| 3 | `d88f0fe` | `style` — rewrap of the corrected precedent claim under 100 columns |

## The (b) Noise Floor — Seven Facts, Each Over Its Own 27, Never Pooled

Raw runner output, pasted literally:

```
[phase19_run] (b) per-fact |drate|, question unit, own denominator, never pooled:
    cand_cat_zibby           cat_name       27/27 -> 27/27   |d| = 0.0
    cand_house_7412          house_number   24/27 -> 23/27   |d| = 0.03703703703703698
    cand_person_quillon      person_name    26/27 -> 26/27   |d| = 0.0
    cand_sister_orsala       sibling_name   27/27 -> 27/27   |d| = 0.0
    cand_street_marrowgate   street         27/27 -> 27/27   |d| = 0.0
    cand_town_brindlemoor    hometown       21/27 -> 17/27   |d| = 0.14814814814814814
    cand_year_1987           birth_year     18/27 -> 15/27   |d| = 0.11111111111111105
    nontarget_noise_floor(max) = 0.14814814814814814; margin at gate = 0.2962962962962963
```

Per tier, so the 27 = 14 + 13 is auditable rather than asserted:

| fact | slot | pre (taught + held-out) | post (taught + held-out) | \|Δ\| |
| --- | --- | --- | --- | --- |
| `cand_cat_zibby` | cat_name | 27/27 = 14/14 + 13/13 | 27/27 = 14/14 + 13/13 | `0.0` |
| `cand_street_marrowgate` | street | 27/27 = 14/14 + 13/13 | 27/27 = 14/14 + 13/13 | `0.0` |
| `cand_sister_orsala` | sibling_name | 27/27 = 14/14 + 13/13 | 27/27 = 14/14 + 13/13 | `0.0` |
| `cand_person_quillon` | person_name | 26/27 = 14/14 + 12/13 | 26/27 = 14/14 + 12/13 | `0.0` |
| `cand_house_7412` | house_number | 24/27 = 14/14 + 10/13 | 23/27 = 14/14 + 9/13 | `0.03703703703703698` |
| `cand_year_1987` | birth_year | 18/27 = 8/14 + 10/13 | 15/27 = 8/14 + 7/13 | `0.11111111111111105` |
| `cand_town_brindlemoor` | hometown | 21/27 = 13/14 + 8/13 | 17/27 = 10/14 + 7/13 | **`0.14814814814814814`** |

**Four of the seven cannot contribute to the floor.** Three sit at 27/27 in both readings and one
at 26/27 in both. A saturated fact has no room to vary upward, so its zero delta is a ceiling
artefact rather than measured sampling noise. The pinned reduction is `max`, so the published
floor is the noise of the three facts that CAN move, taken over a set where four are pinned.

The number is threshold-shaped — `erasure_succeeded` multiplies it by `MARGIN_K` — and it is
permissive: `0.2963 × 27 = 8.0`, so a non-target may lose **eight of its twenty-seven questions**
post-erasure and still clear (b).

### The stride non-collision, proved per question

```
offset                    = 100000   (SEED_STRIDE_OFFSET)
seed indices in use       = 112      (0 .. 111)
phase18_window_end_max    = 5376     = 111 * 48 + 48
replicate bases           = 100000 .. 105328
collision_free            = True
proved_by                 = phase19_erasure.replicate_seed_stride, called on every seed index in use
```

Every question passed through `replicate_seed_stride`, which raises when its Phase 18 window
`[i·K, i·K+K)` reaches the offset. The four measured zeros above are therefore separable from a
collision zero — which is exactly why the separation had to exist before the numbers did.

### The arm's provenance

```
$ tail -3 results/phase19_replicate_run.log
[phase19_erasure] wrote results/phase19_arm_replicate.json in 45.3 min
{'corpus_sha256': 'ff8e6e3c...f0dd67', 'forbid_ids_sha256': '79b55770...3cfc28', 'k': 48,
 'seed_stride': 'replicate: SEED_STRIDE_OFFSET 100000 + seed_index * K', 'ablated_components': [],
 'arm': 'replicate', 'attack_family': 'A2', 'corpus': 'phase18_corpus.json', 'corpus_entries': 216,
 'device': 'mps', 'wall_clock_min': 45.27792596419652}
EXIT=0
```

`ablated_components: []` — the adapter is the UNERASED production one, which is what makes this a
noise floor and not an effect size. 216 entries × K=48 = 10,368 draws; 9,072 of them non-target.

## Retention PPL on the Adapted Model — the Measurement §Q4 Found Missing

```
[phase19_run] retention adapter_on = 4.219759892336485
[phase19_run] retention adapter_off = 3.891139975617828
[phase19_run] retention cap = 4.029
[phase19_run] retention n_windows = 3908
[phase19_run] retention n_scored_tokens = 1000285
```

| quantity | value |
| --- | --- |
| adapter ON | `4.219759892336485` |
| adapter OFF | `3.891139975617828` |
| ON − OFF | `0.3286199167186572` |
| cap | `4.029000` = `3.891140 + 2 × 0.068930` (`erasure_gate.py:246`) |
| **ON above cap** | **True — headroom `−0.1907598923364855`** |
| OFF above cap | False |
| dead-id mask | `79b55770f4dcfa943d7528cb04829e8d2e7dd8823b9b5450da418b4fcf3cfc28` — matches the pinned `FORBID_IDS_SHA256` |
| mask census | 7,645 dead of 8,192 vocab; 547 live |

**The OFF arm validates the instrument against the cap's own operand.** `3.891139975617828`
against the committed `V20_EWC_RETENTION_PPL` = `3.891140` is `2.4e-08` absolute — the un-adapted
reading reproduces the exact constant the cap is built from, so the excess is the adaptation's
cost and not an instrument mismatch. The ON−OFF gap is **4.77×** the committed retention noise
floor `0.068930`; admitting the pre-erasure model would need `MARGIN_K` = `4.767`, not `2`.

**The block was regenerated after a prose-only correction and both PPLs reproduced
bit-identically** — a determinism check obtained for free.

## THE FINDING: Condition (c) Is Red on BOTH Legs Before the Erasure Exists

| leg | pre-erasure reading | cap | standing |
| --- | --- | --- | --- |
| dialogue | `5.8154` | `4.5837288963367` | **+1.2317 OVER** |
| retention | `4.219759892336485` | `4.029000` | **+0.1908 OVER** |

Task 1 found the dialogue half failing; task 3 found the retention half failing the same way.
Condition (c) as written therefore cannot attribute anything to an erasure that has not happened.
§Q4 named this shape in advance and D8 fixes the posture: it ships unsoftened, the estimators were
not re-chosen, and 19-15 must publish the pre-erasure standing beside any post-erasure reading —
a (c) failure that predates the erasure and one caused by it are different findings, and the only
thing separating them is having both numbers.

## Deviations from Plan

### 1. [Falsification — plan instruction refused by the pin] `assert_phase18_parity` is not for this arm

- **Found during:** Task 2 pre-flight, before the 45-minute run started
- **Plan said:** "Call `assert_phase18_parity` on the config before the first draw."
- **Measured:** `PARITY_ASSERTED_ARMS = ('erased', 'retrain')` — `replicate` is not in it, and
  `_cmd_noise_floors`' own docstring reads *"the arm parity is NOT asserted"*. `seed_stride` is a
  `PARITY_KEY` and the stride is offset ON PURPOSE, so asserting parity would abort the run by
  design.
- **Done instead:** the block publishes the per-key comparison. **7 of 8 keys match Phase 18
  exactly** (`corpus_sha256`, `forbid_ids_sha256`, `k`, `asr_rungs`, `stop_ids`,
  `sample_temperature`, `sample_top_p`); only `seed_stride` differs, with the reason recorded.
- **Commit:** `8a02b04`

### 2. [Falsification — the plan asked for a measurement with no draws behind it] the soft facts

- **Found during:** Task 2
- **Plan said:** "Score the two SOFT-tier taught facts as well and store them under
  `soft_descriptive`."
- **Measured:** `results/phase18_corpus.json` holds `core_taught` and `core_held_out` ONLY. This
  arm's tier census is `{core_held_out: 104, core_taught: 112}` and **soft = 0**. A soft rate here
  would have no draws behind it.
- **Done instead:** `soft_descriptive.measured = false` with the census, the slot list and the
  reason — the narrowing is declared rather than reported as a measurement that was not taken.
- **Commit:** `8a02b04`

### 3. [Rule 3 - Blocking] the pinned (b) path raises on both of its own producers

- **Found during:** Task 2
- **Issue:** `_nontarget_rates` proves `n_questions == N_TARGET_QUESTIONS` (27).
  `target_rows_from_arm_record` scores the gated tier alone (13); `run_erasure_arm`'s
  `rows.update(per_fact_rows(...))` lets `core_taught` (14) overwrite `core_held_out` (13) —
  19-09's defect C in the (b) position. `nontarget_deltas` aborts on both sides.
- **Fix:** drive the pin's own `per_fact_rows` ONCE PER TIER and sum, reconstituting 27 = 14 + 13.
  The reduction to the scalar stays the pinned `nontarget_noise_floor`, called and never inlined.
  `test_the_pinned_b_path_still_raises_on_both_of_its_own_producers` asserts the defect against the
  CODE, so the artifact's `denominator_recovery` sentence cannot outlive it.
- **Commit:** `8a02b04`

### 4. [Rule 1 - Bug] the pin's retention census guard went RED, and the claim it protects is stale

- **Found during:** Task 3
- **Issue:** `RETENTION_MEASUREMENT` clause 2 promised *"the committed test re-runs that census by
  AST walk on every run, so the claim cannot go stale the first time someone adds a fifth
  caller"*. `scripts/phase19_run.py` is that fifth caller:

  ```
  E  AssertionError: the retention call-site census moved: 8 calls in ['build_retention_bin.py',
     'finetune_ab.py', 'finetune_dialog.py', 'finetune_smoke.py', 'phase19_run.py']
  E  assert (8 == 6)
  ```

- **Fix:** the test already excluded the PIN on the grounds that the pin is the SUCCESSOR and the
  census is about the PRECEDENT. The driver — named by the pin's own `main` docstring — is
  excluded on identical grounds, under the same positive obligation both successors now carry:
  each must be shown to reach the injection path. Raising `6` to `8` would have retired the guard;
  excluding by name keeps a genuinely new unadapted caller reddening it. The precedent census is
  untouched at 6 calls in 4 modules, which is what ties the test to the CLOSED prose.
- **And the claim itself is now false.** Clause 2's stronger sentence — *"retention PPL has never
  once been measured on a LoRA-adapted model in this repository"* — stopped being true at 19-09,
  and the caller that falsified it is **the pin itself**: `run_erasure_arm._capability()`
  (`:2869`) runs on `load_adapted_model`, so `results/phase19_arm_cal-erased.json` already carries
  `retention_ppl = 3.7583892242829355` over the same 1,000,285 tokens, on the calibration adapter.
  The artifact's `adapted_precedent` field states the narrower true claim — first on the
  **production taught** adapter, first taken ON and OFF in one process and published standalone
  with its own denominator, cap and mask digest. **The CLOSED prose was not opened.**
- **Commit:** `165e525`

### 5. [Rule 1 - Bug] the retention denominator guard was checking a formula the code does not use

- **Found during:** Task 3
- **Issue:** the driver asserted `n_corpus - n_windows == on_tokens`, taken from
  `perplexity.py:11-13`. That form assumes DISJOINT slices. The code slices
  `data[i : i+block+1]` at stride `block`, so consecutive windows share their boundary token and
  every target `1..n-1` is scored exactly once.

  ```
  n = 1000286   n_windows = 3908
  measured denominator      = 1000285
  n - 1                     = 1000285   match: True
  n - n_windows (docstring) = 996378    match: False
  ```

- **Fix:** the guard checks `n - 1` and the artifact records `n_scored_tokens == corpus_tokens - 1`,
  asserted by `tests/test_phase19_noise_floors.py`. `tests/test_perplexity.py:98-104,122` already
  describes and asserts the correct form, so only the module docstring is stale — **prose only,
  no measured number in the repository is wrong.** `perplexity.py` is the frozen gate-metric
  module, so the one-line docstring fix is logged to `deferred-items.md` rather than taken here.
- **Commit:** `165e525`

### 6. [Naming — third occurrence this phase] the plan's adapter path never existed

- **Plan frontmatter said:** `checkpoints/phase19_noise_seed_b_adapter.pt`
- **Measured:** the file does not exist. The pin writes through `tp.arm_outputs`, giving
  `checkpoints/phase19_erase_dialogue_floor_seed{1337,2024}_adapter.pt`. Tasks 2 and 3 produced no
  adapter at all — task 2 read the UNERASED production adapter and task 3 read the same one.
- **Note:** 19-08 and 19-09 each hit the same class. **Read the pin's constant, never the plan's
  spelling.**

### 7. [Style] a lint failure in this executor's own edit

`E501` at `scripts/phase19_run.py:714`. Caught by `ruff` before the final verification, fixed in
`d88f0fe`. The concatenated string is byte-identical to the one already committed in the artifact
(1,244 chars, verified by AST-extracting the literal and comparing against `git show HEAD:`), so
the published block needed no regeneration.

## What This Plan Did NOT Do

- **No taught fact was erased.** The target's erasure is 19-12; no target erasure number exists.
  Both readings here are on the UNERASED adapter, which is what makes them noise floors.
- **No constant was locked.** `git ls-files 'scripts/phase19_floor.py'` returns empty.
- **Defect A was not worked around.** It bites 19-12's target arm, not this one.

## Verification

### The pin, byte-identical — fresh

```
$ shasum -a 256 scripts/phase19_erasure.py
c407246de3c470094ab0bdd868961b7b1c22529c5e00522fec67c3852cb6e303  scripts/phase19_erasure.py
$ git log --oneline -- scripts/phase19_erasure.py | wc -l
      15
$ git log --oneline -- scripts/phase18_extraction.py | wc -l
      26
```

### The ancestry guard, non-vacuous at 15 artifacts

```
pin commits to scripts/phase19_erasure.py : 15   (MUST be 15)
tracked results/phase19_* artifacts       : 15
  results/phase19_arm_cal-erased.json                   first-add 14ab93df6 — 15/15 ancestors
  results/phase19_arm_replicate.json                    first-add 8a02b04dc — 15/15 ancestors
  results/phase19_cal_training.log                      first-add 0ee9b322a — 15/15 ancestors
  results/phase19_calibration_corpus.json               first-add 7293ec97d — 15/15 ancestors
  results/phase19_calibration_correction.json           first-add dcb1b7c1c — 15/15 ancestors
  results/phase19_calibration_correction.md             first-add 06dd3a35f — 15/15 ancestors
  results/phase19_calibration_curve.json                first-add 69fc6718c — 15/15 ancestors
  results/phase19_calibration_curve_siblings.json       first-add 69fc6718c — 15/15 ancestors
  results/phase19_dialogue_floor.json                   first-add c9f5f979c — 15/15 ancestors
  results/phase19_dialogue_floor_training.log           first-add c9f5f979c — 15/15 ancestors
  results/phase19_erase_calibration/run.csv             first-add 0ee9b322a — 15/15 ancestors
  results/phase19_erase_dialogue_floor_seed1337/run.csv first-add c9f5f979c — 15/15 ancestors
  results/phase19_erase_dialogue_floor_seed2024/run.csv first-add c9f5f979c — 15/15 ancestors
  results/phase19_noise_floors.json                     first-add c9f5f979c — 15/15 ancestors
  results/phase19_replicate_run.log                     first-add 8a02b04dc — 15/15 ancestors

checked = 225; len(pin)*len(art) = 225; product OK: True
bool(checked)==bool(tracked) : True      NON-VACUOUS: True
scripts/phase18_extraction.py commits (must be 26): 26
```

### Lint and full suite, fresh

```
$ .venv/bin/python -m ruff check . && .venv/bin/python -m ruff format --check .
All checks passed!
169 files already formatted

$ .venv/bin/python -m pytest -q
830 passed, 1 skipped, 83 warnings in 178.66s (0:02:58)
```

826 was 19-09's baseline; the 4 added are `tests/test_phase19_noise_floors.py`.

### The plan's own verification

```
$ .venv/bin/python -m pytest -q tests/test_phase16_prereg.py tests/test_phase19_erasure.py \
      tests/test_package.py tests/test_phase19_noise_floors.py tests/test_perplexity.py
105 passed in 39.39s

$ .venv/bin/python -c "... assert len(r['per_fact'])==7 ... assert r['value']==p.nontarget_noise_floor(...)"
PASS value = 0.14814814814814814

$ .venv/bin/python -c "... assert r['adapter_on']>0 and r['adapter_off']>0 and r['cap']==4.029"
PASS

$ grep -rn '0%' results/phase19_*
(no matches — STAT-02 clean)

$ git ls-files 'scripts/phase19_floor.py' | wc -l
       0        (the floor is NOT locked)

$ git diff --diff-filter=D --name-only c9f5f97..HEAD
(empty — nothing was deleted)
```

## The Persistent Artifacts — path, size, sha256

All gitignored (`.gitignore:14`), on disk, never `git add -f`'d. **Tasks 2 and 3 produced no new
adapter**; the two seed adapters below are task 1's, recorded here because the plan's frontmatter
named a third path that never existed.

| path | bytes | sha256 |
| ---- | ----- | ------ |
| `checkpoints/persona_adapter.pt` (PRODUCTION taught — 19-12/19-13 consume) | 1,350,523 | `226f2ae59938e389b396d999bc5f3e1e464874db5f3352d513dc5cd85984ebfb` |
| `checkpoints/phase19_erase_dialogue_floor_seed1337_adapter.pt` | 1,352,991 | `f12ab4c3db4126b5399f46cd2b674d7ae5fdae83f7aff27fdffe9bb65ee64974` |
| `checkpoints/phase19_erase_dialogue_floor_seed2024_adapter.pt` | 1,352,991 | `3fd5aba43e25c43a957d3e6901c398c20a8f3b308f9f04facaa80c23c444f74f` |
| `checkpoints/phase19_cal_erased_adapter.pt` (19-09, unchanged) | — | `e3cb42b867ba1b751523985b92adb386619723f4974faeb007dcb2142b3e1842` |
| `checkpoints/phase19_erase_calibration_adapter.pt` (19-08, unchanged) | — | `bc616c3667719e677532a5e56c7b8de8e2dc79e15af85ccc14bc1dcce66856da` |

## Known Stubs

None. Every number in `results/phase19_noise_floors.json` is a measured output of committed code,
derived through a pinned function, and re-derived from a committed record by
`tests/test_phase19_noise_floors.py` on every suite run. `soft_descriptive.measured = false` is a
declared narrowing with its census, not a stub.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema at a trust boundary was
introduced — this plan reads two committed corpora and one adapter and writes one JSON artifact.

## Handover to 19-11+

1. **19-11 LOCKS `TARGET_FLOOR = 0.09107873950450847`** (19-09's corrected floor). Unchanged by
   this plan, and `tests/test_phase19_correction.py::test_a_locked_floor_must_be_the_corrected_one`
   still guards it. `scripts/phase19_floor.py` is still absent.
2. **The (b) floor is `0.14814814814814814`, margin `0.2962962962962963`** — and it is permissive
   for the reason above: four of its seven inputs are saturated and the margin tolerates a
   non-target losing eight of twenty-seven questions. 19-15's report must state that, not just the
   scalar.
3. **Condition (c) is already red on BOTH legs.** Any post-erasure (c) reading must be published
   beside these pre-erasure ones or the report will attribute a pre-existing failure to the
   erasure. Both caps and both pre-erasure readings are in
   `results/phase19_noise_floors.json`.
4. **Defect A still bites 19-12.** A clean target erasure produces 0 successes and
   `zero_results_have_nll` reads False on key ORDER alone, so `erasure_gate` short-circuits to
   INCONCLUSIVE. Read the flag against an order-normalised copy of the record and say so.
5. **The pin is still 15 commits and must stay there.** `scripts/phase18_extraction.py` is still
   26. Any further defect gets a dated continuation, never an edit.
6. **Read the pin's constants, never a plan's spelling.** Three plans in a row have named
   artifacts the pin does not use.

## Self-Check: PASSED

```
FOUND: results/phase19_arm_replicate.json
FOUND: results/phase19_replicate_run.log
FOUND: results/phase19_noise_floors.json  (3 blocks: dialogue_ppl_noise_floor, nontarget_noise_floor, retention_ppl_pre_erasure)
FOUND: tests/test_phase19_noise_floors.py
FOUND: .planning/phases/19-selective-memory-erasure/deferred-items.md
FOUND: checkpoints/persona_adapter.pt (gitignored, on disk, UNERASED)
FOUND commit: c9f5f97
FOUND commit: 8a02b04
FOUND commit: 165e525
FOUND commit: d88f0fe
ABSENT (required): scripts/phase19_floor.py
scripts/phase19_erasure.py sha256 c407246d… — byte-identical, 15 commits
```
