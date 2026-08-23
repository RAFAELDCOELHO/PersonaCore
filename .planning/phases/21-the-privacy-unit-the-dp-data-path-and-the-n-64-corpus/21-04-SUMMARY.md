---
phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
plan: 04
subsystem: aligned-bins
tags: [unit-02, d-01, d-05, d-06, byte-identity, ragged-packing, wave-2, t-21-20, t-21-21, t-21-59, t-21-60, t-21-22, t-21-23]
requires:
  - "21-02 — tests/fixtures/golden_build_bins_v2.json, the v2.0 pre-edit byte-level baseline"
provides:
  - "personacore.training.data.fact_window_impurities(fact_ids, block_size, *, space='input') — the ONE purity predicate, shared by the packer, the loader (21-06) and the tests"
  - "scripts/teach_persona.py::fact_bin_path(bin_path) — the third bin's path, DERIVED; no consumer may use a string literal"
  - "scripts/teach_persona.py::build_bins(..., align_facts=None) — the RAGGED fact-aligned packer, proof-1 over three files, proof-7 in both spaces"
  - "tests/test_phase21_aligned_bins.py — A0-A5 adversaries, the byte-identity pair, three-bin 1:1"
  - "The PINNED align_facts shape: a list of (fact, already-rendered episodes) PAIRS — inherited by 21-06, 21-10, 21-11"
affects:
  - "21-06 — the loader consumes fact_bin_path() and calls fact_window_impurities(..., space='input') at run time"
  - "21-10 / 21-11 — the drivers build with align_facts=[(f, render_episodes([f], ...)) for f in facts] and episodes=[]"
tech-stack:
  added: []
  patterns:
    - "One purity predicate, three consumers (packer / loader / tests) — a second copy is a second thing to keep in agreement, so there is none"
    - "Proofs read BYTES BACK FROM DISK with np.fromfile, never the packer's own arithmetic: a check that re-derives boundaries from the same cumulative lengths the packer used shares the packer's defect"
    - "A byte-identity assertion with no paired NON-identity assertion is vacuous — every identity test here is half a pair"
    - "The target-space boundary is stated as a POSITIVE counted claim (exactly n_facts-1, each masked, each in fact order), never waived as an inequality"
key-files:
  created:
    - "tests/test_phase21_aligned_bins.py"
    - ".planning/phases/21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus/21-04-SUMMARY.md"
  modified:
    - "src/personacore/training/data.py"
    - "scripts/teach_persona.py"
decisions:
  - "space='input' is the DEFAULT and there is no union mode. On a CORRECTLY built bin target space returns exactly n_facts-1 rows, never [] — so a union default would abort every aligned build at proof-7. Measured on the real 8-fact geometry: input [], target [3,7,11,15,19,24,28]"
  - "Proofs 2 and 3 were extracted into _prove_floor_and_band and are called by BOTH branches. Two copies of a guard drift; the extraction is proven byte-neutral by the golden digest match rather than argued"
  - "The aligned branch also REFUSES a non-zero replay_ratio, which the plan did not specify. D-09/D-10 put replay outside the teaching bin; silently ignoring the kwarg would give the caller a bin they believe has replay and falsify grad_accum_steps = n_facts by ~7.9x"
  - "align_facts pair validation accepts tuple OR list. The load-bearing discrimination is 'length-2 with an .id on the first member', which still rejects the bare-Fact-objects error the plan names"
metrics:
  duration: "~50 min"
  tasks_completed: 3
---

# Phase 21 Plan 04: The Fact-Aligned Bin Path Summary

`build_bins(..., align_facts=None)` is byte-identical to v2.0 against 21-02's committed sha256,
and the aligned branch packs 8 facts into 33 ragged windows where no `block_size`-aligned window
carries two fact shards — proven by reading bytes back from disk, not inferred from offsets.

## The Central Claim, Proven Rather Than Argued

The plan named this the thing most likely to be quietly wrong. It was checked with a digest
comparison, not by reading the diff:

| Field | Golden (21-02) | Rebuilt with `align_facts=None` |
|---|---|---|
| `token_bin_sha256` | `91c2549388079c3da2d5888706ba6b80f70383f320112ae768f6a78372f90fac` | identical |
| `mask_bin_sha256` | `4a674423ec9412fc6a302adcc419faa98d78a1e8b8c00107b13aeb864c15061f` | identical |
| `token_bin_bytes` | 20,036 | identical |
| `mask_bin_bytes` | 10,018 | identical |
| `stats_repr` | 12 keys, 220 episodes / 10,018 tokens | identical |

This also proves the `_prove_floor_and_band` extraction byte-neutral. That refactor was the one
structural change to the default path, and the fixture is exactly the instrument that settles
whether it moved a byte. It did not.

## D-01's Geometry, Observed

