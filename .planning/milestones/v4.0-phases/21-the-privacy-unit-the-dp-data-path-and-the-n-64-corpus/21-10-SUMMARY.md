---
phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
plan: 10
subsystem: multiplicity-instrument
tags: [unit-03, d-26, attribution-rule, instrument-validation, wave-4, t-21-10, t-21-44, t-21-45, t-21-46, t-21-47, t-21-63, t-21-65, t-21-48, t-21-64]
requires:
  - "21-06 — get_batch_fact_aligned and the EXPORTED fact_window_span, which count_aligned calls rather than re-implementing"
  - "21-04 — fact_window_impurities(space='input'), teach_persona.fact_bin_path(), the ragged aligned packer and tests/test_phase21_aligned_bins.py's corpus builder"
  - "21-01 — scripts/mitigation_unit.py's PRIVACY_UNIT_ARITHMETIC, the analytic figure this instrument is reconciled against"
provides:
  - "scripts/phase21_unit_record.py::ATTRIBUTION_RULE = 'first-token-owns-draw' — 21-RESEARCH Open Question 2, RESOLVED"
  - "scripts/phase21_unit_record.py::count_unaligned(...) -> row — the real random-window path, instrumented by wrapping np.random.randint around get_batch_memmap_masked"
  - "scripts/phase21_unit_record.py::count_aligned(..., strict=True) -> row — per-step counts plus per_step_distinct_facts / per_step_raised"
  - "scripts/phase21_unit_record.py::ARTIFACTS, BIN_COMPOSITION_LABELS, ROW_SCHEMA, refuse_existing_artifacts"
  - "tests/test_phase21_multiplicity.py — 17 tests: conservation, seeded reproduction, the row schema, non-vacuity, four independent oracles, the analytic cross-check, the artifact-ordering guard"
affects:
  - "21-11 — resolves both artifact paths from ARTIFACTS, calls count_aligned at the strict=True DEFAULT, and inherits refuse_existing_artifacts. It is the ONLY plan permitted to commit results/phase21_*"
  - "Phase 22 DPSGD-01 — the row schema (with its label and denominators) is the shape any published epsilon's multiplicity input takes"
tech-stack:
  added: []
  patterns:
    - "An instrument is validated against inputs whose TRUE answer is known INDEPENDENTLY of it — hand-counted degenerate cases, an exact replay of the seeded draw, and a corpus where a WRONG rule provably answers differently. Validating only against the real corpus, where the true answer is whatever the instrument says, is not validation"
    - "The TEST may re-derive the draw; the INSTRUMENT may not. Agreement between an observation of the real call and an independent re-derivation is evidence; agreement between two copies of a re-derivation is not"
    - "A wrong answer is COMPUTED and shown not to be the one produced, never described in prose"
    - "counts is seeded with every fact id before any draw, so an undrawn fact reports 0 rather than vanishing from min/spread"
key-files:
  created:
    - "scripts/phase21_unit_record.py"
    - "tests/test_phase21_multiplicity.py"
    - ".planning/phases/21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus/21-10-SUMMARY.md"
  modified: []
decisions:
  - "ATTRIBUTION_RULE = 'first-token-owns-draw'. Its cost is stated in the module rather than discovered later: the conservation law pins the per-fact MEAN at total_draws / n_facts by arithmetic, so the mean carries NO information about the corpus and everything the measurement says lives in min/max/spread. That is why D-26 asks for min/max/mean/spread and not an expectation."
  - "bin_composition is a REQUIRED keyword argument on BOTH counters, with no default. D-26 makes the label part of the row; a default would let the one field that disambiguates which bin was measured go quietly missing. Membership in BIN_COMPOSITION_LABELS is NOT enforced, because a synthetic validation fixture legitimately carries its own descriptive label — the three PUBLISHED literals are the constant, and 21-11 passes one of them."
  - "count_unaligned asserts the token bin and the fact map are 1:1 before counting. get_batch_memmap_masked checks token-vs-mask and knows nothing about a third file, so the token-vs-fact half is checked here or nowhere — and a skew there does not raise, it MIS-ATTRIBUTES."
  - "The analytic cross-check's band is centred on the CLOSED-FORM p = 2048/3839 = 0.5335, not on n/2. The naive n/2 sits 2.7 sigma below the true expectation and still falls inside a 4-sigma band, so a test written against n/2 would pass for the wrong reason."
metrics:
  duration: "~1h"
  tasks_completed: 3
  completed: 2026-08-23
---

