---
phase: 18-black-box-adversarial-extraction-audit
plan: 02
subsystem: testing
tags: [draw-loop, seeding, prefix-stability, mutation-proof, fake-model, cpu-only]

# Dependency graph
requires:
  - phase: 14-persona-recall-demo
    provides: "`draw_all` / `question_seed` / `SEED` / `N_SEEDED_SAMPLES` — the draw loop every phase since 14 has paired its arms through"
  - phase: 18-black-box-adversarial-extraction-audit
    plan: 03
    provides: "`K = 64` and `FAMILY_ZERO_DRAWS = 9` — the pre-registered budgets, imported rather than retyped"
provides:
  - "`draw_all(..., index, *, n_samples=N_SEEDED_SAMPLES)` — the attacks' 64-draw budget and family zero's 9 both traverse ONE loop"
  - "`fake_lm` — a parameter-free, RNG-free, bit-deterministic `nn.Module` on the `gpt.py` forward contract; no checkpoint, no GPU"
  - "`tests/test_phase18_draws.py` — D-09's prefix stability proved of the CODE PATH by two RED mutations, and D-06's stride measured collision-free at 216x64"
affects: [18-04, 18-05, 18-06, 18-07, 18-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A stand-in model whose logits are an integer HASH of the input ids: deterministic without parameters and without a seed, so the only RNG reaching a draw is the generator under test"
    - "Mutation proof reported as a TABLE of reds AND greens — the greens bound what the guard covers, instead of leaving the bound to be inferred"

key-files:
  created:
    - tests/test_phase18_draws.py
  modified:
    - scripts/phase14_recall.py
    - tests/conftest.py

key-decisions:
  - "`n_samples` is KEYWORD-ONLY, matching 18-01's treatment of `family` and `prompt_ids`: `draw_all` already takes six positionals and a seventh would be silently accepted by any of its call sites"
  - "The test decodes with an INJECTIVE id-joiner, not the real BPE decoder — the real `decode` is both lossy (two id sequences can render to one string, hiding a divergence) and partial (it raises `UnicodeDecodeError` on hash-driven byte sequences). The real tokenizer is still used for the prompt and the forbid mask"
  - "`K` and `FAMILY_ZERO_DRAWS` are imported from `scripts/phase18_extraction.py`, extending 18-01's import-never-copy from a statistic to the pre-registered budgets"
  - "The plan's proposed mutation was MEASURED not to falsify the claim; two mutations that do were found, and all four results are recorded in the test file itself"
  - "No requirement marked complete: ATK-01/ATK-03 build no family and run no control here, STAT-04 was already `[x]` and is sustained (over-claim-avoidance, seventh application)"

patterns-established:
  - "A guard's mutation proof publishes its GREENs: the two mutations that left the test passing are what turn 'this test catches loop defects' from a claim into a bounded, checkable one"

requirements-completed: []

# Metrics
duration: 25min
completed: 2026-08-15
---

# Phase 18 Plan 02: Draw-Budget Widening and the D-09 Prefix Proof Summary

**`draw_all` gained exactly one keyword (`n_samples`, keyword-only, defaulted) so family zero's 9 draws and the attacks' 64 traverse one loop — and D-09's prefix-stability claim is now a committed CPU test that two independent mutations drive RED, against a parameter-free fake model that needs no checkpoint and no GPU.**

## Performance

- **Duration:** ~25 min (including a worktree base correction)
- **Started:** 2026-08-16T00:06:00Z
- **Completed:** 2026-08-16T00:31:00Z
- **Tasks:** 3
- **Files:** 2 modified, 1 created — 253 insertions / 4 deletions

## Accomplishments

- **`draw_all` widened by one keyword-only parameter** (`scripts/phase14_recall.py:612`). `range(N_SEEDED_SAMPLES)` became `range(n_samples)`; nothing else moved — draw 0 is still greedy, each seeded draw still builds its OWN `torch.Generator` at `question_seed(index) + s`, and the `(completions, stopped)` shape is unchanged. `question_seed` was not touched: D-06's stride is the caller passing `src_index * K` as the positional `index`, and the docstring now says so rather than leaving it to be inferred.
- **`fake_lm`** (`tests/conftest.py:33`) — a `torch.nn.Module` carrying a real `ModelConfig()` (so `vocab_size=8192` spans `STOP_IDS` 8184/8185 and the role ids, and `block_size`/`eos_id` are read rather than re-transcribed) whose logits are a pure integer hash of the input ids. **No parameters, no RNG of its own**, so two forwards on the same ids satisfy `torch.equal` and the only randomness reaching a sampled draw is the generator under test. `loss` is `None` bare and the identical flattened `F.cross_entropy` with `targets` — 18-06's span-NLL work (D-29/D-30) reuses that branch.
- **D-09's gap closed by execution, not prose** (`tests/test_phase18_draws.py`). `test_prefix_is_budget_independent` runs the REAL `draw_all` at `n_samples=63` and at `n_samples=8` for two indices and compares decoded completions and the `stopped` flags element-for-element. It additionally asserts the 64-draw run produced **64 completions and 64 DISTINCT ones**, so neither a short-circuiting fixture nor a degenerate logit surface can make the prefix claim vacuous.
- **D-06's stride measured collision-free.** 216 source questions x K=64 strided seeds are **13,824 distinct** values; the same slots unstrided collapse onto **279** — the exact number D-06 names, asserted both as the literal and as `216 + 64 - 1` so its provenance is visible. `SEED` is imported; the string `1337` does not appear in the test file.

## Task Commits

1. **Task 1: the `n_samples` keyword** — `432f1c2` (feat)
2. **Task 2: the `fake_lm` fixture** — `6da0db5` (test)
3. **Task 3: the two draw-layer proofs** — `d91e256` (test)

**TDD gate note.** Task 3 is marked `tdd="true"` but its `<files>` are test-only — the implementation it exercises landed in Task 1, so a literal RED-then-GREEN would have required writing a test known to pass. The plan substitutes a **mutation proof** for the RED gate, and that is what was run (below). The `feat` commit precedes both `test` commits, which is the correct order for a widening whose whole contract is that existing callers do not change.

## The mutation proof — four mutations, measured

Each was applied to `scripts/phase14_recall.py`, run against `test_prefix_is_budget_independent`, and reverted; `git diff --exit-code scripts/phase14_recall.py` returns 0 after every one.

| # | Mutation | Result | Why |
|---|---|---|---|
| M1 | generator hoisted above the loop, seeded once at `question_seed(index)` | **GREEN** | one shared stream is still consumed in draw order, so the first 9 draws read the same prefix of it at either budget |
| M2 | seed becomes `question_seed(index) + s + n_samples` | **RED** | draw *s* now depends on the budget — the defect in its purest form |
| M3 | `for s in reversed(range(n_samples))` | **RED** | draw ORDER becomes budget-relative |
| M4 | `SAMPLE_TEMPERATURE` 0.8 -> 1.7 | **GREEN** | both compared runs shift together |

**M1 is the mutation 18-02-PLAN prescribed, and it does not falsify the claim.** Recorded rather than quietly swapped: the plan's acceptance criterion ("temporarily reseed `draw_all`'s generator once outside the loop, observe RED") is measurably wrong, because hoisting the generator breaks *cross-question* independence — the property `question_seed`'s docstring is actually about — and leaves *budget*-independence intact. M2 and M3 are the mutations D-09 was really asking for. M2's failure output is diagnostic in the right way: draw 0 (greedy, no generator) still matches and the diff opens at index 1, the first seeded draw.

**What this bounds.** The test pins budget-independence, **not** the absolute stream: any change moving both compared runs equally is invisible to it by construction (M4). D-01's "identical stream" is a different claim needing a different guard, and the plan's action text asserting that a sampling-parameter change "fails it" is not true. All four rows are written into the test module's own docstring, so a future reader inherits the bound rather than the claim.

## Files Created/Modified

- **`scripts/phase14_recall.py`** — `draw_all`'s signature, `range(n_samples)`, and 8 docstring lines recording D-09's prefix argument and that D-06's stride is caller-side. **16 insertions / 3 deletions**; no assertion removed, no second loop, no batching path, no `greedy=False` option.
- **`tests/conftest.py`** — the `fake_lm` fixture plus 5 module-level hash constants. **73 insertions / 1 deletion** (the module docstring line, rewritten to mention the second fixture). `simulate_pascal` is untouched.
- **`tests/test_phase18_draws.py`** — new, 168 lines, 2 tests with the node ids 18-VALIDATION.md names.

## Verification

| Check | Result |
|---|---|
| `pytest -q` (full suite) | **662 passed, 7 skipped** in 123s |
| `pytest -q tests/test_phase14_scoring.py tests/test_phase16_driver.py` | **114 passed** — unchanged by the widening |
| `pytest -q tests/test_phase18_draws.py` | 2 passed in 3.9s (CPU, no GPU, no checkpoint) |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 159 files already formatted |
| `git diff --exit-code scripts/phase14_recall.py` after mutations | 0 |
| Existing tests modified | **0** |

Acceptance criteria as specified by the plan:

| Criterion | Expected | Actual |
|---|---|---|
| `grep -c "n_samples=N_SEEDED_SAMPLES" scripts/phase14_recall.py` | 1 | 1 |
| `grep -c "range(N_SEEDED_SAMPLES)" scripts/phase14_recall.py` | 0 | 0 |
| `inspect.signature(draw_all)` parameter list + default | as specified | `(model, tok, prompt_ids, device, forbid, index, *, n_samples=8)`, default `is N_SEEDED_SAMPLES`, kind KEYWORD_ONLY |
| `grep -c "def fake_lm" tests/conftest.py` | 1 | 1 |
| two forwards on the same ids satisfy `torch.equal` | yes | asserted in `test_prefix_is_budget_independent` |
| `grep -c "1337" tests/test_phase18_draws.py` | 0 | 0 |
| `tests/conftest.py` line count | >= 30 | 87 |
| `tests/test_phase18_draws.py` line count | >= 60 | 168 |

## Threat register disposition

| Threat ID | Disposition | How it was discharged |
|---|---|---|
| T-18-02-01 (Tampering — the widening changes the 9-draw stream every prior phase measured) | mitigated | `n_samples` defaults to `N_SEEDED_SAMPLES` and is keyword-only; the signature is asserted by an executable `inspect` check; Phase 14 + 16 suites re-run at 114 passed and the full suite at 662. |
| T-18-02-02 (Repudiation — the prefix claim asserted but never observed failing) | mitigated, **more strongly than planned** | Two independent mutations (M2, M3) drive it RED. Two further mutations that leave it GREEN are published, so the guard's coverage is bounded rather than assumed. |
| T-18-02-03 (Info Disclosure — a fixture loading a real checkpoint pulls taught weights into the CPU suite) | mitigated | `fake_lm` imports `ModelConfig` and nothing else; no checkpoint path, no device string, no GPU marker. The plan's grep recipe for this is unsatisfiable as written — see Deviations — so the intended quantity was measured on the added lines instead: 0. |
| T-18-02-SC (Tampering — package installs) | accepted | Zero installs. `pyproject.toml` untouched; its sha256 pin in `tests/test_package.py` is green. |

## Decisions Made

- **The test decodes with an injective id-joiner rather than the real BPE decoder.** This started as a blocker (below) but is the better comparator on its own merits: `BPETokenizer.decode` can render two different id sequences to the same string, which would let a genuine divergence compare equal. Joining the ids is total and injective, so a single differing token anywhere fails the assertion. The **real** tokenizer is still used for the prompt (`build_recall_prompt`) and the forbid mask (`undecodable_ids_mask` — 547 of 8192 ids decodable, both `STOP_IDS` among them), so the stop-without-yield path is genuinely reachable: 8 and 9 of the 64 draws terminate early at the two tested indices.
- **`_SPREAD = 4.0` is the one tuned number in the fixture**, and it is tuned against a stated failure mode: a peakier surface collapses the top-p nucleus, every draw becomes identical, and prefix equality holds vacuously. Measured at 4.0: 64 draws from one prompt are 64 distinct completions. The constant carries that measurement in its comment.
- **`K` and `FAMILY_ZERO_DRAWS` imported from `scripts/phase18_extraction.py`.** 18-04 owns that file this wave; this is a read, not an edit, and the file is under 18-03's ancestry pin so both constants are effectively frozen. The alternative — retyping 64 and 9 — produces a test that keeps passing after the budget it guards moves.
- **`test_strided_seeds_are_disjoint` requests `fake_lm` but does not use it**, with the reason stated in its docstring: it keeps both tests naming the same fixture, so a later edit cannot quietly make one model-dependent and the other not. The unused argument is asserted non-`None` so it is not merely decorative.
- **No requirement checked off.** ATK-01 constructs no attack family here and ATK-03 runs no positive control — this plan makes ATK-03's 9-draw budget *admissible*, which is a precondition, not the requirement. STAT-04 was already `[x]` and is sustained (zero installs). `REQUIREMENTS.md` is byte-unchanged.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] The plan's prescribed mutation does not falsify the test**

- **Found during:** Task 3, mutation proof
- **Issue:** the acceptance criterion prescribes hoisting/reseeding the generator once outside the loop and observing RED. Measured: **GREEN**. A single shared stream is consumed in draw order, so the 9-draw prefix is unaffected by the budget.
- **Fix:** two mutations that genuinely falsify the claim were found (budget-dependent seed; reversed draw order), both observed RED, and all four results — including the two GREENs that bound the guard — were written into the test module's docstring.
- **Files modified:** `tests/test_phase18_draws.py` (docstring only; the four mutations to `scripts/phase14_recall.py` were all reverted byte-identically)
- **Commit:** `d91e256`

**2. [Rule 3 — Blocking] The real BPE decoder cannot decode hash-driven draws**

- **Found during:** Task 3, first end-to-end run
- **Issue:** `draw_all` calls `tok.decode(gen_ids)`, and `BPETokenizer.decode` raised `UnicodeDecodeError: 'utf-8' codec can't decode byte 0x84` on the fake model's byte sequences. A trained model rarely emits invalid UTF-8; a hash over 547 decodable ids does so constantly.
- **Fix:** the test passes an injective `_IdDecoder` as `tok` while keeping the real tokenizer for the prompt and the forbid mask. No production code changed.
- **Files modified:** `tests/test_phase18_draws.py`
- **Commit:** `d91e256`
- **Scope note:** that the production decode path is *partial* on adversarial byte sequences is a pre-existing property of the real harness, not caused by this plan, and not in scope here. It is bounded in practice by `undecodable_ids_mask` plus a trained logit surface, and no Phase 14/16/17 run has hit it.

**3. [Bookkeeping] Task 2's grep acceptance recipe is unsatisfiable as written**

`grep -c "cuda\|mps\|load_slim\|checkpoints/" tests/conftest.py` returns **2**, not 0 — the two `torch.cuda` lines in the pre-existing `simulate_pascal` body. The plan's proposed filter, `grep -v simulate_pascal`, does not remove them, because those lines do not contain the string `simulate_pascal`. The intended quantity was measured on the lines this task actually added: `git diff -U0 tests/conftest.py | grep '^+' | grep -c 'cuda\|mps\|load_slim\|checkpoints/'` returns **0**. Recorded rather than silently reconciled.

### Environment correction (not a plan deviation)

The worktree spawned at `829cd5f`, behind the required base `450eb9c`, so the Phase 18 planning directory and Wave 1's merged code were absent. `829cd5f` was a strict ancestor and the tree was clean, so the base was corrected with `git merge --ff-only` — a pure fast-forward, 0 commits lost. Same quirk 18-01 recorded, second occurrence.

## Issues Encountered

- **Two `E501` line-length violations**, both in docstring prose (a table row and a summary line), caught by `ruff` before the commits and reworded. No logic involved.
- **The fixture's cost was measured, not assumed**, before it was committed: the full `test_prefix_is_budget_independent` (2 indices x (64 + 9) draws = 146 draws through the real loop) runs in **3.9s** on CPU. A 512-id-limited synthetic forbid mask was benchmarked as an alternative and offered no meaningful saving over the real 547-id mask, so the real one was kept.

## Known Stubs

None. Both tests drive the real `draw_all` and the real `question_seed`; nothing is placeholdered or left unwired. `fake_lm` is a deliberate test double, not a stub — its scope limit (models shape and determinism, not language) is stated in its own docstring.

## Next Phase Readiness

- **18-04 / 18-05 (the attack drivers)** can call `draw_all(..., src_index * K, n_samples=K - 1)` for 64 disjointly-seeded draws, and `draw_all(..., index)` for family zero's 9, through one loop. The disjointness is measured, not argued.
- **18-06 (the NLL / admissibility work)** reuses `fake_lm` for D-29's frame conditioning and D-30's sum-vs-mean reductions: the `targets=`-bearing branch returns a real `F.cross_entropy` on the `gpt.py` flatten, on CPU, with no checkpoint.
- **A caveat worth carrying forward:** `test_prefix_is_budget_independent` pins budget-independence only. If a later plan needs D-01's "identical stream" between family zero and the attacks, that is a distinct claim (M4 shows this test is blind to a change moving both runs together) and needs its own guard.
- `scripts/phase14_recall.py` is under no STAT-05 ancestry pin (only `scripts/erasure_gate.py`, `scripts/phase17_personas.py` and `scripts/phase18_extraction.py` are), so this edit disturbs no pre-registration ordering guard.

## Self-Check: PASSED

- All 3 claimed files present on disk (`scripts/phase14_recall.py`, `tests/conftest.py`, `tests/test_phase18_draws.py`), plus this SUMMARY.
- All 3 claimed commits present in `git log`: `432f1c2`, `6da0db5`, `d91e256`.
- `git status --short` clean apart from this SUMMARY.
- `git diff --name-only 450eb9c..HEAD` lists exactly 3 paths; **no `STATE.md`, no `ROADMAP.md`, no `REQUIREMENTS.md`** — the orchestrator owns the first two, and the third is genuinely unchanged.
- No file deleted by any commit (`git diff --diff-filter=D` empty for all three).

---
*Phase: 18-black-box-adversarial-extraction-audit*
*Completed: 2026-08-15*
