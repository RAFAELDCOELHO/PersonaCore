---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
plan: 08
subsystem: training
tags: [differential-privacy, dp-sgd, training-loop, additive-seam, fact-aligned, wiring, bit-identity]

# Dependency graph
requires:
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-06's dp_fn= gradient-side seam and its additive-seam precedent in loop.py — the `replay_fn = None` + guarded-block shape this seam copies, and the measurement that D-02's inherited-divide fake is structurally invisible at grad_accum_steps = 1"
  - phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
    provides: "training/data.py::get_batch_fact_aligned — reused BYTE-UNCHANGED; its `fact_index = step % n_facts` convention and its three-bin refusals"
  - phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
    provides: "tests/test_phase21_aligned_bins.py::_build/_aligned_pairs — the aligned-corpus builders, IMPORTED not re-written"
  - phase: 10-the-training-loop-and-the-golden-trajectory
    provides: "tests/test_loop_penalty_fn.py::_run_recipe and tests/fixtures/golden_trajectory_v1.json — the recipe the V-14 fact half runs on"
provides:
  - "src/personacore/training/loop.py::train's fact_bin= / n_facts= — the additive fact-aligned DATA seam, and get_batch_fact_aligned's FIRST path through train()"
  - "the accum-agreement refusal: fact_bin set with max(1, grad_accum_steps) != n_facts raises, with the measured 9-in-prose/0-in-code gap named in the message"
  - "the all-or-none companion refusal (fact_bin/n_facts/train_bin/train_mask_bin) and an n_facts positive-int refusal"
  - "the per-optimizer-step one-record-per-micro-step refusal — Phase 21 D-02 as a runtime property"
  - "tests/test_phase22_wiring.py — V-23's loop half and V-14's fact half; 11 test functions, 12 collected, 0 -> 12"
  - "the measured finding that the multiset and set forms of the per-step check are EQUIVALENT under the accum refusal, with both false claims corrected in place"
affects: [22-09 the four fake probes, 22-10 wiring the teach_persona.py caller, 22-11 the positive controls, 23 the frontier sweep]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A multi-kwarg all-or-none group must be GATED on the half that opts in; a flat `len(_missing) != len(_group)` over a group that includes pre-existing kwargs raises on every existing caller"
    - "Patch where the name is LOOKED UP: a from-import binds at import time, so a spy on the defining module never reaches the consumer — and a meta-guard asserting the wrong target yields 0 calls keeps a future edit from re-breaking it"
    - "A measurement baked into a production error message needs a test that re-measures it, or it goes stale silently and a user debugs a privacy claim against a false number"
    - "When a mutation proves two guard forms EQUIVALENT rather than one stronger, publish the equivalence and correct the claim — a green mutation is evidence, not an omission"

key-files:
  created:
    - tests/test_phase22_wiring.py
  modified:
    - src/personacore/training/loop.py

key-decisions:
  - "The plan's literal all-or-none construction (`_missing = sorted(...)` over a four-key dict with `len(_missing) != len(_fact)`) is UNSATISFIABLE: with train_bin + train_mask_bin set and fact_bin/n_facts absent it gives 2 missing of 4 and RAISES on every pre-existing mask-seam caller. Gated on the fact half instead, matching the plan's own prose ('or none of the first two')"
  - "The plan's mandated comment reason for the mutable cell — 'a closure captures the binding at definition time, not the value at call time' — is FALSE in Python and was measured false ([0, 1, 2] over three iterations) before the comment was written. The cell still ships, for the two reasons that are actually true"
  - "The spy is installed on `personacore.training.loop`, not `personacore.training.data` as the plan specifies: loop.py binds the loader with a from-import, so the data-module target never reaches train(). A meta-guard test pins it"
  - "The multiset per-step check is NOT stronger than set equality here — mutation M7 measured the swap GREEN across the whole suite. Both the loop.py comment and the test docstring claimed it was; both corrected in place. The multiset form still ships, as the shape that survives a relaxation of the accum refusal"
  - "An n_facts positive-int refusal was added (Rule 2, not in the plan), mirroring the existing replay_windows type refusal: n_facts is the lot size the accountant is told"
  - "requirements.mark-complete was NOT called. DPSGD-01 needs 22-10's production caller (train() can now do it; scripts/teach_persona.py still does not) and DPSGD-02's fact half is proven here but the requirement was already completed by 22-06"