# Phase 21 Plan 10: The Multiplicity Instrument Summary

`scripts/phase21_unit_record.py` counts per-fact draw multiplicity on both paths, and the
instrument itself has been shown counting — against hand-counted cases, an exact independent
replay of the seeded draw, and a corpus where a wrong attribution rule provably answers
differently.

## THE CENTRAL FINDING: 262.9437 is the REJECTED rule's number

**Reported, not tuned away.** The frozen pin's analytic figure and this instrument's measurement
disagree, and the disagreement is not noise — it is a different quantity.

`scripts/mitigation_unit.py`'s `PRIVACY_UNIT_ARITHMETIC` reads
`1,600 * (947.625 + 256) / (7,581 - 256 - 1) = 262.94`. That `+ 256` in the numerator is the count
of start offsets from which a `block_size` window **TOUCHES** a fact — it is the *overlap*
expectation, i.e. **the "credit every overlapped fact" rule, which is exactly the alternative this
plan's `ATTRIBUTION_RULE` rejects** (21-10-PLAN's own rule table, second row). Under the pinned
`first-token-owns-draw`, the same geometry gives:

| quantity | value | route |
|---|---|---|
| frozen pin's formula | **262.9437** | `1600 * (947.625 + 256) / 7324` — the OVERLAP rule |
| the reading the pin rejects | 54.0298 | `1600 * 256 / 7581` — wrong denominator AND wrong numerator |
| first-token at the mean fact length | **207.018** | `1600 * 947.625 / 7324` |
| gap, per interior fact | **55.9257** | `1600 * 256 / 7324` — exactly the `+ 256` |
| **conservation-pinned mean** | **200.0** | `total_draws / n_facts`, by arithmetic |

`262.9437 - 55.9257 = 207.018` — the two figures reconcile exactly, so neither is wrong. They
answer different questions, and **a row that does not name its rule is unreadable**, which is
precisely why `ATTRIBUTION_RULE` is now a module constant carried in every row.

The sharper consequence, and it changes what 21-11 can publish: **under the pinned rule the mean
is pinned at `total_draws / n_facts` and therefore carries no information about the corpus.** A
published "mean multiplicity of 200" would be a restatement of `1600 / 8`. Everything the
measurement actually says lives in `min` / `max` / `spread` — which is what D-26 asked for and
what a reader quoting a mean would miss.

## The measurement, on D-10's real geometry

