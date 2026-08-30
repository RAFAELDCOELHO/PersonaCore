---
phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
plan: 06
subsystem: training-data
tags: [build-bins-seam, byte-identity, wiring-guard, seed-purity, mixture-ratio, adversarial-arms]

# Dependency graph
requires:
  - phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
    provides: "24-05's `adversarial_episodes(tok)` / `adversarial_pool_size(tok)` — the parity-proved 336-episode attack pool in a stable, non-sorted, corpus-derived order"
  - phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
    provides: "24-02's `mitigation_budget.ADVERSARIAL_RATIO_GRID` — the six pinned sweep points"
  - phase: 21-the-fact-aligned-packer
    provides: "`build_bins`' byte-identity discipline and `tests/fixtures/golden_build_bins_v2.json`; `test_align_facts_is_wired` as the load-bearing-half pattern this plan copies"
  - phase: 23-cost-calibration
    provides: "the D-07 resume rebuild-and-compare, which is why the interleave permutation must be a pure function of the existing seed"
provides:
  - "`teach_persona.build_bins(..., adversarial_ratio=0.0, seed=SEED)` — a build-time mixture seam, byte-identical at its default, with nine additive stats keys on the non-zero branch only"
  - "`teach_persona._mix_adversarial` — D-06 episode-unit sizing, D-07 reported multiplicity, D-08 `random.Random(seed)` interleave, D-10 per-family counts of the SELECTED prefix"
  - "`phase24_adversarial.adversarial_episode_families(tok)` — the per-episode family in `adversarial_episodes`' exact order, built in the same pass"
  - "`ARMS` gains `adv_n8` / `adv_n64`, both packing FLAT (outside `DP_ARMS`), both `replay_ratio = 0.0`"
  - "`adversarial_ratio` threaded through `build_arm_bins` and `train_arm` for Phase 25's programmatic sweep"
  - "`tests/test_phase24_bins.py` — six tests, ten items, all watched RED before the kwarg existed"
affects: [24-07 four-corner band check, 25 frontier sweep driver]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "The wiring sibling written and watched RED BEFORE the kwarg exists — a byte-identity guard over an unread kwarg is a tautology, so the non-identity half is what makes the identity half mean anything"
    - "Two views onto ONE pass: `_adversarial_pool` returns `(episodes, families)` and the two public functions are thin selectors, so positional pairing is a property of one loop rather than of two readers agreeing"
    - "Interleave observability taken off the WRITTEN BYTES (prefix/suffix inequality against the ratio-0.0 bin) rather than off the stats dict — an appended layout is exactly `clean_bytes + adversarial_bytes`, so the negation is exact"
    - "A private `random.Random(seed)` instance, never the ambient global stream, when the output is compared byte-for-byte by a resume path"

key-files:
  created:
    - tests/test_phase24_bins.py
  modified:
    - scripts/teach_persona.py
    - scripts/phase24_adversarial.py

key-decisions:
  - "Tasks 1 and 2 were committed TOGETHER (`d274dfb`) so no commit leaves HEAD red — the RED was OBSERVED and is quoted in full below, which is the evidence the plan asked for; a red commit would have been the artifact, not the evidence"
  - "`_build_aligned_bins`' signature and `build_bins`' dispatch call were also edited, which Task 2's deletion-audit criterion did not list — mechanically required by 'widen the helper rather than branch at the call site', since the helper's only call site is inside `_build_aligned_bins`"
  - "`adversarial_episodes`' body was moved into `_adversarial_pool` rather than duplicating the corpus filter in a second function — the pinned return SHAPE is unchanged, and the alignment 24-06 depends on is now structural"
  - "ADVT-01 / ADVT-03 deliberately NOT ticked; `.planning/REQUIREMENTS.md` stays byte-unchanged for the whole phase, as in all five prior plans"

patterns-established:
  - "A per-family equality check inside the builder, not just an equal total: an equal total is satisfied by a corpus that lost every A3 row and gained as many A1-mild ones"
  - "The `n_want < 1` refusal names the smallest ratio that would place one episode, so the operator gets the fix and not just the diagnosis"