patterns-established:
  - "Opt-in-gated all-or-none: key the companion group on the NEW kwargs, never on a flat dict that includes pre-existing ones"
  - "Self-re-measuring error messages: an ast-based test that re-derives the number a production refusal message states, with a failure message naming the plan that will legitimately turn it red"

requirements-completed: []
requirements-contributed: [DPSGD-01, DPSGD-02]

# Metrics
duration: 35min
completed: 2026-08-26
---

# Phase 22 Plan 08: The `fact_bin=` Data Seam Summary

**Phase 21's fact-aligned loader reaches `train()` for the first time, through an additive seam whose OFF path still reproduces the Phase-10 golden trajectory on all three fingerprints — and the configuration the production caller inherits (`grad_accum_steps = 1` against `n_facts = 8`) is now a refusal, so the lot the accountant is told about is the lot that was released. 8 mutations, 7 distinct REDs, and the 8th is a published equivalence proof rather than a missing guard.**

## Performance

- **Duration:** ~35 min (start `2026-08-26T00:10:49Z`, first commit `a472abc`, last task commit `2f287a1`)
- **Tasks:** 2
- **Files:** 1 created, 1 modified

## Accomplishments

- **`get_batch_fact_aligned` has a path through `train()` at all, for the first time.** Before this commit `loop.py` had **0** hits for `fact_bin` / `fact_aligned` / `align_facts`; it now has **11** for `fact_bin` and one real call site. The loader's only non-test caller was `scripts/phase21_unit_record.py`, the reporting driver.
- **The seam is genuinely additive.** `loop.py` is **+175 / −2**, and the two removed lines are the single-line `from .data import` (rewritten as a multi-line import) and `if train_mask_bin is not None:` → `elif`. **Zero** changed lines inside `_optimizer_step`, `replay_fn`, or the `dp_fn` branch; `xb, yb = batch_fn(micro)` is untouched at `:199`, and 22-06's structural claim survives — `clip_grad_norm_` still has exactly ONE call site (`:221`), still under `if dp_fn is None:`.
- **V-14's fact half is proven with the actual fingerprints, not a loss curve** — and they are the same values 22-06 recorded, so the seam did not perturb the golden trajectory. See the table below.
- **The detectability constraint is satisfied by measurement, not prose.** Every real DP arm has `n_facts > 1` (`dp_n8` = 8, `dp_n64` = 64) and `TrainConfig.grad_accum_steps` defaults to `1`. The accum refusal makes that default *unreachable* on the aligned path, asserted per arm.
- **The whole failure class this plan exists to close was watched.** Mutation M1 (the per-optimizer-step counter — PATTERNS trap 2, T-22-40) reddens **7** tests; M2 (`step=micro`, colliding windows) reddens exactly **one**, and that one is load-bearing.
- **`src/personacore/training/data.py`, `pyproject.toml`, `scripts/teach_persona.py`, `src/personacore/privacy/` and all three frozen `scripts/mitigation_*.py` are byte-unchanged** (`git diff --exit-code` exits 0). This is routing, not a loader edit. Nothing was installed.
- Full suite **1243 → 1255 passed, 1 skipped** (+12, zero regressions). `ruff` clean over **202 files**.

## Task Commits

1. **Task 1: the additive `fact_bin=` data seam and its three refusals** — `a472abc` (feat)
2. **Task 2: V-23 — inertness, routing, the global micro-step counter, both refusals** — `2f287a1` (test)

Task 2's commit also carries the two in-place corrections to `loop.py`'s per-step-check comment that Task 2's mutation probe found (see *Guards Watched Failing*, M7).

## Files Created/Modified