Per-fact teaching-token lengths taken from the **real flat packer**, one build per fact, and
verified two ways before use: they sum to **7,581** (D-10's teaching-token total) and their window
ceilings are **`(4,4,4,4,4,5,4,4)`** — D-01's measured `windows_per_fact`, recovered from a
completely different route. Lengths `[892, 867, 897, 1022, 916, 1041, 976, 970]`.

At `SEED = 1337`, `MAX_STEPS = 200`, `BATCH_SIZE = 8`, `block_size = 256`, label
`facts-only (D-10)`:

| fact | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| **measured** | 210 | 197 | 203 | 221 | 180 | 229 | 217 | **143** |
| E[first-token] | 194.87 | 189.40 | 195.96 | 223.27 | 200.11 | 227.42 | 213.22 | 155.76 |
| z | +1.16 | +0.59 | +0.54 | −0.16 | −1.52 | +0.11 | +0.28 | −1.08 |

`min 143 · max 229 · mean 200.0 · spread 86`, `sum = 1600` exactly, support = **7,324** start
offsets (`7581 − 256 − 1`), not 7,581. Every fact lands within **±1.6 sigma** of the closed-form
first-token expectation computed independently of the counter — the instrument recovers the
analytic answer on the real geometry without having been fitted to it.

Fact 7's 143 is not an anomaly: it is the LAST fact, so the final `block_size + 1` tokens can never
be a window start and it owns **713** of its 970 tokens as reachable offsets. That asymmetry is a
real property of the old loader and it is visible only because `counts` is seeded with every fact
before any draw.

**This measurement is NOT committed.** `git ls-files 'results/phase21_*'` is empty; it was taken in
a scratch process and is recorded here. Plan 21-11 owns the first add, irrevocably (`adds[-1]`).

## The instrument has been shown reporting a value other than 1

Every measured prediction in the plan's task-3 text held **exactly** — the first plan in this phase
whose adversary arithmetic needed no correction.

Rolled-bin window owners, measured:
`[7, 0,0,0,0, 1,1,1,1, 2,2,2,2, 3,3,3,3, 4,4,4,4, 5,5,5,5,5, 6,6,6,6, 7,7,7]` — identical to the
plan's prediction, including fact 7 owning **non-contiguous rows `[0, 30, 31, 32]`**.

| arm (`strict=False`, a FULL LOT of 8 steps) | `per_step_distinct_facts` | `per_step_raised` |
|---|---|---|
| **mis-built** (A1 roll at `block_size = 256`) | `[2, 2, 2, 2, 2, 2, 2, None]` | `['loader'] * 7 + ['span']` |
| **correct** (negative control, SAME call) | `[1, 1, 1, 1, 1, 1, 1, 1]` | `[None] * 8` |

All 8 steps raise on the rolled bin — the loader on impurity at steps 0-6, `fact_window_span` on
non-contiguity at step 7 — which is why **both** calls sit inside one `try/except` and why
`np.unique` runs strictly before the loader call. A `steps < n_facts` run never reaches step 7 and
would pass over a counter that aborts there; the lot length is asserted in the test body, not left
to the parametrize table. Input-space impurities on the rolled bin: `[0, 4, 8, 12, 16, 20, 25, 29]`
(asserted first, at the `space="input"` DEFAULT); target space: `[]` — a roll is invisible there,
which is the second reason a target-space assertion here would have passed for the wrong reason.

The correct bin also returns normally at the `strict=True` **default**, and the default **aborts**
on the mis-built bin. `strict=False` is a test affordance and appears in no other test.

## The instrumentation routes, and what each one rejected

| path | route TAKEN | route REJECTED, and why |
|---|---|---|
| unaligned | wrap `np.random.randint` around the real `get_batch_memmap_masked`, asserting the wrapper saw exactly `steps` calls of size `batch_size` | (a) re-deriving the indices by re-seeding — that measures a RE-IMPLEMENTATION of the draw and would pass unchanged if the loader stopped drawing; (b) a `return_indices=None` kwarg on `get_batch_memmap_masked` — a fourth additive default-`None` kwarg with no is-wired pair, the exact defect class this phase exists to eliminate, and it would break 21-06's byte-unchanged criterion |
| aligned | `fact_window_span`, the function the LOADER ITSELF draws through, exported by 21-06 for this | counting distinct ids from the windows the loader returns — **impossible**: it raises before returning on exactly the bins the non-vacuity test needs, and returns `(x, y, fact_index)` with no fact ids at all |

The call-count assertion is not decoration. `test_the_wrapper_call_count_is_asserted_not_assumed`
stands in a loader that never draws and the instrument **refuses to return a row**. The
conservation law alone cannot catch that: it balances against the draws the wrapper *did* see.

## The deliberate-RED, watched

Mutation: credit **every** overlapped fact in `count_unaligned` — i.e. switch to the rejected rule.

```
AssertionError: the counts sum to 1993 against a budget of 200 x 8 = 1600 under
ATTRIBUTION_RULE='first-token-owns-draw'. Over-count means a draw was credited to more than one
fact (the REJECTED rule); under-count means a draw was dropped.
  where 1993 = sum(dict_values([226, 268, 276, 264, 240, 267, 263, 189]))
8 failed, 4 passed
```

**Which four stayed GREEN is the informative part:**

| test | under the mutation | what that records |
|---|---|---|
| `test_conservation` ×3, `..._real_budget_denominator` | **RED** | the load-bearing law works, and it is an equality with nothing to tune |
| `test_seed_reproducible` | **RED** | — |
| `test_oracle_exact_replay_of_the_draw` | **RED** | the independent oracle discriminates |
| `test_oracle_an_undrawable_fact_counts_zero` | **RED** | — |
| `test_oracle_a_wrong_attribution_rule_gives_a_different_answer` | **RED** | it caught the instrument answering `{0: 25, 1: 480}` against the first-token `{0: 25, 1: 455}` |
| `test_oracle_one_fact_takes_every_draw` | GREEN | **a degenerate case CANNOT separate the two rules** — with one fact they coincide. This is why the discriminating corpus exists and why degenerate cases alone would be a false comfort |
| `test_aligned_conservation`, `test_row_carries_its_denominator` | GREEN | correctly insensitive: the mutation is in `count_unaligned`, and the schema is unchanged |
| `test_the_wrapper_call_count_is_asserted_not_assumed` | GREEN | same |

Restore sha256 `986cd7eea07d6ab07b77f20f6499cbb2aaf2e57b2dd6c59f8c894c511da172e7`, equal to the
pre-mutation value; `git diff --exit-code scripts/phase21_unit_record.py` returns 0. **The restore
was ordered AFTER the GREEN commit** — 21-01 and 21-04 both lost work to a `git checkout` inside an
uncommitted RED cycle, and 21-06 recorded the correction.

## The four independent oracles

The prompt's requirement, and the plan's weakest point as written: an instrument validated only
against the real corpus is validated against whatever it says.

| oracle | how the true answer is known WITHOUT the instrument |
|---|---|
| `test_oracle_exact_replay_of_the_draw` | the seeded start offsets replayed **in the test** and attributed by hand — EXACT, no interval. The route the instrument refuses is legitimate as a test oracle precisely because the instrument does not use it |
| `test_oracle_one_fact_takes_every_draw` | hand-counted: one fact owns the corpus, so it owns all 240 draws, `spread == 0` |
| `test_oracle_an_undrawable_fact_counts_zero` | hand-counted: a fact living entirely in the last `block_size + 1` elements can never be a window start. `counts == {0: 400, 1: 0}`, `min == 0`. Separates a counter that summarises EVERY fact from one that summarises only the facts it observed — the latter reports a flattering `min` and understates the spread |
| `test_oracle_a_wrong_attribution_rule_gives_a_different_answer` | fact 0 owns exactly the first `block_size` tokens, so first-token and last-token attribution differ **by construction**. Both wrong answers (last-token, mid-token) are COMPUTED and shown not to be the one produced, and the rejected overlap rule is shown overshooting the budget on the same corpus |

## Plan vs Code Fidelity

Five mismatches, reported rather than silently adapted. The historical PLAN.md was **not** amended.

**1. Every `teach_persona.py` line anchor in `<interfaces>` is stale; every `data.py` anchor is
correct.** The plan's own paragraph predicted this ("resolve BY SYMBOL after waves 2 and 3 land"),
so this is the warning working, not a defect — recorded because the phase has measured both
outcomes.

| symbol | plan says | measured |
|---|---|---|
| `SEED` | `:99` | **`:102`** |
| `BLOCK_SIZE` | `:100` | **`:103`** |
| `refuse_if_exists` | `:236` | **`:311`** |
| `BATCH_SIZE` | `:517` | **`:853`** |
| `MAX_STEPS` | `:523` | **`:859`** |
| `WARMUP_STEPS` | `:524` | **`:860`** |
| `get_batch_memmap_masked` | `data.py:93` | `:93` ✓ |
| `np.random.randint` draw | `data.py:117` | `:117` ✓ |

Everything was resolved by symbol; nothing was written against a line number.

**2. The task-1 acceptance criterion `sorted(r.ARTIFACTS)` prints KEYS, not paths.** `ARTIFACTS` is
a dict keyed by semantic name (`"privacy_unit"`, `"multiplicity"`) so 21-11 can write
`ARTIFACTS["multiplicity"]` rather than index a path string. `len(ARTIFACTS) == 2` and both paths
are asserted in `test_the_artifact_is_not_written_yet`; the paths print via
`sorted(str(p) for p in r.ARTIFACTS.values())`. Satisfied in substance, not verbatim.

**3. The plan's `count_unaligned` / `count_aligned` signatures omit the bin-composition label that
its own `must_haves` require.** Truth 6 says *"Every row carries its denominator: bin composition
label, ..."*, but neither signature accepts one. Resolved as a Rule-2 addition (below) rather than
by dropping the requirement.

**4. `test_analytic_cross_check_only`'s stated centre is wrong.** The plan says the two counts must
lie "within a STATED binomial interval of `n/2`". With two facts of exactly equal length,
`p(fact 0) = 2048 / 3839 = 0.5335`, not `0.5`, because the last `block_size + 1` offsets are
unreachable. At 1,600 draws `n/2 = 800` sits **2.68 sigma** below the true expectation of 853.56 —
and still **inside** a 4-sigma band, so a test written against `n/2` would have passed *for the
wrong reason*. The band is centred on the closed form and the gap is asserted (`> 2 sigma` and
`< band`) so the finding cannot go stale silently. Same denominator confusion, one layer down, as
the 54.03-vs-262.94 problem 21-01 had to freeze a formula to settle.

**5. `21-VALIDATION.md`'s full-suite figures are stale, in two ways.** `:30`/`:52` state
`877 passed, 1 skipped`; measured here **955 passed, 7 skipped** (see Verification for the
reconciliation). And `:32` names `test_loop_penalty_fn::test_golden_trajectory_bit_identity` as
"the one skip" — measured, that test does **not** skip at all; the platform-gated skip is
`tests/test_train_loop.py:81` (`fp16 AMP smoke needs a CUDA GPU`). Neither file is this plan's to
edit; both are recorded so the next reader does not chase them.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — Missing critical functionality] `bin_composition` is a REQUIRED keyword argument on
both counters**