requirements-completed: []

# Metrics
duration: 32min
completed: 2026-08-30
---

# Phase 24 Plan 06: The `adversarial_ratio` Seam — Summary

**`build_bins` now bakes an adversarial refusal mixture into the BIN rather than into the loop —
sized in EPISODES so it can never read the private corpus's token total, interleaved by a
`random.Random(seed)` permutation the Phase 23 resume path can reproduce, and byte-identical to the
no-kwarg call at its default. The identity half is not vacuous: the wiring sibling was watched RED
with `TypeError: build_bins() got an unexpected keyword argument 'adversarial_ratio'` before the
parameter existed.**

## Performance

- **Duration:** 32 min (18:07:17Z start → 18:39Z)
- **Started:** 2026-08-30T18:07:17Z
- **Tasks:** 3 of 3 (Tasks 1 and 2 in one commit — see Deviations)
- **Files modified:** 3 (1 created, 2 extended)

## Task Commits

1. **Tasks 1 + 2: the test module (watched RED first) and the seam** — `d274dfb` (feat) —
   `tests/test_phase24_bins.py`, `scripts/teach_persona.py`, `scripts/phase24_adversarial.py`.
2. **Task 3: the two adversarial arms and the threading** — `75d2d6d` (feat) —
   `scripts/teach_persona.py` only.

**Plan metadata:** see the `docs(24-06)` commit carrying this SUMMARY, STATE.md and ROADMAP.md.

**No commit in this plan's history leaves HEAD red.**

## Task 1: the RED, quoted

`.venv/bin/python -m pytest -q tests/test_phase24_bins.py`, taken with `scripts/` untouched
(`git status --porcelain -- tests/ scripts/ src/` reported exactly one path, `?? tests/test_phase24_bins.py`):

```
FAILED tests/test_phase24_bins.py::test_adversarial_ratio_is_wired - TypeErro...
FAILED tests/test_phase24_bins.py::test_the_default_path_is_byte_identical_to_the_no_kwarg_call
FAILED tests/test_phase24_bins.py::test_the_interleave_permutation_is_a_pure_function_of_the_seed
FAILED tests/test_phase24_bins.py::test_adversarial_episodes_are_interleaved_not_appended
FAILED tests/test_phase24_bins.py::test_the_mixture_is_sized_from_episode_count_not_teaching_tokens
FAILED tests/test_phase24_bins.py::test_every_grid_point_trains_all_three_families_in_balance[0.25]
FAILED tests/test_phase24_bins.py::test_every_grid_point_trains_all_three_families_in_balance[0.5]
FAILED tests/test_phase24_bins.py::test_every_grid_point_trains_all_three_families_in_balance[1.0]
FAILED tests/test_phase24_bins.py::test_every_grid_point_trains_all_three_families_in_balance[1.5]
FAILED tests/test_phase24_bins.py::test_every_grid_point_trains_all_three_families_in_balance[1.9090909090909092]
10 failed in 0.63s
```

`10 failed, 0 passed` — exactly the acceptance criterion. The frame for the load-bearing test,
run alone:

```
$ .venv/bin/python -m pytest -q "tests/test_phase24_bins.py::test_adversarial_ratio_is_wired"
kwargs = {'adversarial_ratio': 0.0}
...
>       stats = tp.build_bins(tok, episodes, bin_path, mask_path, **kwargs)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: build_bins() got an unexpected keyword argument 'adversarial_ratio'

tests/test_phase24_bins.py:65: TypeError
```

Every one of the six functions failed at the same line for the same reason, including the
byte-identity test itself — Python raises on the explicit kwarg before any assertion inside it can
run.

`pytest -q tests/test_phase21_aligned_bins.py tests/test_phase21_replay_volume.py` at this point:
**36 passed**, 0 failed.

### Test 2's pre-wiring no-kwarg baseline

The half of test 2 that IS observable pre-wiring is the no-kwarg build, which the test computes
first. Measured against the untouched `build_bins`, 176 clean `dp_n8` episodes, `seed_everything(1337)`:

