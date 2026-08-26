---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
plan: 10
subsystem: training
tags: [differential-privacy, dp-sgd, production-wiring, cli, fact-aligned, replay-seam, end-to-end]

# Dependency graph
requires:
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-04's privacy/dpsgd.py::DPSGD — the keyword-only no-default sigma/clip_norm constructor and D-04's three property refusals the caller must satisfy"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-06's train(dp_fn=) gradient-side seam, and the measurement that D-02's inherited-divide fake is structurally invisible at grad_accum_steps = 1"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-08's train(fact_bin=/n_facts=) data seam, its accum-agreement refusal, and tests/test_phase22_wiring.py — extended here, not clobbered"
  - phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
    provides: "teach_persona.py's PACKER half — build_arm_bins' DP_ARMS branch, fact_bin_path, replay_window_budget, and stats['fact_bin']/['n_facts']"
provides:
  - "scripts/teach_persona.py::train_arm's FOUR D-08 wirings on dp_n8/dp_n64 — the first production path from an arm name to a DP-SGD training run"
  - "dp_sigma/dp_clip_norm threaded main() -> train_arm(), no numeric sigma or C literal anywhere in the file"
  - "main()'s --sigma= / --clip-norm= branch: required, no default, parsed in the file's own argv-slicing register (no argparse)"
  - "a DP-arm refusal at train_arm ITSELF, so the five callers that bypass main() are covered too"
  - "the DIALOG_TRAIN_BIN/MASK existence guard for DP arms, hoisted above the bins build"
  - "tests/test_phase22_wiring.py — V-23's caller half and V-13; 12 -> 21 collected"
  - "the measured finding that a dict-STRING-KEY splat is invisible to 22-08's code-hit predicate, and the dict(kw=...) form that fixes it"