- **Found during:** Task 1
- **Issue:** The plan's signatures accept no label, but its own `must_haves` truth 6 and D-26 both
  require every row to carry its bin composition. Without it the row cannot say which of the three
  compositions was measured — which is the exact ambiguity D-26 exists to close, since SC3's
  phrasing ("at the chosen `replay_ratio`") predates D-10 moving replay out of the bin entirely.
- **Fix:** keyword-only, no default, on `count_unaligned` and `count_aligned`; the three published
  literals stay in `BIN_COMPOSITION_LABELS`. Membership is deliberately not enforced — a synthetic
  validation fixture carries its own descriptive label, and forcing it to claim a published one
  would be dishonest.
- **Commit:** `280e2c1`

**2. [Rule 2 — Missing critical functionality] The token bin and the fact map are asserted 1:1
before any counting**

- **Found during:** Task 1
- **Issue:** `count_unaligned` attributes a draw by `fact_ids[start]`. `get_batch_memmap_masked`
  checks token-vs-mask (T-11-04) and knows nothing about a third file, so a token/fact length skew
  is checked here or nowhere — and it does not raise, it **MIS-ATTRIBUTES**, producing a row that
  looks fine. `get_batch_fact_aligned` refuses the same skew across three bins (D-06 proof 1); the
  unaligned counter had no equivalent.