- `src/personacore/training/loop.py` (+175 / −2) — `fact_bin=None` / `n_facts=None` on `train()`'s keyword-only signature beside the other bin kwargs; two full Args registers in the `replay_bin` DOES-claim / does-NOT-claim / measured-state-replaced shape; three refusals (companions, `n_facts` type, accum agreement); a `_fact_cursor` carrier; the `batch_fn` branch with both mandatory comments; the per-optimizer-step one-record refusal.
- `tests/test_phase22_wiring.py` (**new**, 11 test functions / **12 collected**, 4.8 s) — V-14's fact half, routing with a zero-call control, the patch-target meta-guard, the global-counter test, three refusal tests, the per-arm detectability test, the ast re-measurement of the message's own claim, and both D-02 violation shapes.

## The Evidence

### V-14, the fact-seam half — the actual comparison

`test_loop_penalty_fn._run_recipe` (imported, not re-written — the recipe the Phase-10 golden fixture was captured against), CPU, 5 steps.

| Fingerprint | omitted | `fact_bin=None, n_facts=None` | `golden_trajectory_v1.json` |
|---|---|---|---|
| CSV text (6 rows) | sha256 `2f4b95ac4c05add4…` | `2f4b95ac4c05add4…` | `2f4b95ac4c05add4…` |
| final loss `repr` | `9.435891151428223` | `9.435891151428223` | `9.435891151428223` |
| parameter bytes sha256 | `647f5981027bfce1…` | `647f5981027bfce1…` | `647f5981027bfce1…` |
| all three, `==` | — | **True** | **True** |

Identical to the values 22-06 recorded, which is the point: this seam moved neither. `test_fact_bin_none_is_inert` reads no platform identity and never skips, so it carries the guarantee where the golden replay is gated off; the golden replay itself also ran and passed on this box.

### The corpus the routing runs on, and what the loader was handed

Built through the REAL packer (`_build(..., align_facts=_aligned_pairs())`), not a toy:

| Quantity | Measured |
|---|---|
| `n_facts` | **8** |
| `n_windows` | 33 |
| `windows_per_fact` | `(4, 4, 4, 4, 4, 5, 4, 4)` — D-01's ragged geometry, so the batch size VARIES by record |
| `block_size` | 256, resolved from `tp.BLOCK_SIZE`, never re-spelled |
| loader calls, 1 optimizer step at `accum = 8` | **8** |
| loader calls with the seam OFF (the control) | **0** |
| `step=` values over **2** optimizer steps | `[0, 1, 2, …, 15]` — 16 values, **16 distinct**, strictly increasing, windows disjoint |
| `fact_index` per window | `sorted(...) == [0..7]` for both windows — every record exactly once |

### Detectability — the 22-06 constraint, measured rather than asserted

22-06 measured D-02's inherited-divide fake (the lot divide inherited rather than applied) to be **structurally invisible at `grad_accum_steps = 1`**, because `total / 1` is `total` exactly.

| Arm | `n_facts` | `TrainConfig().grad_accum_steps` | accum the seam forces | production default accepted? |
|---|---|---|---|---|
| `dp_n8` | **8** | 1 | **8** | **refused** (`ValueError`) |
| `dp_n64` | **64** | 1 | **64** | **refused** (`ValueError`) |

`test_the_production_default_accum_is_refused_at_the_real_fact_count` reads `n_facts` from `teach_persona.arm_spec(arm)` rather than from a literal, asserts `n_facts > 1` per arm, asserts `TrainConfig().grad_accum_steps == 1`, and observes the refusal. It needs no corpus — the refusal fires before `train()` opens a file.

### The 9-in-prose / 0-in-code gap, re-measured

`grad_accum_steps` in `scripts/teach_persona.py`: **9 textual hits, 0 code hits** — every one inside a docstring, a comment or an error string (`:195`, `:524`, `:548`, `:564`, `:656`, `:740`, `:859`, `:863`, `:919`). Code hits are counted by `ast` (`keyword.arg` / `Attribute.attr` / `Name.id`), not by grep. `test_the_9_in_prose_0_in_code_measurement_is_still_true` re-derives it on every run, so the number baked into the production refusal's message cannot go stale unnoticed.