affects: [22-11 the positive controls, 23 the frontier sweep and DPSGD-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A gated kwarg group spelled `dict(kw=value, ...)` rather than `{\"kw\": value}`: same single splat, but every entry is a real ast.keyword, so the static instruments that count code hits can SEE the wiring"
    - "A refusal that guards a resource parameter belongs at the ENTRY POINT (train_arm), not at the argv parser — a CLI-only refusal is bypassed by every programmatic caller"
    - "An end-to-end wiring test asserts each wiring by its OWN observation; 'the run did not crash' passes with three of four paths unwired"
    - "The mirror of a wiring threat needs its own control: a test that stubs the callee proves the CLI branch did not narrow and NOTHING about what the callee received"

key-files:
  created: []
  modified:
    - scripts/teach_persona.py
    - tests/test_phase22_wiring.py
    - src/personacore/training/loop.py

key-decisions:
  - "dp_sigma/dp_clip_norm ship as keyword-only with a `None` SENTINEL, not as required-no-default parameters. The plan's literal instruction makes all FIVE external train_arm callers a TypeError, and the plan's own refusal instruction ('if either is None on a DP arm, refuse') presupposes the sentinel. No sigma and no C value is named, so T-22-49 is unaffected"
  - "The DPSGD object is constructed AFTER `model.to(runtime.device)`, which the plan does not say and the code requires: `__init__` allocates its accumulator as `torch.zeros_like(p)` over the LIVE params, so a pre-move build pins the DP-owned sum on CPU while the params travel to MPS"
  - "The two gated splats are spelled `dict(...)`, not `{...}`. MEASURED: with string keys, 22-08's code-hit predicate read 0 against a file that plainly DID wire grad_accum_steps — the number in loop.py's refusal message would have stayed confidently wrong. This also satisfies the plan's own key_links patterns, which the string-key form contradicted"
  - "`runtime=runtime` is passed to DPSGD (not in the plan's literal call) so D-04 refusal 2 is armed on the P100 fallback; `seed=seed` makes the noise stream's provenance greppable"
  - "A DP-arm refusal was added at train_arm itself, not only at the CLI (Rule 2): five external callers bypass main() entirely"
  - "A non-DP end-to-end control ships because a mutation measured the gap — flipping the dp_kwargs guard to `if True` left the ENTIRE suite green"
  - "requirements.mark-complete was NOT called for DPSGD-01: the arm is wired and proven at fixture scale, but no real training run exists and DPSGD-06 is 22-11/23's"

patterns-established:
  - "dict(kw=...) for a gated kwarg splat, so static instruments see the wiring"
  - "Entry-point refusal over CLI refusal for resource parameters"
  - "A wiring test with one observation per wiring, plus the inverted control"

requirements-completed: []
requirements-contributed: [DPSGD-01, DPSGD-03]

# Metrics
duration: 60min
completed: 2026-08-26
---

# Phase 22 Plan 10: Wiring the Production Caller Summary

**`python scripts/teach_persona.py dp_n8 --sigma=<f> --clip-norm=<f>` now routes the aligned three-bin corpus through `get_batch_fact_aligned` at `grad_accum_steps = 8`, draws 32 public replay windows per lot, and releases a per-record-clipped, Gaussian-noised gradient — proven by an end-to-end CPU run through `main()` that completes in 0.94 s, asserts each of the four wirings by its OWN observation, and leaves `results/` byte-identical. 10 mutations, 10 distinct REDs, sha256-identical restore — and one of them was GREEN until a control this plan added.**

## Performance

- **Duration:** ~60 min
- **Tasks:** 3 (4 commits — the 4th is a measured correction, see *Deviations*)
- **Files:** 0 created, 3 modified (`teach_persona.py` +233/−6, `test_phase22_wiring.py` +497/−19, `loop.py` +7/−3)

## Accomplishments

- **All four D-08 paths are live on `dp_n8` / `dp_n64` and nothing else**, gated on ONE `is_dp` boolean and two `dict(...)` splats, so every v2.0/v3.0 arm's `train()` call is byte-unchanged — and that is now **asserted**, not argued (see M5 below).
- **The end-to-end run is real, not inspected.** `tp.main(["dp_n8", "--sigma=…", "--clip-norm=…"])` runs the actual packer, the actual `torch.load` of a base checkpoint, the actual LoRA injection + freeze + census, the actual `train()` with all four wirings, the actual canary, the actual `export_adapter`, and the actual adapter-on/off perplexity sweep — at fixture scale, on CPU, in **0.94 s**.
- **`dp_fn._records == 8` after a production-caller run.** V-13: D-16's invariants fired outside a unit test for the first time.
- **`replay_window_budget`'s docstring claim is true in BOTH directions.** IN-04 closed: the sentence named a caller that did not exist; wiring 3 makes it exist and the sentence was rewritten in the same diff to name `train_arm` rather than left as a claim that happened to become correct.
- **No numeric σ or C exists anywhere in `scripts/teach_persona.py`** — `grep -nE "sigma\s*=\s*[0-9]|clip_norm\s*=\s*[0-9]"` returns nothing, and an AST walk over `Assign` / `AnnAssign` / `keyword` / dict-entry / parameter-default proves it with two meta-guards.
- **`results/` is byte-identical before and after**, by BOTH fingerprints (`sorted(os.listdir)` and `git status --porcelain results/`), with a non-emptiness assertion so the comparison cannot be vacuous. Empty after the full suite too.
- `scripts/mitigation_gate.py`, `scripts/mitigation_unit.py`, `scripts/mitigation_accountant.py` and `pyproject.toml` are **byte-unchanged** (`git diff --exit-code` exits 0). Nothing was installed. No commit deleted a tracked file.
- Full suite **1259 → 1268 passed, 1 skipped** (+9, zero regressions), 216.94 s. `ruff` clean over **202 files**.

## Task Commits

1. **Task 1: the four wirings at the `train()` call, on the DP arms only** — `cd90520` (feat)
2. **Task 2: the no-default σ/C CLI contract and its six refusal shapes** — `255ff5d` (test)
3. **Task 3: V-23 — the end-to-end CPU run, plus the non-DP control the probe demanded** — `10f9283` (test)
4. **The `dict(...)` correction** — `9f430f8` (refactor) — see Deviation 3

Task 1's commit carries Task 2's CLI *code* as well: `dp_sigma` cannot arrive at `train()` without `main()` parsing it, and both are kwarg-chain edits to one function pair in one file. Task 2's commit carries its tests.

## Files Created/Modified

- `scripts/teach_persona.py` (+233 / −6) — the `DPSGD` import; `replay_window_budget`'s corrected docstring with the IN-04 note and the TOKENS→WINDOWS conversion stated; `train_arm`'s `dp_sigma`/`dp_clip_norm` parameters and their Args register; the `is_dp` gate and the σ/C refusal; the DP replay-source existence guard; the `DPSGD(...)` construction with its two ordering reasons; `dp_accum` / `dp_kwargs` with a per-wiring decision-id comment; `**dp_accum` inside `TrainConfig(...)` and `**dp_kwargs` at `train()`; the DP provenance print; `SIGMA_FLAG`/`CLIP_FLAG`, the extended `USAGE`, `_parse_dp_flags`, and `main()`'s DP branch.
- `tests/test_phase22_wiring.py` (+497 / −19, **12 → 21 collected**, 20 test functions, 6.56 s) — six CLI tests, the `_e2e_env` fixture-scale harness, `_results_state`, V-23, the non-DP control, the mismatched-accum caller test, and the re-measured prose/code assertion.
- `src/personacore/training/loop.py` (+7 / −3, **3 changed lines**) — the accum refusal's measurement only. **Scope deviation, see Deviation 1.**

## The Evidence

### The four wirings, measured at the production caller

`tp.main(["dp_n8", "--sigma=1.0", "--clip-norm=1.0"])` with a delegating spy on `tp.train` capturing the kwargs `train()` was actually handed, and a delegating spy on `loop_mod.get_batch_fact_aligned`:

| Wiring | Observation | Measured |
|---|---|---|
| 1. fact-aligned routing | the REAL loader fired | **16 calls** over `MAX_STEPS=2` × `n_facts=8`; each window's `fact_index` multiset `== [0..7]`; **16 distinct** `step=` values |
| 1. fact bin path | `seen["fact_bin"]` | `== tp.fact_bin_path(paths["bin"])`, the file that exists on disk |
| 2. `grad_accum_steps` | read off the `TrainConfig` `train()` received | **8**, against `TrainConfig().grad_accum_steps == 1` |
| 3. replay | `seen["replay_windows"]` | **32**, `== replay_window_budget(8) // BLOCK_SIZE` = `8,192 // 256`; `replay_bin`/`replay_mask_bin` are the PersonaChat train pair |
| 4. `dp_fn` | the object, after the run | `_records == 8`; `(sigma, C) == (1.0, 1.0)` — **the values the CLI parsed** |

Per arm, from `arm_spec` rather than a literal:

| Arm | `n_facts` | wired accum | wired `replay_windows` | budget (tokens) | `replay_ratio` |
|---|---|---|---|---|---|
| `dp_n8` | **8** | **8** | **32** | 8,192 | 0.0 |
| `dp_n64` | **64** | **64** | **256** | 65,536 | 0.0 |

Both arms clear 22-06's detectability constraint by measurement: `accum > 1` on both, so D-02's inherited-divide fake — structurally invisible at `accum = 1` because `total / 1` is `total` exactly — stays detectable for 22-11's positive controls.

### The prose-vs-code measurement, re-derived

| | before 22-10 | after 22-10 |
|---|---|---|
| textual `grad_accum_steps` in `teach_persona.py` | 9 | **14** |
| CODE hits (`ast.keyword`/`Attribute`/`Name`) | 0 | **1** — `dict(grad_accum_steps=stats["n_facts"])` |

`loop.py`'s refusal message was UPDATED to `14` / `exactly 1`; the test was not deleted, skipped or xfailed. It now also asserts the hit is the wiring line itself, not a prose string that happens to parse.

### `results/` — the D-08 boundary

Snapshotted by both fingerprints immediately before and after the end-to-end run, and asserted equal. Non-degeneracy: `assert before[0]` (the listing is non-empty). After the **full** suite, `git status --porcelain results/` is **empty**.

## Guards Watched Failing

Ten mutations against `scripts/teach_persona.py`, each applied to the work-tree file and restored in a `finally`. Restore verified by sha256: **`5106ba44f448d0892567443b41bad731b0a54db304b45f96271ba8f96b1699bb` before and after.** Probe target: `tests/test_phase22_wiring.py tests/test_phase14_teaching.py`.

| # | Mutation | Result | Guard(s) reddened |
|---|---|---|---|
| M0 | control | **63 passed** | — |
| M1 | `fact_bin=`/`n_facts=` dropped | 2 failed | V-23 + the mismatched-accum caller test |
| M2 | `grad_accum_steps` dropped | 2 failed | V-23 + `test_the_prose_vs_code_measurement_is_still_true` |
| M3 | the replay seam dropped | 1 failed | V-23, at `KeyError: 'replay_windows'` |
| M4 | `dp_fn=` dropped | 1 failed | V-23, at `KeyError: 'dp_fn'` |
| M5 | **the wirings made UNCONDITIONAL (non-DP arms too)** | **GREEN → after the new control: 1 failed** | `test_a_non_dp_arm_reaches_train_with_NONE_of_the_four_wirings` |
| M6 | the σ/C refusal dropped | 1 failed | `test_the_dp_refusal_also_fires_at_train_arm_not_only_at_the_cli` |
| M7 | `dp_sigma=1.0` / `dp_clip_norm=1.0` defaults | 2 failed | the AST no-literal test + the entry-point refusal test |
| M8 | `DPSGD` built BEFORE `mark_only_lora_trainable` | 3 failed | the non-DP control, the mismatched-accum test, V-23 |
| M9 | `replay_windows` in TOKENS (`// BLOCK_SIZE` dropped) | 1 failed | V-23, at `assert 8192 == 32` |
| M10 | `accum = n_facts + 1` (a caller-side skew) | 1 failed | V-23, via `loop.py`'s production `ValueError` raised **through `main()`** |

**M5 was GREEN and it changed what shipped.** Flipping `dp_kwargs`' guard from `if is_dp` to `if True` — so `real`, `cal_first_person`, `cal_first_person_replay` and `cal_second_person` all get the fact bin, the replay seam and the DP lot size — left the **entire suite green (62 passed)**. The reason is structural: `test_non_dp_arm_cli_is_unchanged` stubs `train_arm` out entirely, so it proves the CLI branch did not narrow and *nothing* about what the callee received. **No test looked at a non-DP arm's `train()` call at all.** T-22-48 is "a DP-named arm producing a non-DP adapter"; its mirror — a non-DP arm silently becoming a DP one — had no guard. `test_a_non_dp_arm_reaches_train_with_NONE_of_the_four_wirings` now runs a real non-DP arm end to end and reads the kwargs.

**M3, M4, M9 and M10 share a test name but hit four different assertions** — verified individually and recorded above rather than reported as "one guard caught four mutations".

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `dp_sigma`/`dp_clip_norm` as required-no-default parameters make all five external `train_arm` callers a `TypeError`**

- **Found during:** Task 1
- **Issue:** The plan mandates both *"keyword-only with no default"*. Measured, `train_arm` has **five** call sites outside `main()` — `scripts/phase17_isolation.py:1138`, `scripts/phase19_erasure.py:3528/3630/3701`, `scripts/phase19_run.py:1646` — plus `run_calibration` in this file. None passes a DP arm; every one would raise `TypeError: missing 2 required keyword-only arguments`. The plan is also internally contradictory here: its next sentence says *"If either is `None` on a DP arm, refuse"*, which presupposes `None` is reachable.
- **Fix:** `dp_sigma=None, dp_clip_norm=None` keyword-only **sentinels**, with the `SystemExit` refusal the plan itself specifies. `None` names no σ and no C, so T-22-49's no-literal property is untouched, and the docstring records why the sentinel is not a default value.
- **Verification:** M7 (numeric defaults) watched RED across two tests; the full suite's Phase-17/19 tests stay green.
- **Committed in:** `cd90520`

**2. [Rule 1 - Bug] Constructing `DPSGD` where the plan says would pin the accumulator on the wrong device**

- **Found during:** Task 1
- **Issue:** The plan says construct *"after `mark_only_lora_trainable(model)` at `:1147` and after the existing census at `:1148-1156`"*. `DPSGD.__init__` allocates `self._accum = [torch.zeros_like(p) for p in params]` over the LIVE trainable params, and `train_arm` moves the model with `model.to(runtime.device)` **after** that census. Constructing where the plan says pins the DP-owned sum on CPU while the parameters travel to MPS; `buf.add_(contribution)` then raises mid-run — on the primary M3 path, i.e. every real run.
- **Fix:** constructed after `model.to(runtime.device)`, which is still after the freeze and the census (the plan's stated acceptance criterion, *"appears AFTER `mark_only_lora_trainable(model)` in file order"*, holds). Both ordering reasons are recorded in the source.
- **Verification:** M8 (construct before the freeze) watched RED across three tests, confirming the freeze-ordering half is still guarded.
- **Committed in:** `cd90520`

**3. [Rule 1 - Bug] A dict-STRING-KEY splat is invisible to the instrument that measures it**

- **Found during:** Task 1 verification, corrected in `9f430f8`
- **Issue:** The plan mandates a single `dp_kwargs = {...} if arm in DP_ARMS else {}` splat, and separately its `key_links` and Task-1 acceptance criteria require the literal patterns `fact_bin=`, `n_facts=`, `replay_windows=`, `dp_fn=`. With `{"key": value}` **none** of those appear. Worse: 22-08's `test_the_9_in_prose_0_in_code_measurement_is_still_true` counts code hits by `ast.keyword`/`Attribute`/`Name`, and against the wired file it still returned **0 code hits** — a detector reporting "the caller never sets this" about a caller that does. My first fix was to widen the predicate; the better fix is to spell the wiring so it is visible.
- **Fix:** both gated dicts use `dict(kw=value, ...)`. Same single splat, same `is_dp` gate, but every entry is a real `ast.keyword` — so the plan's four link patterns appear literally AND the 22-08 instrument works unwidened. The `ast.Constant` arm stays in the test helper as the guard against the string-key spelling coming back, with the measurement that motivated it recorded in its docstring. `ruff`'s `C4` rules are not enabled (`select = ["E", "F", "W", "I"]`), so `dict()` is not flagged.
- **Verification:** original predicate now reads **1** code hit; both tests re-run green; all ten mutations re-run against the shipped bytes.
- **Committed in:** `9f430f8`

**4. [Rule 2 - Missing critical functionality] The σ/C refusal existed only at the CLI**

- **Found during:** Task 2
- **Issue:** The plan puts the required-argument contract in `main()`. Five callers bypass `main()` entirely (deviation 1's list). A DP arm reached through any of them would have trained with `dp_sigma = None` and crashed inside `DPSGD.__init__`'s `float(None)` — a `TypeError` naming nothing, rather than a refusal naming Phase 20's Z boundary.
- **Fix:** the refusal lives at `train_arm`, the entry point, and the CLI's two domain refusals are the early, cheap copy the mechanism re-checks.
- **Verification:** `test_the_dp_refusal_also_fires_at_train_arm_not_only_at_the_cli`; M6 watched RED.
- **Committed in:** `cd90520`

**5. [Rule 2 - Missing critical functionality] A DP arm with no replay source fails after writing recorded evidence**

- **Found during:** Task 1
- **Issue:** Under D-10 replay is drawn at TRAIN time, so a missing `data/dialog_train.bin` surfaces inside `train()`'s `replay_fn` — *after* `build_arm_bins` has written three bins that `refuse_if_exists` then treats as recorded evidence, forcing the operator to delete them by hand before retrying. The existing `DIALOG_VAL_BIN` guard has exactly this shape and exactly this reason.
- **Fix:** the same guard, hoisted above the bins build, DP-arms only.
- **Committed in:** `cd90520`

**6. [Rule 2 - Missing critical functionality] The wirings' inverse had no guard — measured, not suspected**

- **Found during:** Task 3's mutation probe (M5)
- **Issue:** See *Guards Watched Failing*. The whole suite stayed green with every non-DP arm wired for DP.
- **Fix:** `test_a_non_dp_arm_reaches_train_with_NONE_of_the_four_wirings` runs a real non-DP arm end to end and asserts `train()` received none of the five kwargs, `dp_fn is None`, `grad_accum_steps == TrainConfig().grad_accum_steps` (resolved from the dataclass, never re-spelled as `1`), and the fact-aligned loader fired **0** times.
- **Committed in:** `10f9283`

**7. [Rule 3 - Blocking] `make test` / `make lint` still do not resolve the venv**

- **Found during:** verification
- **Issue:** The `Makefile` invokes bare `pytest` / `ruff`, which resolve to a pyenv 3.12.13 with no torch. **Ninth** confirmation (22-01…22-08). Task 3's acceptance criterion literally says `make lint` exits 0; it cannot on this box.
- **Fix:** all verification ran through `.venv/bin/`. `.venv/bin/ruff check . && .venv/bin/ruff format --check .` is clean over **202 files**. The `Makefile` is untouched — out of scope.
- **Committed in:** n/a

**8. [Rule 1 - Bug] `gsd-sdk` mutation-handler defects, hand-repaired before commit** — see *Tooling Corruption Encountered*.

### Scope deviation

**`src/personacore/training/loop.py` is not in this plan's `files_modified`, and it was modified.** Three lines, inside the accum-agreement refusal's message string only. The plan's prompt sanctioned exactly this: 22-08 baked a MEASUREMENT (`9 times in prose, 0 in code`) into a production error string and shipped a test that re-derives it, predicting this plan would legitimately turn it red. It did. The correct fix is to update the number, and the alternative — deleting, skipping or `xfail`ing the test — would leave a false number in a message a user reads while debugging a privacy claim. No behaviour changed: `git diff` shows 3 removed lines, all inside the same f-string.

### Deliberate departures from the plan text

- **Two gated dicts, not one.** `grad_accum_steps` belongs to the `TrainConfig` constructor and the other four to `train()`; they cannot ride one splat. Both are keyed on the SAME `is_dp` boolean, so the DP/non-DP boundary is still one readable predicate and M5's control now proves a partial wiring cannot ship.
- **`n_facts` is read from `stats["n_facts"]`, not `len(facts)`.** The accum, the declared lot size and the replay budget all come from the packer's own record count, so a caller-side skew between "what the arm declares" and "what the bin contains" is structurally impossible. `fact_bin` uses `fact_bin_path(paths["bin"])` — the plan's primary form, in the same register as its two sibling kwargs on the same call, and provably the same string the packer wrote.
- **`runtime=runtime` and `seed=seed` are passed to `DPSGD`**, neither in the plan's literal call. The first arms D-04 refusal 2 (an AMP-scaled `.grad` read mid-accumulation is wrong by the scale factor, silently) on the P100 fallback; the second makes the noise stream's provenance greppable rather than an implicit read of `torch.initial_seed()`. Both are the values that path would have used anyway.
- **A DP provenance line is printed** (arm, σ, C, `n_facts`, accum, `replay_windows`, last-lot `_records`, run-lifetime `_clip_bind_count`). A DP run whose stdout does not record its budget is a privacy claim with no provenance, and this file's entire register is per-run provenance. Non-DP arms' output is byte-unchanged.
- **`grep -n "argparse"` returning nothing is NOT satisfied, deliberately.** `_parse_dp_flags`' docstring names the rejected alternative — this file's established "rejected alternatives" register. The grep cannot distinguish a use from a rejection note, so `test_the_cli_does_not_use_argparse` asserts the load-bearing property by AST instead (no `Import`/`ImportFrom` of `argparse`, no `argparse.` attribute access, no module attribute) — strictly stronger than the grep. Precedent: 22-06 deviation 5.
- **`MAX_STEPS = 2` in the end-to-end harness, not 1**, and the reason is a measurement. LoRA initialises `lora_B` to zeros and `dL/dA` carries a factor of `B`, so at step 0 every `lora_A` gradient is exactly `0.0` and `train_arm`'s canary correctly raises. Watched: the **DP arm passes that canary at one step and the non-DP arm does not**, because the DP path adds noise to every parameter's gradient. Two steps makes both arms legitimate for the same reason.
- **The test drives `main()` through `tp.main([...])`, and CPU is forced explicitly.** `preflight_device(strict=True)` returns MPS on this box and RAISES on a CPU-only CI runner, so both it and `RuntimeConfig` are replaced — the test must run identically on both.
- **The test-count criterion (≥ 11) is met at 21 collected**, against the plan's arithmetic of 6 + 4 + 1. The file started at 12 collected, not 6; six CLI tests shipped rather than four (the entry-point refusal and the argparse guard are additions), and three end-to-end tests rather than one.
- **Line anchors inside new code are cited by SYMBOL, never by line number**, continuing 22-02…22-09's habit.

---

**Total deviations:** 8 auto-fixed (1 signature that breaks five callers, 1 device-ordering bug, 1 invisible-to-its-own-instrument wiring, 3 missing guards, 1 blocking environment issue, 1 tooling corruption), 1 sanctioned scope deviation, 8 deliberate departures.
**Impact on plan:** every correction makes a guard bite more, a claim narrower and truer, or an instruction actually executable; none weakens a guard or widens a claim. No scope creep — `pyproject.toml`, `privacy/`, `data.py` and all three frozen `scripts/mitigation_*.py` are byte-unchanged.

## Tooling Corruption Encountered

Nineteenth consecutive session. Every `gsd-sdk` mutation call used the `--flag` form and was followed by `git diff` on the three planning files, hand-repaired before the metadata commit. `22-10-SUMMARY.md` was written to disk **before** `roadmap.update-plan-progress` ran (the 22-06 workaround), so the handler counted 10 summaries and wrote the count and the checkbox correctly.

| Handler | Defect observed | Repair |
|---|---|---|
| `state.advance-plan` | rewrote `Status: Executing Phase 22` back to `Status: Ready to execute` — identical to 22-01…22-09 | restored by hand |
| `roadmap.update-plan-progress 22` | wrote the status cell as `In Progress\|  \|` — no space before the pipe, empty date cell where every sibling carries `-` | corrected to `\| 10/11 \| In Progress \| - \|` |
| `state.add-decision --summary` | prefixed all four entries `- [Phase ?]:` | prefix corrected; `grep -c "Phase ?"` → **0** |
| `state.update-progress` | `{"updated": false, "reason": "Progress field not found in STATE.md"}` against a frontmatter that plainly has one | harmless; `advance-plan` had already set the block |
| `state.record-metric --flag` / `state.record-session --stopped-at` | **correct** under the `--flag` form | — |

Seventh consecutive confirmation that the corruption lives in the **positional** argument path. `completed_plans: 37 → 38` was verified against `ls .planning/phases/*/*-SUMMARY.md | wc -l` = **38** before being accepted.

**One in-place correction to `REQUIREMENTS.md`, not a handler defect (Rule 1).** UNIT-04's traceability row stated *"IN-04 REMAINS OPEN AND IS SCOPED HONESTLY: the seam has NO production caller … there is no such caller in today's tree."* This plan makes that false. A dated closure note was appended naming the caller, the measured budgets (32 windows at n=8, 256 at n=64) and the test; the original sentences are left unamended as the record of what was true when Phase 21 closed. Precedent: 22-06 deviation 4.

## Issues Encountered

- **The `.gitignore` modification present at session start is pre-existing and untouched** — not staged in any commit here.
- **M9 takes 76 s** under mutation (replay in TOKENS means 8,192 windows per optimizer step instead of 32). That is the mutation, not the shipped code: the shipped path is 32 windows and the file runs in 6.56 s.
- **`requirements.mark-complete` was deliberately NOT called.** DPSGD-01's production caller is now wired and proven at fixture scale, but no real training run exists and DPSGD-06's *"a DP-correctness bug and a wiring bug must be distinguishable"* endpoint is 22-11's and Phase 23's. DPSGD-03 is contributed, not completed.

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest tests/test_phase22_wiring.py -q` | **21 passed** in 6.56 s (was 12) — under `22-VALIDATION.md`'s 30 s max feedback latency |
| Full suite `.venv/bin/python -m pytest -q` | **1268 passed, 1 skipped** in 216.94 s (baseline 1259/1, +9, zero regressions) |
| `git status --porcelain results/` after the full suite | **empty** |
| `grep -n "dp_accum = dict"` | `:1352` — a CODE line whose value reaches `TrainConfig(...)` via `**dp_accum` |
| `grep -n "fact_bin=fact_bin_path\|n_facts=stats\|replay_windows=replay_window_budget\|dp_fn=dp_fn"` | `:1364`, `:1365`, `:1373`, `:1374` — **all four** |
| `grep -nE "sigma\s*=\s*[0-9]\|clip_norm\s*=\s*[0-9]" scripts/teach_persona.py` | **nothing** |
| `replay_window_budget`'s docstring | names `:func:`train_arm``; the old false claim is quoted and marked closed |
| `mark_only_lora_trainable(model)` / `model.to(runtime.device)` / `DPSGD(` | `:1277` / `:1291` / `:1319` — construction is after BOTH |
| `USAGE` interpolation | `'\|'.join(ARMS)` at `:996` and `'\|'.join(DP_ARMS)` at `:997` — never hand-typed |
| `.venv/bin/python scripts/teach_persona.py dp_n8` | exit **1**, message names `--sigma=`, `--clip-norm=`, `NO DEFAULT` and Phase 20's Z boundary |
| `argparse` import / attribute / module attr | **absent** (AST-asserted; one docstring mention names the rejected alternative) |
| Mutation probe | **10 mutations, 10 distinct REDs**, control GREEN, sha256-identical restore |
| `git diff --exit-code -- mitigation_{gate,unit,accountant}.py pyproject.toml` | exit **0** — byte-unchanged |
| `git diff --diff-filter=D` on all four commits | **no deletions** |
| `.venv/bin/ruff check . && .venv/bin/ruff format --check .` | clean, **202 files** |

## Known Stubs

None. Every kwarg wired is consumed by a committed observation, every refusal is watched failing, and no placeholder was left. What this plan does **not** deliver, stated so no reader infers it: **no real training run exists.** The arms are wired and proven at fixture scale (2 optimizer steps, `n_embd = 16`, a synthetic base checkpoint); `python scripts/teach_persona.py dp_n8 --sigma=… --clip-norm=…` at production scale has never been executed, and Phase 23 supplies the σ and C it would need. Wiring is not executing — that is D-08's boundary and it is why this plan costs nothing against the roadmap's no-M3-time constraint.

## Threat Flags

None. No network endpoint, no auth path, no schema change. Two new file-access patterns, both reads of this project's own gitignored corpora through paths that already existed as module constants (`DIALOG_TRAIN_BIN` / `DIALOG_TRAIN_MASK`, previously read only by `_prepend_replay` at build time). Nothing was installed; `pyproject.toml` is byte-unchanged.

Threat register dispositions, each mitigated as planned:

- **T-22-48** (a DP-named arm producing a non-DP adapter) — all four wirings land together on `DP_ARMS`, each asserted by its own observation in V-23; M1/M2/M3/M4 each watched RED, and dropping any single one reddens.
- **T-22-49** (a default σ or C silently becoming the operating budget) — no default at the CLI, at `train_arm`, or in the constructor; `SystemExit` on omission naming Phase 20's Z boundary at BOTH the CLI and the entry point; the AST test proves no numeric literal exists, with two meta-guards. M6 and M7 watched RED.
- **T-22-50** (a Phase-22 write under `results/`) — V-23 snapshots `git status --porcelain results/` and the listing before and after and asserts byte-identity, with a non-emptiness assertion; the full suite leaves it empty.
- **T-22-51** (an end-to-end test green because it only checks "no crash") — four separate positive observations plus the deliberate mismatch case observed raising `loop.py`'s production `ValueError` **through `main()`** (M10).
- **T-22-52** (the new CLI branch narrowing the existing non-DP path) — `test_non_dp_arm_cli_is_unchanged` is the control, **and it was measured insufficient**: M5 stayed green through it. `test_a_non_dp_arm_reaches_train_with_NONE_of_the_four_wirings` is the control that actually bites.
- **T-22-53** (`replay_window_budget`'s docstring claiming a caller that does not exist) — the claim is made TRUE by wiring 3 and the docstring is corrected in the same diff, quoting the old sentence and naming the plan. IN-04 closed in both directions.
- **T-22-SC** (package installs) — accepted; nothing installed, `pyproject.toml` byte-unchanged.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plan 22-11's positive controls can now run against the REAL arms, at `accum > 1`.** Measured: `dp_n8` → `n_facts = 8`, accum 8, 32 replay windows; `dp_n64` → 64, 64, 256. D-02's inherited-divide fake is detectable on both because neither runs at `accum = 1`. Do not construct a one-fact arm — `n_facts = 1` re-opens the blind spot.
- **Phase 23 supplies σ and C, and there is nothing to override.** No numeric value for either exists anywhere in Phase 22's tree; `python scripts/teach_persona.py {dp_n8|dp_n64} --sigma=<f> --clip-norm=<f>` is the interface, and both are refused at the CLI *and* at `train_arm`, so a programmatic caller cannot bypass the contract.
- **The end-to-end harness is reusable and is `_e2e_env` in `tests/test_phase22_wiring.py`.** It monkeypatches the module's OWN shape constants — `MAX_STEPS`, `WARMUP_STEPS`, `BATCH_SIZE`, `EVAL_INTERVAL`, `CHECKPOINT_INTERVAL`, `_REPO_ROOT`, the four corpus constants, `FACTSET_REPORT`, `CONVBASE_BEST`, `preflight_device` and `RuntimeConfig`. **`BLOCK_SIZE` is deliberately NOT scaled**: the packer packs at `tp.BLOCK_SIZE` and the aligned loader derives its window count from `model_cfg.block_size`, so a skew would mis-attribute windows to privacy records.
- **A control that stubs the callee proves nothing about what the callee received.** M5 is the concrete instance: `test_non_dp_arm_cli_is_unchanged` passed through a mutation that wired every arm for DP. Any future "X is unchanged" test should be checked against that shape before it is trusted.
- **Anything that re-measures `grad_accum_steps` in `teach_persona.py` must count `ast.Constant` string keys too.** The predicate is `tests/test_phase22_wiring.py::_accum_code_hits` and the reason is in its docstring: the dict-key spelling was measured invisible to the three-arm predicate during this plan.
- **`train_arm`'s `dp_sigma`/`dp_clip_norm` are `None` sentinels, not defaults.** A future plan that "tightens" them into required parameters breaks five callers in `phase17_isolation.py`, `phase19_erasure.py` and `phase19_run.py`, none of which passes a DP arm.

## Self-Check: PASSED

- `scripts/teach_persona.py` — FOUND
- `tests/test_phase22_wiring.py` — FOUND
- `src/personacore/training/loop.py` — FOUND
- `.planning/phases/22-dp-sgd-core-accountant-and-the-correctness-battery/22-10-SUMMARY.md` — FOUND
- commit `cd90520` — FOUND
- commit `255ff5d` — FOUND
- commit `10f9283` — FOUND
- commit `9f430f8` — FOUND

---
*Phase: 22-dp-sgd-core-accountant-and-the-correctness-battery*
*Completed: 2026-08-26*