- **Fix:** `_read_fact_map` raises naming both lengths and both paths, before any draw.
- **Commit:** `280e2c1`

**3. [Rule 2 — Missing critical functionality] `counts` is seeded with every fact id before any
draw**

- **Found during:** Task 1
- **Issue:** A counter that only records facts it observed drops an undrawn fact from the row
  entirely, so `min` is the smallest NON-ZERO count and `spread` is understated — both in the
  flattering direction, on the number a published epsilon rests on. It is not hypothetical: fact 7
  of the real D-10 geometry loses 257 of its 970 tokens to the unreachable tail, and a fact packed
  wholly inside that tail counts zero.
- **Fix:** `counts` is initialised from `np.unique(fact_ids)` (unaligned) / `range(n_facts)`
  (aligned). `test_oracle_an_undrawable_fact_counts_zero` is the guard, and it asserts
  `n_facts == 2` explicitly so a vanished fact fails loudly.
- **Commit:** `280e2c1`

No Rule 4 (architectural) decisions arose. No package was installed.

## Verification

| Check | Result |
|---|---|
| `pytest -q tests/test_phase21_multiplicity.py` | **17 passed in 1.12s** (budget 36s, `21-VALIDATION.md:53`) |
| `... tests/test_phase21_aligned_loader.py tests/test_phase21_aligned_bins.py tests/test_phase20_prereg.py` | **65 passed in 4.19s** |
| `-k conservation` (`21-VALIDATION.md:73`) | 5 passed, 12 deselected |
| `-k instrument_can_report_not_one` (`:74`) | 2 passed, 15 deselected — the mis-built arm AND the negative control |
| `-k seed_reproducible` (`:75`) | 1 passed, 16 deselected |
| **Full suite** | **955 passed, 7 skipped in 201.51s**, exit 0 |
| `git ls-files 'results/phase21_*'` | **empty** |
| `git status --porcelain results/` and `data/` | **empty** — nothing wrote into recorded evidence |
| `git diff --exit-code` on the three frozen pins | **0** — `mitigation_gate.py`, `mitigation_unit.py`, `phase18_extraction.py` byte-unchanged |
| `shasum -a 256 scripts/mitigation_unit.py` | `45f37e152bb4035667b804c1463431b3f12fa5096c47de32b1dc27abbe000473` — equal to 21-01's frozen value |
| `ruff check . && ruff format --check .` | All checks passed · 186 files formatted |
| `.planning/STATE.md` / `ROADMAP.md` | byte-unchanged (worktree mode — the orchestrator owns them) |