Nothing was adjusted to hit a target. Every number below is what the packer produced on the
first run, at `BLOCK_SIZE = 256` over `fs.LOCKED_FACTS` through `fs.TAUGHT_FAMILY_IDS`:

| Quantity | D-01 predicted | Observed |
|---|---|---|
| `windows_per_fact` | `(4,4,4,4,4,5,4,4)` | `(4,4,4,4,4,5,4,4)` ✓ |
| `n_windows` | 33 | 33 ✓ |
| `pad_tokens` | 867 | 867 ✓ |
| teaching tokens | 7,581 | 7,581 ✓ |
| rendered rows | 176 | 176 ✓ |
| total elements | — | 8,449 = 33 × 256 + 1 ✓ |

`7,581 + 867 = 8,448 = 33 × 256`, plus the one-element label-shift tail.

## Proof 7, Both Spaces, On The Real Bin

Read back with `np.fromfile`, asserted from outside the packer:

| Claim | Observed |
|---|---|
| INPUT space impurities (**this is SC2**) | `[]` |
| TARGET space boundary rows | `[3, 7, 11, 15, 19, 24, 28]` — **7 = `n_facts - 1`** |
| mask at every boundary token | `[0, 0, 0, 0, 0, 0, 0]` — all masked |
| fact id across every boundary | `(0,1) (1,2) (2,3) (3,4) (4,5) (5,6) (6,7)` — every one `own_id + 1` |

This reproduces the carry-forward's measured prediction exactly. **Proof-7 did not redden, so
nothing had to be reported as a finding and nothing was loosened.** The `space="input"` default
is unchanged.

## The Two Deliberate-REDs

### RED 1 — the A0-A5 parametrization discriminates

Mutation: `np.unique(r).size != 1` → `len(r) != block_size` in `fact_window_impurities`.

```
assert [] == [0, 2, 3]   # A1-roll
assert [] == [1]         # A2-interior
assert [] == [1]         # A3-padding
assert [] == [1, 2]      # target-space boundary rows
```

A0 and A5 stayed GREEN, so the assertion is not universally true.
Restore sha256 `fbf9bdaa79a5b281dbc6877cc4a9db1f160f62045b87d73dd3737f5768db2d57`,
equal to the pre-mutation value.

### RED 2 — the golden guard, watched going red on one element

Mutation: one extra pad element into the `align_facts=None` branch's `ids_all` / `mask_all`.

```
assert '7d6486c983fb0bbb3aa6688a1ddd0cb57d5482d67323b134dd8b6cf994223998'
    == '91c2549388079c3da2d5888706ba6b80f70383f320112ae768f6a78372f90fac'
```

Byte counts under the mutation, measured separately because assertion order means only the
first fires: token 20,038 vs 20,036; mask 10,019 vs 10,018; `stats_repr` unequal.

`test_build_bins_byte_identity_omitted_equals_align_facts_none` **stayed GREEN** — recorded
because it is informative: an omitted-equals-None test cannot see a change that moves BOTH
branches, which is exactly why the golden fixture is the second tier.

Restore sha256 `200233c8366c7626ec2af29685796415e9592e4a5b85b336a2ff297930aacfa6`,
equal to the pre-mutation value; `git diff --exit-code scripts/teach_persona.py` returns 0.

## Plan vs Code Fidelity

Every `<interfaces>` line anchor in this plan verified against the source, unlike 21-03's:
`teach_persona.py` `:100` `:197` `:256` `:312`, `data.py` `:112-116` `:125`,
`serialize.py:81`, `gpt.py:212`. **Zero stale anchors.** Recorded because this phase has
measured the opposite twice (21-01 falsified three of its own claims, 21-03 four).

Four plan/reality mismatches, reported rather than silently adapted:

**1. The carry-forward's `meta.order` / `meta.serialization` instruction does not apply to this
fixture.** `golden_build_bins_v2.json` has NEITHER field — those are on
`golden_render_family_v2.json`, which is 21-05's. The build fixture carries `meta.recipe`
instead, naming the exact call. No order had to be guessed: `render_episodes:251` applies
`sorted(family_ids)`, which 21-02 measured stable across four `PYTHONHASHSEED` values. The
test resolves facts BY ID from `meta.facts` and asserts the resolved list still equals
`LOCKED_FACTS + SOFT_TIER_FACTS`, so a drift in either is a named finding.

**2. The task-1 acceptance criterion's restore step is ordered wrong, and it destroyed work.**
It says *"Restore with `git checkout src/personacore/training/data.py`"* — but at that point in
the plan's own sequence the GREEN implementation is not yet committed, so `git checkout` reverts
to HEAD and deletes it. That is what happened; the implementation was re-applied from context and
verified sha256-equal, then committed BEFORE the second deliberate-RED. **A restore-by-checkout
step is only valid after the GREEN commit.** Plans 21-05 and later should order it that way.