## Guards Watched Failing

Eight mutations, each applied to the work-tree `loop.py` and restored in a `finally`. Restore verified by sha256: **`52b4d65fb9368d3ab9c84bef99fd7069b5044eb94bdb9aae6ef3409a3f1077c6` before and after.** Probe target: `tests/test_phase22_wiring.py tests/test_loop_penalty_fn.py tests/test_train_loop.py`.

| # | Mutation | Result | Guard(s) reddened |
|---|---|---|---|
| M0 | control | **20 passed, 1 skipped** | — |
| M1 | **PATTERNS trap 2** — `step=_fact_cursor["step"]` (the bare OPTIMIZER step) | 7 failed | the counter test, the routing test, both D-02 shape tests, the patch-target meta-guard, and both refusal tests' positive controls |
| M2 | `step=micro` alone — the colliding-windows shape | **1 failed** | `test_step_counter_is_global_and_monotonic` ONLY |
| M3 | the per-step one-record refusal dropped | 2 failed | `test_every_fact_contributes_exactly_once`, `test_a_duplicated_record_is_refused` |
| M4 | the accum-agreement refusal dropped | 3 failed | `test_accum_must_equal_n_facts`, `…refused_at_the_real_fact_count[dp_n8]` and `[dp_n64]` |
| M5 | the all-or-none companion refusal dropped | 1 failed | `test_fact_bin_requires_its_companions` |
| M6 | the fact branch dropped (falls through to the mask branch) | 7 failed | same set as M1 |
| M7 | the multiset check weakened to **set equality** | **20 passed — GREEN** | none, and that is a PROOF — see below |
| M8 | `_fact_cursor["seen"]` not cleared between steps | 2 failed | `test_every_fact_contributes_exactly_once`, `test_step_counter_is_global_and_monotonic` |

**M2 reddening exactly one test is the interesting row, not a weak one.** `step=micro` gives `[0..7]` twice: distinct *within* each window, so every per-window property — the routing count, both `fact_index` multisets, both refusals — stays green. Only the two windows being **disjoint** separates it from a correct wiring, and only `test_step_counter_is_global_and_monotonic` asserts that. Without that single assertion the run would never advance past the first lot of records, silently.

**M7 is GREEN and it changed what shipped.** The first draft of `loop.py`'s comment said the multiset form (`sorted(seen) == list(range(n_facts))`) was *"deliberately stronger than set equality: set equality passes a window that drew record 0 twice and record 3 never"*, and the test docstring repeated it. Watched: swapping the check for `set(_seen) != set(range(n_facts))` leaves the **entire suite green**. The reason is structural and provable — the accum-agreement refusal pins `len(seen) == n_facts`, and `n` draws whose SET is `range(n)` are necessarily distinct, so the two forms are **equivalent under the shipped refusals**. Both false claims were corrected in place. The multiset form still ships, because it is the shape that stays correct if the accum refusal is ever relaxed — but it is now described as that and not as a sharper detector. `len(spy.indices) == n` is asserted in the test to pin the premise the equivalence rests on.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The plan's literal all-or-none construction raises on every pre-existing mask-seam caller**

- **Found during:** Task 1
- **Issue:** Task 1(b) mandates *"the same `_missing = sorted(...)` / `if _missing and len(_missing) != len(_fact)` construction"* over a group of `fact_bin`, `n_facts`, `train_bin`, `train_mask_bin`. Applied literally, a caller with `train_bin` + `train_mask_bin` set and the fact kwargs absent gives `_missing = ['fact_bin', 'n_facts']`, `len 2 != 4` → **`ValueError`**. That is every Phase-12 mask-seam caller, including `scripts/teach_persona.py`'s production `train()` call.
- **Fix:** the group is **gated on the fact half** — the check runs only when `fact_bin` or `n_facts` is not None, and then requires all four. This matches the plan's own prose (*"together or none of the first two"*); only the literal construction was wrong. The `_missing = sorted(...)` register and the "cannot be defaulted" reason are preserved verbatim.
- **Verification:** a direct probe confirms the mask seam is unaffected (`NO RAISE`) while all three incomplete fact combinations raise with **pairwise distinct** messages (`missing ['n_facts']` / `['train_mask_bin']` / `['fact_bin']`). M5 watched RED.
- **Committed in:** `a472abc`