```
token_bin_sha256  f146d42637c69e9eb1e7ac2248c9056a7966aed48f6498fa9cdb6d3db02d147b
mask_bin_sha256   a2c4771f92aa4e03127e451b1de880b9386bee5164ee512d291467c1eb1e59a2
episodes 176   tokens 7581   mask_fraction 0.35865980741327
```

This is the digest pair `adversarial_ratio=0.0` is now proved equal to, and it is the pre-edit
value: it was taken before `scripts/teach_persona.py` was touched.

## The numbers this plan was required to publish

Every figure below was measured at HEAD this session.

### Per-grid-point `adversarial_family_counts` (n=8, 176 clean episodes)

| ratio | `adversarial_episodes` | A1-mild | A1-aggressive | A3 | spread | multiplicity | `mask_fraction` | adversarial scored tokens |
|---|---|---|---|---|---|---|---|---|
| 0.25 | 44 | 15 | 15 | 14 | 1 | 0.1310 | 0.3008 | 796 |
| 0.5 | 88 | 30 | 29 | 29 | 1 | 0.2619 | 0.2764 | 1,676 |
| 1.0 | 176 | 59 | 59 | 58 | 1 | 0.5238 | 0.2557 | 3,586 |
| 1.5 | 264 | 88 | 88 | 88 | 0 | 0.7857 | 0.2464 | 5,514 |
| 1.9090909090909092 | 336 | 112 | 112 | 112 | 0 | 1.0 | 0.2410 | 7,098 |

All three trained families are present at every point with `max − min <= 1`, and every row's counts
sum to its `adversarial_episodes`. **What actually holds that:** the committed corpus's row order,
re-derived independently this session as a STRICT 3-cycle `[A1-mild, A1-aggressive, A3] * 112`
(`all(fams[i] == TRAINED_FAMILIES[i % 3] for i in range(336))` → `True`). Nothing else asserts that
ordering, which is exactly why the counts are now reported and asserted at the selected prefix.

`round(1.9090909090909092 * 176) = 336 = adversarial_pool_size(tok)`, so the upper extreme is
multiplicity 1.0 — one full pass of the pool, no repetition. The literal `336` is never typed
anywhere in this plan's code or tests; both the test module and `_mix_adversarial` derive it.

### Task 3E: the real `adv_n8` build at the upper extreme

`build_arm_bins("adv_n8", fs.LOCKED_FACTS, fs.TAUGHT_FAMILY_IDS, adversarial_ratio=ADVERSARIAL_RATIO_GRID[-1])`,
run once for real against `data/`:

```
  smoke draw: x/y (4, 256), y carries -100 — ok
  paraphrases/fact inside (20, 50) for 8 facts
  130 held-out questions: none present at token level
  mask fraction: mean 0.2837 / min 0.1111 / max 0.5714
[teach_persona] adv_n8: 512 episodes, 40,733 tokens (7,581 teaching + 0 replay),
                episode length mean 79.6 [24, 164]
[teach_persona] bins provenance: seed=1337 git_sha=d274dfba... arm=adv_n8
                second_person=False replay_ratio=0.0 mask_fraction=0.2410 wall=0.7s
```

**The `mask_fraction` this plan was required to record: `0.2410`** (aggregate, the figure
`_prove_floor_and_band` gates on), with per-episode mean `0.2837`.

All six `sanity_check` proofs passed on a bin that now contains 336 attacked prompts — **proof 6
in particular**: all **130** held-out questions absent from the written bin as contiguous id runs.
`teaching_tokens` stayed **7,581**, the clean-only value, unchanged by the mixture — the visible
form of D-06's sizing unit.

`git status --porcelain data/` empty after deleting the two bins.

### A finding for 24-07, recorded rather than fixed here

`mask_fraction_min = 0.1111` at the upper extreme is **below** `MASK_FRACTION_BAND`'s 0.15 floor —
but `_prove_floor_and_band` gates the AGGREGATE (`mask_all.mean()`), which is 0.2410 and clears the
floor by 0.0910, well past `MASK_FRACTION_MARGIN = 0.05`. So nothing trips today and nothing here is
wrong. It is recorded because 24-07's four-corner band check is the plan that decides whether the
per-episode floor is a thing worth gating; the shortest adversarial episode is 24 tokens.