**The 7 skips reconcile exactly and none is caused by this plan.** All are gitignored artifacts
absent from a fresh worktree or a CUDA gate: `test_forbid_ids.py:196`, `test_lora_artifact.py:238`,
`test_slim_checkpoint.py:168` (slim artifact), `test_phase14_demo.py:611` and `:625`,
`test_phase15_plots.py:191` (checkpoints), `test_train_loop.py:81` (fp16 AMP needs CUDA). Six of
those PASS on the main checkout, so the worktree baseline is **938 passed, 7 skipped**; this plan
adds 17 tests and **938 + 17 = 955**. That closes against the prompt's `944 passed, 1 skipped` on
main exactly (`944 − 6 = 938`).

`scripts/phase21_unit_record.py` joins four `scripts/*.py` file-set walks 21-01 surfaced
(`test_phase14_scoring.py:461`, `test_lora_inject.py:279`, `test_phase17_stats.py:327`,
`test_phase19_erasure.py:1386`) and the `scripts/mitigation_*.py` glob it is deliberately outside.
All are inside the green full suite, and `test_phase20_prereg.py` was additionally run alone at
each task: **21 passed**, so the accumulated import ceiling was not widened.

## Requirements — deliberately NOT marked complete

`UNIT-03` is this plan's `requirements:` frontmatter and it is **not** marked complete.
`REQUIREMENTS.md` was not modified. D-26 requires the multiplicity to be MEASURED and written to
`results/phase21_*`, which is plan 21-11; this plan ships the instrument and the evidence that it
counts. Marking UNIT-03 complete on an uncommitted measurement would be the same substitution
UNIT-03 exists to refuse, and `21-CONTEXT.md` names "do not mark a requirement complete in the
first plan that touches it" as an Established Pattern.

## Known Stubs

**One, and it is the plan's design rather than an omission.** `refuse_existing_artifacts` exists
and is wired to `teach_persona.refuse_if_exists`, but **nothing writes**: `ARTIFACTS` is declared
and neither path is created. The plan's objective states this explicitly ("no artifact writing
yet"), and `test_the_artifact_is_not_written_yet` asserts it, because `adds[-1]`
(`tests/test_phase20_prereg.py:157`) makes the ancestry ordering of the first
`results/phase21_*` commit **irrevocable**. **Plan 21-11 resolves it** and is the only plan
permitted to. No stub prevents this plan's goal — the instrument is fully implemented and exercised
against the real 8-fact geometry at `block_size = 256`.

## Threat Flags

None. This plan adds no network endpoint, no auth path and no new file-access pattern: it READS
three bins the caller supplies at paths `fact_bin_path()` derives, and writes nothing. The one
`subprocess` call passes argv directly with no `shell=True`.

Register dispositions, all `mitigate`, all satisfied: T-21-10 (instrument prints its own
conclusion — the non-vacuity pair), T-21-44 (unnamed attribution rule — `ATTRIBUTION_RULE` in one
place, in the failure message, in the row), T-21-45 (double-counting/off-by-one — the exact
conservation law, RED observed overshooting to 1,993), T-21-46 (seed not reaching the draw — 1338
differs), T-21-47 (measuring a re-implementation — the wrapper and `fact_window_span`), T-21-63
(`strict=False` producing the record — default asserted, aborts on the mis-built bin), T-21-65
(span raise aborting the count — `"span"` observed at step 7 of a full lot), T-21-48 (analytic
number becoming the artifact — cross-check only, on a synthetic closed-form bin), T-21-64 (early
artifact commit — `git ls-files` empty).

## Commits

| Commit | Task | Content |
|---|---|---|
| `280e2c1` | 1 | `scripts/phase21_unit_record.py` — `ATTRIBUTION_RULE`, both counters, `ARTIFACTS`, `BIN_COMPOSITION_LABELS`, `ROW_SCHEMA`, the inherited refusal |
| `f1e8677` | 2 | conservation at (10,4)/(37,3)/(200,8), seeded reproduction, the row schema, four independent oracles, the wrapper's provenance |
| `ddd4196` | 3 | `instrument_can_report_not_one` + negative control, the `strict=True` default arm, the analytic cross-check, the artifact-ordering guard |

## Self-Check: PASSED

- `scripts/phase21_unit_record.py` — FOUND
- `tests/test_phase21_multiplicity.py` — FOUND
- `280e2c1`, `f1e8677`, `ddd4196` — all FOUND in `git log 1de1c98..HEAD`
- Working tree clean before this SUMMARY; `.planning/STATE.md` and `.planning/ROADMAP.md`
  byte-unchanged as required in worktree mode
- No gitignored artifact was produced, so nothing needed copying back to the main checkout