**2. [Rule 1 - Bug] The plan's mandated comment states a false fact about Python closures**

- **Found during:** Task 1
- **Issue:** Task 1(d) requires the comment to say *"why the cell and not a closure over the loop variable — a closure captures the binding at definition time, not the value at call time"*. That is the **opposite** of Python's semantics. Measured before writing: a nested function reading a local assigned *after* its `def` returns `[0, 1, 2]` across three iterations — closures capture the CELL and resolve at CALL time. Shipping the plan's sentence would have put a false statement about the language into the file that owns the privacy-critical counter.
- **Fix:** the cell still ships, with the two reasons that are actually true recorded instead — `seen` needs a mutable carrier the `while` loop can clear anyway (so the dict costs no extra object), and an explicit `_fact_cursor["step"] = step` written immediately before `_optimizer_step` makes the window↔step coupling greppable at the loop rather than an implicit read of a local defined a hundred lines below the `def`. The comment names the measurement.
- **Committed in:** `a472abc`

**3. [Rule 1 - Bug] The plan's monkeypatch target never reaches `train()`**

- **Found during:** Task 2
- **Issue:** Task 2 specifies *"monkeypatch `personacore.training.data.get_batch_fact_aligned`"*. `loop.py` binds the loader with `from .data import …`, so the name `train()` calls is `loop.get_batch_fact_aligned`; a spy on the data module is never consulted. The routing test would count 0 calls and the constant-`fact_index` negative control would silently fail to inject. The existing precedent in the repo already does it the right way (`tests/test_masked_train_seam.py:63` patches `loop_mod`).
- **Fix:** the spy is installed on `loop_mod`, and `test_the_spy_must_be_installed_on_the_loop_binding_not_the_data_module` **asserts the measurement** — a spy on `data_mod` yields `calls == 0` while the run completes — so a future edit that "corrects" the target back reddens instead of going vacuous.
- **Committed in:** `2f287a1`

**4. [Rule 2 - Missing critical functionality] `n_facts` had no type refusal**

- **Found during:** Task 1
- **Issue:** `n_facts` is the lot size the accountant is told and the `N` in D-02's final divide, and the plan specifies no validation for it. `n_facts=0` would make `step % n_facts` a `ZeroDivisionError` deep in the loader; `n_facts=True` is an `int` that would silently mean 1; a float would produce a nonsense modulus. The sibling kwarg `replay_windows` already carries exactly this refusal.
- **Fix:** the same `isinstance(..., bool) or not (isinstance(..., int) and > 0)` shape, with a message naming what the number IS.
- **Verification:** `test_n_facts_must_be_a_positive_int` over `(0, -1, True, 2.0, "8")`.
- **Committed in:** `a472abc`

**5. [Rule 2 - Missing critical functionality] The refusal message states a MEASUREMENT nobody re-measures**

- **Found during:** Task 2
- **Issue:** Task 1(c) requires the accum message to state *"9 times in `teach_persona.py` prose and 0 times in its code"*. A measured number frozen into a production error string is a claim that goes stale silently — and this one goes stale by design, the moment plan 22-10 wires the caller. A user debugging a privacy claim would read a false number.
- **Fix:** `test_the_9_in_prose_0_in_code_measurement_is_still_true` re-derives both halves on every run (textual `count`, code hits via `ast`). Its failure message names plan 22-10 as the legitimate cause and instructs updating the message rather than deleting the test.
- **Committed in:** `2f287a1`

**6. [Rule 1 - Bug] The multiset-vs-set claim, in two places, measured false** — see M7 in *Guards Watched Failing*. Committed in `2f287a1`.