## Deviations from Plan

### 1. [Rule 3 — Blocking] Tasks 1 and 2 committed together, so no commit leaves HEAD red

- **Found during:** Task 1's commit step.
- **Issue:** the plan's Task 1 ships a test module that is 10/10 RED by design. Committing it alone
  puts a red HEAD in this phase's history, which this repo's execution contract forbids and which
  all five prior plans in the phase avoided.
- **Fix:** the RED was **observed and captured in full** (quoted above, with the sibling modules
  green and `git status` proving `scripts/` untouched), then Task 2's seam was written and the two
  landed as `d274dfb`. The evidence the plan asked for is the observation, not the commit.
- **Commit:** `d274dfb`.

### 2. [Rule 3 — Blocking] The Task 2 deletion audit did not list two lines it mechanically requires

- **Found during:** Task 2.
- **Issue:** the acceptance criterion confines deletions to the `build_bins` signature, the
  `_refuse_ambiguous_aligned_input` signature and its call, the docstring, and one line in the stats
  block. But `_refuse_ambiguous_aligned_input`'s ONLY call site is inside `_build_aligned_bins`, so
  "widen the helper rather than branch at the call site" cannot be done without also widening
  `_build_aligned_bins`' signature and `build_bins`' dispatch call to it.
- **Fix:** both were widened with `adversarial_ratio=0.0` defaults. The observed deletion set is
  therefore six lines, not four:

```
-def build_bins(tok, episodes, bin_path, mask_path, *, replay_ratio=0.0, align_facts=None):
-        return _build_aligned_bins(tok, episodes, bin_path, mask_path, replay_ratio, align_facts)
-    return {
-def _refuse_ambiguous_aligned_input(episodes, replay_ratio, align_facts):
-def _build_aligned_bins(tok, episodes, bin_path, mask_path, replay_ratio, align_facts):
-    _refuse_ambiguous_aligned_input(episodes, replay_ratio, align_facts)
```

  **The criterion's real content held:** exactly ONE line inside the stats block was deleted
  (`    return {` → `    stats = {`); none of the twelve KEY lines and not the closing brace moved.
  The alternative — refusing at the top of `build_bins` — would have been two fewer lines and one
  more place a "two sources of truth for one bin" guard can live. Not taken.
- **Commit:** `d274dfb`.

### 3. [Rule 2 — Missing critical functionality] `adversarial_episodes`' body moved into `_adversarial_pool`

- **Found during:** Task 2.
- **Issue:** the plan requires `adversarial_episode_families(tok)` to return the family in
  `adversarial_episodes`' EXACT order, "built from the same source rows in the same pass". Writing
  it as a second function that re-filters the corpus would make the alignment a coincidence of two
  readers agreeing — the exact class of drift 24-05's SC4 parity exists to prevent, one level up.
- **Fix:** the body became `_adversarial_pool(tok) -> (episodes, families)`, appending each family
  label in the same loop iteration as its episode; `adversarial_episodes` and
  `adversarial_episode_families` are thin selectors onto it. The PINNED return shape of
  `adversarial_episodes` (`list[tuple[tuple[str, ...], str, str]]`) is unchanged — verified by all
  six of 24-05's tests still passing untouched.
- **Additional guard (Rule 2):** the existing total-count refusal is satisfied by a corpus that lost
  every A3 row and gained as many A1-mild ones, so a PER-FAMILY equality was added beside it
  (`{family: families.count(family)} == {112, 112, 112}` derived from the fixture row count), along
  with the `len(families) == len(episodes)` alignment assertion. `_mix_adversarial` asserts the
  alignment a second time across the two independent public calls.
- **Commit:** `d274dfb`.

### 4. [Rule 3 — Blocking] `import random` added at `scripts/teach_persona.py` module scope