**3. RED 1 reddens three parametrizations, not two.** The plan predicts *"A1 and A2 must return
`[]` (RED on two of six parametrizations)"*. Observed: A1, A2 **and A3** redden, plus the
separate target-space test. A3 is the padding-labelling error and it discriminates on exactly
the same mechanism — the plan under-counted its own adversary set. The parametrization also
holds five cases, not six: A4 raises rather than returning, so it is a separate test.

**4. `replay_ratio` on the aligned branch is unspecified by the plan.** Added a refusal — see
Deviations.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — Missing critical functionality] The aligned branch refuses a non-zero `replay_ratio`**

- **Found during:** Task 2
- **Issue:** The plan pins `episodes` on the aligned branch and raises on a non-empty value, but
  says nothing about `replay_ratio`. The aligned path does not consume it, so it would have been
  silently ignored — the caller gets a bin they believe carries replay and does not.
- **Why critical:** D-09 measured 7,581 replay tokens ≈ 30 windows against 33 fact windows, so a
  silently-baked-in replay makes `grad_accum_steps = 63` rather than 8 — falsifying SC2's
  `grad_accum_steps = n_facts` by ~7.9×. D-10 puts replay outside the teaching bin entirely.
- **Fix:** a named `SystemExit` naming the ratio, the pair count and the D-09/D-10 reason.
- **Files modified:** `scripts/teach_persona.py`
- **Commit:** `c382ecb`

**2. [Rule 2 — Missing critical functionality] A fact with zero rendered episodes is refused**

- **Found during:** Task 2
- **Issue:** A pair whose episode list is empty packs to zero windows, so its privacy record
  exists in the accounting (`n_facts`) and nowhere in the bin. It would also make `min(lengths)`
  raise on an all-empty input.
- **Fix:** a named `SystemExit` naming the index and the fact id.
- **Commit:** `c382ecb`

**3. [Rule 3 — Blocking] `_prove_floor_and_band` extracted from `build_bins`**

- **Found during:** Task 2
- **Issue:** The aligned branch needs proofs 2 and 3, which lived inline in `build_bins`.
  Duplicating them would put two copies of a guard in one file.
- **Fix:** extracted to one function, called by both branches. The plan's "do not restructure"
  clause names the shard loop, the `np.concatenate` order and the stats dict — all untouched.
  Byte-neutrality is **proven** by the golden digest match, not asserted.
- **Commit:** `c382ecb`

## Verification

| Check | Result |
|---|---|
| `pytest -q tests/test_phase21_aligned_bins.py tests/test_masked_batch.py tests/test_phase14_teaching.py tests/test_package.py` | **61 passed** |
| Full suite | **900 passed, 7 skipped**, 1 failed |
| The 1 failure | `test_phase18_docs.py::test_no_bare_zero_percent_in_docs` — PRE-EXISTING at base `7ca8945`, from README commit `9cc2c94`; orchestrator-owned, untouched |
| `git diff --exit-code` on the 4 frozen pins | 0 — `mitigation_gate.py`, `mitigation_unit.py`, `phase18_extraction.py`, `phase14_factset.py` byte-unchanged |
| `git status --porcelain data/` | empty — no test wrote into recorded evidence |
| `git ls-files 'results/phase21_*'` | empty |
| `ruff check . && ruff format --check .` | All checks passed, 180 files formatted |
| `.planning/STATE.md` / `ROADMAP.md` | byte-unchanged (worktree mode) |

`21-VALIDATION.md`'s six `-k` selectors for this plan all select and pass: `byte_identity` (2),
`align_facts_is_wired` (1), `window_purity_input` (1), `window_purity_target` (1),
`window_purity_adversaries` (6), `three_bin_alignment` (2).

## Known Stubs

None. Every function this plan adds is fully implemented and exercised against the real
8-fact geometry, not a placeholder.

## Threat Flags

None. This plan adds no network endpoint, no auth path and no new file-access pattern: it writes
one additional bin beside two the same function already wrote, under paths the caller supplies.

## Commits

| Commit | Task | Content |
|---|---|---|
| `a3fe2ab` | 1 (RED) | A0-A5 adversaries on hand-written literals — ImportError |
| `48eca7a` | 1 (GREEN) | `fact_window_impurities`, input-space default, no union mode |
| `c382ecb` | 2 | `fact_bin_path`, the ragged packer, proof-1 over three files, proof-7 both spaces |
| `0964841` | 3 | the byte-identity pair, non-vacuity, three-bin 1:1, truncation in both spaces |

## Self-Check: PASSED

All three claimed source files exist on disk; all four commits present in
`git log 7ca8945..HEAD`; working tree clean before this SUMMARY; `.planning/STATE.md` and
`.planning/ROADMAP.md` untouched as required in worktree mode.