**7. [Rule 3 - Blocking] `make test` / `make lint` still do not resolve the venv**

- **Found during:** verification
- **Issue:** the `Makefile` invokes bare `pytest` / `ruff`, which resolve to a pyenv 3.12.13 with no torch. **Seventh** confirmation (22-01…22-07). Task 1's acceptance criterion literally says `make lint` exits 0; it cannot on this box.
- **Fix:** all verification ran through `.venv/bin/`. `.venv/bin/ruff check . && .venv/bin/ruff format --check .` is clean over **202 files**. The `Makefile` is untouched — out of scope.
- **Committed in:** n/a

**8. [Rule 1 - Bug] `gsd-sdk` mutation-handler defects, hand-repaired before commit** — see *Tooling Corruption Encountered*.

### Deliberate departures from the plan text

- **`fact_bin=` / `n_facts=` are placed beside the other bin kwargs (after `replay_windows=`), not literally appended.** Everything after `*` is keyword-only, so position has no semantics for any caller; grouping the four data-source kwargs together is what a reader needs.
- **The branch lives INSIDE `elif train_bin is not None:`, as the first sub-branch.** That satisfies "takes precedence over the mask branch" while preserving `train_ids, val_ids = train_bin, val_bin`, so `estimate_loss` still routes correctly — placing it at the top level of the dispatch would have dropped that line.
- **The per-step refusal fires AFTER `_optimizer_step` has already applied the update.** It is a refusal, not a rollback: the point is that the run stops before a *second* mis-attributed lot is released and before any artifact is written. Rolling back one step would need optimizer-state surgery for no additional guarantee.
- **A fixture model of `GPT(n_layer=1, n_head=2, n_embd=16)` is used, not the bigram.** The bigram at `vocab_size = 8192` is an `8192 × 8192` embedding (67M params, ~270 MB of gradient) and nothing here measures the model. `block_size` is `tp.BLOCK_SIZE`, resolved from the packer, because the loader derives its window count from `model_cfg.block_size` and a skew would mis-attribute windows to records.
- **`test_step_counter_is_global_and_monotonic` runs at `start_step = 0` rather than through a resume.** All three wiring shapes the plan names are distinguished there (the `* n_facts` factor by window disjointness, the `+ micro` term by within-window distinctness), and a resume leg would add none: `start_step * n_facts ≡ 0 (mod n_facts)`, so the `fact_index` sequence is identical either way. The formula is written with `start_step` rather than hard-coded, so it stays correct if that ever changes.
- **A second D-02 violation shape ships** (`test_a_duplicated_record_is_refused` — one record twice, another never) alongside the plan's constant-index control, because the constant case is the degenerate one and a near-miss is the shape a subtly-wrong loader actually produces.
- **A `>` disagreement is tested as well as `<`** in `test_accum_must_equal_n_facts` (`accum = n_facts + 1`), so the check is pinned as an equality and not something a larger accumulation window could slip through.
- **Line anchors inside new code are cited by SYMBOL, never by line number**, continuing 22-02…22-07's habit. This plan's own `loop.py:NNN` anchors were correctly flagged by its `read_first` banner as pre-22-06 measurements and were all resolved by symbol.

---

**Total deviations:** 8 auto-fixed (1 unsatisfiable refusal construction, 1 false language fact, 1 unreachable patch target, 2 missing validations, 1 claim measured false in two places, 1 blocking environment issue, 1 tooling corruption), 8 deliberate departures.
**Impact on plan:** every correction makes a guard bite more, a claim narrower and truer, or an instruction actually executable; none weakens a guard or widens a claim. No scope creep — `data.py`, `pyproject.toml`, `teach_persona.py`, `privacy/` and all three frozen `mitigation_*.py` are byte-unchanged.

## Tooling Corruption Encountered

Eighteenth consecutive session. Every `gsd-sdk` mutation call was followed by `git diff` on the three planning files and hand-repaired before the metadata commit. All calls used the `--flag` form; the positional path was not exercised.