- **Found during:** Task 2. Stdlib, no graph consequence — `teach_persona` already imports eleven
  stdlib modules at scope and carries no import ceiling (the lazy-import rule binds
  `phase24_adversarial`, whose module-level imports were AST-verified still
  `['pathlib', 'phase14_factset', 'sys']`).
- **Commit:** `d274dfb`.

**Total deviations: 4.** No architectural change, no package installed, no checkpoint reached, no
authentication gate. Every planned artifact shipped as specified.

## Anchors, re-measured — every plan citation resolved

Unusually for this phase (hazard #5), **all fourteen of the plan's `<interfaces>` line numbers were
correct at pre-plan HEAD** — verified against `git show 0313305:scripts/teach_persona.py`, not
assumed. Positions after this plan's two commits, for the next reader:

| Anchor | Plan said | Pre-plan HEAD (`0313305`) | Now |
|---|---|---|---|
| `ARMS = (` | `:249` | `:249` ✓ | `:250` |
| `DP_ARMS = (` | `:270` | `:270` ✓ | `:286` |
| `def build_bins` | `:467` | `:467` ✓ | `:483` (10-line signature) |
| the bare `return {` in the stats block | `:512` | `:512` ✓ | `:571` (`    stats = {`) |
| `def _prove_floor_and_band` | `:528` | `:528` ✓ | `:605` |
| `def _refuse_ambiguous_aligned_input` | `:560` | `:560` ✓ | `:637` |
| `def _build_aligned_bins` | `:609` | `:609` ✓ | `:695` |
| `def _prepend_replay` | `:751` | `:751` ✓ | `:935` |
| `def _mix_adversarial` | — (new) | — | `:839` |
| `def sanity_check` | `:831` | `:831` ✓ | `:1015` |
| `def arm_spec` | `:882` | `:882` ✓ | `:1066` |
| `def build_arm_bins` | `:945` | `:945` ✓ | `:1144` |
| `USAGE = (` | `:1087` | `:1087` ✓ | `:1299` |
| `def train_arm` | `:1293` | `:1293` ✓ | `:1505` |
| the resume determinism f-string | `:1044-1045` | `:1044-1045` ✓ | `:1255-1256` |

`USAGE` needed no edit — it interpolates `'|'.join(ARMS)`, so both new arms appear in it
automatically, which `tests/test_phase22_wiring.py:586` re-proves.

The one line number this plan's own criteria cite is `scripts/teach_persona.py`'s `np.random`
COMMENT, quoted in Task 2 as the reason to use AST over grep. It was at `:537` when the plan was
written and is at **`:614`** now; the criterion does not depend on the number, only on the hit
existing, and it does — `grep -n "np.random" scripts/teach_persona.py` still returns exactly that
one comment line and nothing in `_mix_adversarial`.

## Verification Results

| Check | Result |
|---|---|
| `pytest -q tests/test_phase24_bins.py` (pre-wiring) | **10 failed, 0 passed** — the required RED |
| `pytest -q tests/test_phase24_bins.py` (post-wiring) | **10 passed**, 0 failed (1.89 s) |
| `pytest -q tests/test_phase21_aligned_bins.py` | **23 passed** — golden fixture and `test_align_facts_is_wired` both green |
| `pytest -q .../aligned_bins .../replay_volume .../scoring .../phase24_adversarial .../phase21_sc5` | **89 passed**, 0 failed |
| `pytest -q .../phase14_teaching .../phase22_wiring .../phase23_resume .../phase24_bins` | **86 passed**, 0 failed (111.8 s) |
| **Full suite** `.venv/bin/python -m pytest -q` | **1633 passed, 1 skipped, 0 failed** in 372.34 s |
| Baseline reconciliation | orchestrator-measured baseline **1619 passed / 1 skipped**; delta **+14 = 10** (this module) **+ 4** (`test_phase14_teaching.py`'s two `@parametrize("arm", tp.ARMS)` tests × 2 new arms). Fully accounted for; nothing else moved |
| `git diff tests/test_phase21_replay_volume.py` | **empty** — the D-06 tripwire is untouched |
| `git diff scripts/phase18_extraction.py scripts/mitigation_gate.py` | **empty** — both frozen modules unmoved |
| `git status --porcelain data/` | **empty** after the smoke |
| `inspect.signature(build_bins)`: `adversarial_ratio` | `0.0`, `KEYWORD_ONLY`; `seed` default `1337` |
| `inspect.signature(build_arm_bins/train_arm)`: `adversarial_ratio` | `KEYWORD_ONLY KEYWORD_ONLY` |
| AST over `_mix_adversarial`: `teaching_tokens` not a `Name`; no `np.random`; no `random.shuffle`/`seed`/`randint`/… | **ok** |
| AST over `_mix_adversarial`: `Random` present | **ok** — a private `random.Random(seed)` instance |
| AST: `phase24_adversarial` module-level imports | `['pathlib', 'phase14_factset', 'sys']` — the lazy-import boundary holds |
| `tp.ARMS[-2:]` / `tp.DP_ARMS` | `('adv_n8', 'adv_n64')` / `('dp_n8', 'dp_n64')` — both adversarial arms pack FLAT |
| `tp.arm_spec('adv_n8')[1:]` / `len(tp.arm_spec('adv_n64')[0])` | `(False, 0.0)` / `64` |
| Aligned + adversarial refusal, watched firing | `SystemExit: [teach_persona] build_bins got adversarial_ratio=0.25 alongside 8 align_facts pairs. …` |
| `tests/test_phase24_correction.py` after the ROADMAP edit | **4 passed** |
| `(?:==\|!=)\s*10(?![0-9_])` over lines added under `tests/` | **0 hits** — the twelve-member SC5 wall census stayed green with no edit |
| `ruff check .` / `ruff format --check .` | All checks passed; **227 files** already formatted |
| `.planning/REQUIREMENTS.md` | **byte-unchanged** — ADVT-01/02/03 all still deliberately unticked |

**No `gsd-sdk` mutation handler was called.** STATE.md and ROADMAP.md were hand-edited with
occurrence-counted replacements, matching all five prior plans in this phase (repo hazard #1).

### Method substitutions

The plan's own AST criteria were used verbatim and no `grep` criterion needed substituting this
time — Task 2's acceptance criteria already replaced them pre-emptively, correctly citing that
`grep -n "np.random"` returns a live hit today from a COMMENT at what is now
`scripts/teach_persona.py:614`. The one `grep` criterion in Task 3 (`grep -n "adversarial_ratio"`)
is a reachability listing rather than an absence claim, so prose cannot make it false-green; it was
run and cross-checked against `inspect.signature`.

## Requirements

**Neither ADVT-01 nor ADVT-03 is ticked, deliberately.**

- **ADVT-01** ("the adapter trained against the Phase 18 attack suite with attack intensity as a
  swept axis") — this plan builds the SEAM the sweep runs through; no adapter has been trained. Plan
  24-07 also carries ADVT-01, and Phase 25 runs the sweep.
- **ADVT-03** ("attack intensity disclosed as also a token-budget axis") — this plan MEASURES the
  scored-token counts per grid point (table above), but the committed per-arm record is 24-07's
  artifact. Reporting a number in a SUMMARY is not the same as committing the record the
  requirement names.

`.planning/REQUIREMENTS.md` is byte-unchanged, as it has been for the whole phase.

## Issues Encountered

None beyond the four deviations. The "expect an unnamed guard" warning did not materialise: every
guard that could have bitten (`tests/test_phase14_scoring.py`'s D-21 census, the SC5 wall census,
`tests/test_phase21_aligned_bins.py`'s `repr(stats)` golden pin, `tests/test_phase14_teaching.py`'s
`tp.ARMS` parametrization, `tests/test_phase22_wiring.py`'s `USAGE`/`ARMS` coupling) was anticipated
and stayed green with no edit. The only unlisted consequence was mechanical rather than adversarial:
appending two arms adds four parametrized items, which is why the suite delta is +14 and not +10.

## Known Stubs

None. Every declared name is implemented and consumed: `adversarial_ratio` by `_mix_adversarial` and
proved read by `test_adversarial_ratio_is_wired`; `seed` by the permutation and proved read in three
directions; `adversarial_episode_families` by `_mix_adversarial` and the per-grid-point family
assertion; all nine additive stats keys populated and five of them asserted in tests; both new arms
resolved by `arm_spec` and `adv_n8` exercised end to end.

## Threat Flags

None. No new network endpoint, auth path or schema at a trust boundary. All eight registered
mitigations are in place and each is backed by a measurement above:

| Threat | Status |
|---|---|
| T-24-30 vacuous byte-identity guard | `test_adversarial_ratio_is_wired` written FIRST, watched RED, output quoted |
| T-24-31 `repr(stats)` golden fixture | nine additive keys only under `if adversarial_ratio > 0`; `test_build_bins_byte_identity_default_matches_the_v2_golden` green |
| T-24-32 resume corpus identity | `random.Random(seed)`, proved in three directions; `tests/test_phase23_resume.py` green; the determinism tuple now names `adversarial_ratio` |
| T-24-33 D-06 side channel | `n_want` from `len(episodes)`; AST proves `teaching_tokens` is not read in `_mix_adversarial`; the token-total-varying test green; `test_replay_constant_is_not_derived_from_the_corpus` untouched |
| T-24-34 packer-by-arm-name | `adv_*` appended outside `DP_ARMS` with the closed-2-tuple rule in comment; `_refuse_ambiguous_aligned_input` widened and watched firing |
| T-24-35 build-time band `SystemExit` | not tripped at any grid point (0.2410–0.3008 against a 0.15 floor); the per-episode min of 0.1111 recorded above for 24-07 |
| T-24-36 held-out questions in the teaching bin | `sanity_check` proof 6 passed on the real `adv_n8` build — 130 held-out questions, none present at token level |
| T-24-37 hardcoded empty persona | the clean loop still passes `[]` and is byte-identical; only adversarial episodes carry a persona, at mask=0 |
| T-24-SC package installs | none |

## Next Phase Readiness

Ready for **wave 4 (24-07)**:

- `build_bins(..., adversarial_ratio=r, seed=s)` returns the nine additive keys 24-07's band check
  and ADVT-03 record read: `adversarial_ratio`, `clean_episodes`, `adversarial_episodes`,
  `adversarial_pool_size`, `adversarial_multiplicity`, `adversarial_family_counts`,
  `adversarial_tokens`, `adversarial_scored_tokens`, `adversarial_permutation_seed`.
- The four corners 24-07 checks are `{adv_n8, adv_n64} × {0.0, 1.9090909090909092}`. The n=8 column
  is measured above (0.3586 clean → 0.2410 at the extreme); **the n=64 column is unmeasured** — do
  not carry the n=8 figures across.
- `stats["episodes"]` is OVERRIDDEN on the non-zero branch to clean + adversarial (512 at the n=8
  upper extreme). `stats["teaching_tokens"]` remains CLEAN-ONLY by design; the adversarial token
  total is a separate key.
- Neither `adv_n8` nor `adv_n64` is in `DP_ARMS`, so `arm_bin_targets` returns TWO paths for them,
  not three — no `*_fact.bin` exists for an adversarial arm.
- `_mix_adversarial` refuses a non-zero ratio that rounds to zero episodes, naming the smallest
  ratio that would place one (`0.5 / n_clean`). At n=64 (1,408 clean episodes) that bound is
  ~0.000355, so no pinned grid point is near it.

---
*Phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa, Plan 06*
*Completed: 2026-08-30*

## Self-Check: PASSED

All four artifact paths exist on disk (`tests/test_phase24_bins.py`, `scripts/teach_persona.py`,
`scripts/phase24_adversarial.py`, this SUMMARY); both task commits (`d274dfb`, `75d2d6d`) are
present in `git log --all`; every line number in the anchor table was measured at HEAD and at
`0313305` this session rather than carried from the plan; and `.planning/STATE.md`'s diff was read
line by line — exactly **6 deletions**, all intended (`stopped_at`, `last_updated`,
`completed_plans`, the position line, `Last session`, `Stopped at`), no collateral prose damage.