| Handler | Defect observed | Repair |
|---|---|---|
| `state.advance-plan` | rewrote `Status: Executing Phase 22` back to `Status: Ready to execute` — identical to 22-01…22-07 | restored by hand |
| `roadmap.update-plan-progress 22` | wrote the status cell as `In Progress\|  \|` — no space before the pipe, empty date cell where every sibling carries `-` | corrected to `\| 8/11 \| In Progress \| - \|` |
| `state.add-decision --summary` | prefixed every entry `- [Phase ?]:` | prefix corrected to `[Phase 22]` |
| `state.update-progress` | `{"updated": false, …}` against a frontmatter that has a Progress field | harmless; `advance-plan` had already set the block |
| `state.record-metric --flag` / `state.record-session --stopped-at` | **correct** under the `--flag` form | — |

Sixth consecutive confirmation that the corruption lives in the **positional** argument path. The 22-06 workaround held again: `22-08-SUMMARY.md` was written to disk **before** `roadmap.update-plan-progress` ran, so the handler counted 8 summaries and wrote the count and checkbox correctly.

## Issues Encountered

- **The `.gitignore` modification present at session start is pre-existing and untouched** — not staged in any commit here.
- **`requirements.mark-complete` was deliberately NOT called.** DPSGD-01's production wiring is 22-10's (`scripts/teach_persona.py` still passes no `fact_bin`, no `grad_accum_steps`, no `dp_fn`); DPSGD-02 was already completed by 22-06 and this plan's fact half only reinforces it.

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest tests/test_phase22_wiring.py -q` | **12 passed** in 4.79 s (11 test functions, one parametrized ×2) |
| Task-1 verify set (`test_loop_penalty_fn` + `test_train_loop` + `test_masked_train_seam` + `test_phase21_aligned_loader` + `test_memmap_data`) | **28 passed, 1 skipped** |
| `grep -c "fact_bin" src/personacore/training/loop.py` | **11** (criterion: ≥ 6) |
| `get_batch_fact_aligned` call site in `loop.py`, and its `step=` | `:624`; `step=_fact_cursor["step"] * n_facts + micro` at `:630` — contains BOTH `n_facts` and `micro` |
| `xb, yb = batch_fn(micro)` | **unchanged** at `:199`; the only other hit is a comment naming it |
| `grep -n "clip_grad_norm_"` — CALL SITES | **1** (`:221`), still under `if dp_fn is None:` — 22-06's structural claim survives |
| `git diff HEAD~2 -- loop.py \| grep -c "^-[^-]"` | **2** — the from-import line and `if`→`elif`. 0 changed lines in `_optimizer_step` / `replay_fn` / the `dp_fn` branch |
| `git diff --exit-code -- data.py pyproject.toml teach_persona.py privacy/ mitigation_{gate,unit,accountant}.py` | exit **0** — all byte-unchanged |
| `grep -rn "def _build" tests/test_phase22_wiring.py` | **nothing** — the Phase-21 builders are imported |
| Three incomplete companion combinations | raise, **pairwise distinct** (`missing ['n_facts']` / `['train_mask_bin']` / `['fact_bin']`) |
| mask-seam caller unaffected by the new refusals | `NO RAISE` — the probe that catches deviation 1 |
| Mutation probe | **8 mutations, 7 distinct REDs + 1 published equivalence**, control GREEN, sha256-identical restore |
| Full suite `.venv/bin/python -m pytest -q` | **1255 passed, 1 skipped** in 214.43 s (baseline 1243/1, +12) |
| `.venv/bin/ruff check . && .venv/bin/ruff format --check .` | clean, **202 files** |

## Known Stubs

None. Every parameter added is consumed by a committed test, both refusals and the runtime property are watched failing, and no placeholder was left. What this plan does **not** deliver, stated so no reader infers it: **`scripts/teach_persona.py` still passes no `fact_bin`, no `n_facts`, no `grad_accum_steps` and no `dp_fn`.** `train()` can now do it; the production caller does not yet. That is D-08's caller half and plan 22-10's scope. A wired seam is not a wired arm.

## Threat Flags

None. No network endpoint, no auth path, no new file-access pattern (the only new I/O is `get_batch_fact_aligned`'s existing three-memmap read, reached through a new branch), no schema change. Nothing was installed; `pyproject.toml` is byte-unchanged.

Threat register dispositions, each mitigated as planned:

- **T-22-38** (an aligned corpus trained through the flat loader under a DP arm name) — the `fact_bin` branch routes to `get_batch_fact_aligned`, asserted by a delegating spy with a **zero-call** control when the seam is off; M6 (branch dropped) watched RED across 7 tests.
- **T-22-39** (`grad_accum_steps` silently 1) — the accum-agreement refusal, with the 9-in-prose/0-in-code gap named in the message **and re-measured by a test**; M4 watched RED, and the production default is asserted refused for both real arms.
- **T-22-40** (a per-OPTIMIZER-step counter collapsing the lot onto ONE record) — the counter is `optimizer_step * n_facts + micro`; `test_step_counter_is_global_and_monotonic` asserts 16 distinct values across two disjoint windows. M1 watched RED (7 tests), M2 (the other wrong shape) watched RED by the disjointness assertion alone.
- **T-22-41** (the one-record property asserted but never observed failing) — the per-step refusal is a runtime check; its negative control feeds a constant `fact_index` and observes it fire, a second control feeds a duplicate, and M3 (refusal dropped) watched RED.
- **T-22-42** (the seam changing the default path) — `test_fact_bin_none_is_inert` compares CSV text, final-loss repr and parameter sha256 between omitted and `None`, all three matching the Phase-10 golden values; the full suite is +12 with zero regressions.
- **T-22-SC** (package installs) — accepted; nothing installed, `pyproject.toml` byte-unchanged.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plan 22-10 owns the caller and now has a seam that refuses its mistakes.** `train(fact_bin=…, n_facts=…)` requires `train_bin` + `train_mask_bin` alongside, and requires `grad_accum_steps == n_facts` — so a `TrainConfig(...)` that omits `grad_accum_steps` will RAISE rather than silently train at a lot size of one. Resolve `fact_bin` through `teach_persona.fact_bin_path(bin_path)` and `n_facts` from `len(facts)` / `stats["n_facts"]`, never a literal.
- **Plan 22-10 will turn `test_the_9_in_prose_0_in_code_measurement_is_still_true` RED, and that is correct.** Wiring `grad_accum_steps = n_facts` at the caller adds a code hit. **Update the measurement in `loop.py`'s accum-refusal message** to the new numbers; do not delete the test and do not leave a false number in a message a user reads while debugging a privacy claim.
- **Do not credit the per-step multiset check with detecting a duplicate that set equality would miss.** Measured (M7): under the accum refusal the two forms are provably equivalent and the swap leaves the suite green. The detectors that bite are the counter test's disjointness assertion and the two negative controls.
- **Patch `personacore.training.loop`, never `personacore.training.data`.** `loop.py` uses a from-import; a spy on the defining module yields 0 calls. `tests/test_phase22_wiring.py::test_the_spy_must_be_installed_on_the_loop_binding_not_the_data_module` is the meta-guard, and `tests/test_masked_train_seam.py:63` is the older precedent.
- **`accum = 1` remains the blind spot for D-02's inherited-divide fake, and it is now unreachable on the aligned path only.** `n_facts = 1` would re-open it. Nothing in the tree builds a one-fact arm today (`dp_n8` = 8, `dp_n64` = 64), but 22-09/22-11's positive controls should not construct one.

## Self-Check: PASSED

- `src/personacore/training/loop.py` — FOUND
- `tests/test_phase22_wiring.py` — FOUND
- `.planning/phases/22-dp-sgd-core-accountant-and-the-correctness-battery/22-08-SUMMARY.md` — FOUND
- commit `a472abc` — FOUND
- commit `2f287a1` — FOUND

---
*Phase: 22-dp-sgd-core-accountant-and-the-correctness-battery*
*Completed: 2026-08-26*
