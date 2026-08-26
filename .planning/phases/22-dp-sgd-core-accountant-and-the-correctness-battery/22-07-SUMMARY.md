---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
plan: 07
subsystem: checkpoint
tags: [differential-privacy, dp-sgd, checkpoint, mps-rng, backward-compatibility, lora, bit-identity]

# Dependency graph
requires:
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-06's dp_noise_rng slot — the _dp_extra() closure at all three save sites and the .get()-guarded restore in train()'s resume_from block. This plan exercises that wiring end-to-end rather than re-deriving it"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-05's accountant.epsilon_for(sigma, steps, delta) and its TOLERANCE REGISTER — the recorded justification for exact == here"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-04's DPSGD — noise_rng_state / load_noise_rng_state and the dedicated generator whose CPU state is 5,056 bytes"
  - phase: 09-lora-from-scratch
    provides: "LoRALinear's bare nn.Parameter shape, export_adapter/load_adapter, and load_adapter_weights' key+shape+scale audit — the artifact contract DPSGD-07 forbids breaking"
provides:
  - "src/personacore/checkpoint.py::save_checkpoint's rng['mps'] slot, beside cuda in the identical None-when-unavailable shape"
  - "src/personacore/checkpoint.py::load_checkpoint's rng.get('mps') restore — the None-safe read that keeps every pre-Phase-22 checkpoint loadable"
  - "checkpoint.py's module-docstring TWO-SLOT REGISTER — rng['mps'] recorded as required-but-unexercised, dp_noise_rng named as the slot the DP path fires, each figure carried WITH its device"
  - "tests/test_phase22_checkpoint.py — V-15, V-16, V-17; 12 tests, 0 -> 12"
  - "the measured finding that a key-set round trip is SYMMETRIC under a co-moving rename, and the v3.0 key-form literal that closes it"
affects: [22-08 wiring teach_persona.py's DP arms, 22-09 the four fake probes, 23 the frontier sweep and every published epsilon]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "An asymmetry between two adjacent lines (rng['cuda'] subscript vs rng.get('mps')) is CORRECT when the keys have different ages, and the reason belongs in the source at the site — not smoothed into consistency"
    - "A reported quantity must be computed over WHAT RAN, not over a field in a file: T is the count of composed steps, because a step-counter reset leaves the field right and the composition wrong"
    - "A round trip between two co-moving sides is blind to a rename that moves both; the shipped FORM has to be pinned as a literal for the property to survive a restructuring"
    - "Every on-disk leg gated on its own existence via pytest.param(marks=skipif(...)), with a collection meta-guard on the declared case count so an empty directory reports N skips rather than nothing"

key-files:
  created:
    - tests/test_phase22_checkpoint.py
  modified:
    - src/personacore/checkpoint.py
    - .planning/REQUIREMENTS.md

key-decisions:
  - "The plan's requirement that the resumed seam's generator state equal the state saved at the kill point is only satisfiable when the resume takes ZERO further steps, which contradicts the same task's 'resume for the remaining steps'. Solved for intent and shipped the STRONGER form: the uninterrupted arm's and the resumed arm's NEXT NOISE DRAWS are torch.equal end-to-end. 22-06 already pins the narrower zero-step form"
  - "T is read from the COUNT OF COMPOSED STEPS, not from the checkpoint's `step` field. Measured (mutation M6): with start_step reset to 0 the resumed arm composes 6 steps while its checkpoint still records 4, so a field-read epsilon is IDENTICAL across the arms and optimistic. Rule 2"
  - "The key-set round trip alone does NOT catch the restructuring DPSGD-07 forbids — measured, mutation M7 left it GREEN because donor and fresh model move together. The v3.0 key FORM (…lora_A / …lora_B) is now pinned as a literal, and M7 reddens in both the local and the CI shape. Rule 2"
  - "The MPS-gated row RAN on this box rather than skipping (Darwin/arm64, torch.backends.mps.is_available() is True). It is recorded as exercised HERE and required-but-unexercised in CPU-only CI — the two are different statements and neither is substituted for the other"
  - "requirements.mark-complete WAS called for DPSGD-05 and DPSGD-07; both requirement texts are fully and provably satisfied and nothing downstream changes them"

patterns-established:
  - "Key-form literal: pin the shipped state-dict key SUFFIX, not just set-equality between two sides built by the same code"
  - "Composed-step count over checkpoint field: a published composition parameter is read from invocations, never from a serialized counter"

requirements-completed: [DPSGD-05, DPSGD-07]
requirements-contributed: []

# Metrics
duration: 32min
completed: 2026-08-25
---

# Phase 22 Plan 07: The MPS RNG Slot and the Kill→Resume ε Summary

**A kill→resume through `train(resume_from=…)` reproduces ε = `9.9972561464343` (`0x1.3fe985b8d5732p+3`) bit-for-bit at σ=1.0 and `inf` at σ=0.0, with a negative control proving the noise generator — not just the number — resumed; and `rng["mps"]` lands with a `.get()` restore that keeps `checkpoints/latest.pt` (step 50,000, `rng` keys `{python, numpy, torch, cuda}`) loading unchanged.**

## Performance

- **Duration:** ~32 min of execution (first commit `f8969d0` at 2026-08-25T20:53-03:00, last task commit `02c90b1` at 21:03; ~50 min including the pre-task reads from `0500598` at 20:32)
- **Tasks:** 3
- **Files:** 1 created, 2 modified

## Accomplishments

- **`rng["mps"]` saves beside `cuda` and restores through `.get()`.** `CKPT_SCHEMA_VERSION` is still `1`. The asymmetry with the `rng["cuda"]` subscript one line above is spelled out **in the source at the site** rather than smoothed away: `cuda` has existed since schema v1, `mps` arrives now.
- **The backward-compatibility claim rests on a REAL old artifact, not a lookalike.** `checkpoints/latest.pt` (step 50,000) has `rng` keys exactly `{'cuda', 'numpy', 'python', 'torch'}` — measured, no `mps`. The binding in-test leg additionally asserts the synthesized fixture's key set equals that same real set, so the two agree.
- **V-15 is a bit-identity claim with the bits shown.** See the ε table below, including the IEEE-754 hex.
- **The RNG half is separated from the ε half and said out loud.** ε is a function of (σ, T, δ) and **not** of the RNG, so ε bit-identity alone cannot prove the generator resumed. The negative control deletes `dp_noise_rng` at the production boundary and watches the next noise draw diverge.
- **`src/personacore/lora/` is byte-unchanged** (`git diff --exit-code` exits 0), as is `pyproject.toml`. DPSGD-07 and RPT-03 hold; nothing was installed.
- **Six mutations, six distinct RED signatures, three byte-identical restores** (sha256 verified on `checkpoint.py`, `loop.py`, `layer.py`). Two of them changed what shipped.
- Full suite **1231 → 1243 passed, 1 skipped** (+12, zero regressions). `ruff` clean over **201 files**.

## Task Commits

1. **Task 1: the `rng["mps"]` slot, saved beside `cuda` and restored None-safely (V-16)** — `f8969d0` (feat)
2. **Task 2: V-15 — a kill→resume through `train(resume_from=…)` reproduces a bit-identical ε** — `a0c2407` (test)
3. **Task 3: V-17 — `LoRALinear` unrestructured; a v3.0 adapter round-trips, on-disk legs gated** — `02c90b1` (test)

## Files Created/Modified

- `src/personacore/checkpoint.py` (+61 / −2) — the module docstring gains the **TWO-SLOT REGISTER** (D-14) naming `rng["mps"]` and `dp_noise_rng` apart and refusing to collapse them, with every device-dependent figure carried WITH its device; the `mps` save line beside `cuda`; the `.get()` restore with its asymmetry reasoning; `save_checkpoint`'s and `load_checkpoint`'s docstrings updated.
- `tests/test_phase22_checkpoint.py` (**new**, 713 lines, **12 tests**) — V-16 ×3 (+ the `**extra` / schema / clash test), V-15 ×2 (parametrized on σ), V-17 ×3 + a collection meta-guard, and the 3-case on-disk parametrization.
- `.planning/REQUIREMENTS.md` — DPSGD-05 and DPSGD-07 checked off with their traceability rows written by hand (see *Tooling Corruption*).

## The Evidence

### V-15 — the two ε values at full precision, and how the kill→resume was performed

Fixture: a tiny `GPT(ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16))` + `inject_lora(r=4)` + `mark_only_lora_trainable`, CPU, `grad_accum_steps = 2`, finite non-binding `clip_norm = 1e6`, δ = `1e-5`. **Arm A** is one `train(max_steps_override=4)` call. **Arm B** is `train(max_steps_override=2)` → *kill* (model + optimizer + `DPSGD` all reconstructed fresh, `tests/test_resume_curve.py`'s pattern; `train()` builds its own optimizer, so state crosses only through the checkpoint) → `train(resume_from=<that checkpoint>, max_steps_override=4)`.

| σ | arm | T (composed steps) | ckpt `step` | reported ε (`repr`) | ε (`float.hex`) |
|---|---|---|---|---|---|
| 1.0 | uninterrupted | 4 | 4 | `9.9972561464343` | `0x1.3fe985b8d5732p+3` |
| 1.0 | kill@2 + resume | 4 (2+2) | 4 | `9.9972561464343` | `0x1.3fe985b8d5732p+3` |
| 1.0 | — | | | **`epsilon_a == epsilon_b` → True** | identical mantissa + exponent |
| 0.0 | uninterrupted | 4 | 4 | `inf` | — |
| 0.0 | kill@2 + resume | 4 (2+2) | 4 | `inf` | — |
| 0.0 | — | | | **`epsilon_a == epsilon_b` → True** (`inf == inf`) | — |

**Non-degeneracy, σ=1.0 only:** `epsilon_for(1.0, 2, 1e-5) = 6.572970067030331` ≠ `9.9972561464343`, so ε genuinely moves with T and the equality is not green over a constant. **That control cannot exist at σ=0** — ε is `inf` for every T there — which is exactly why it lives on the σ>0 row and is stated rather than silently omitted.

**This is not a loss-curve comparison and is not offered as one.** No parameter or loss value is compared anywhere in V-15.

### The RNG half — what ε is structurally blind to

| Check | σ = 1.0 | σ = 0.0 |
|---|---|---|
| next draw, uninterrupted vs resumed (`torch.equal`) | **True** | **True** |
| first three values of that draw | `1.06912, -1.483205, -1.892289` | identical (the probe draws at std = 1.0, not at the arm's σ) |
| **negative control** — `dp_noise_rng` deleted from the checkpoint | **False** (`-1.255206, 1.22789, -0.570479`) | **False** (same) |
| dedicated generator state, CPU | 5,056 bytes | 5,056 bytes |

The probe draws at `std = 1.0` rather than at the arm's σ **on purpose**: at σ=0 every released value is exactly zero, so comparing released *values* could never see a stream that resumed at the wrong position — while the generator still advances. That makes the σ=0 row carry the same evidence as the σ>0 one instead of being decorative.

### V-16 — the backward-compatibility artifact, measured

| Check | Result |
|---|---|
| `checkpoints/latest.pt` `rng` keys | `['cuda', 'numpy', 'python', 'torch']` — **no `mps`**, step 50,000 |
| `checkpoints/phase14_real_latest.pt` (smallest `*latest.pt`, 59.7 MB) `rng` keys | same four; 72 `lora_` keys; loads through production `load_checkpoint` in 0.28 s |
| in-test pre-Phase-22 fixture key set | asserted `== {python, numpy, torch, cuda}` — the same real set |
| `CKPT_SCHEMA_VERSION` after the change | **1** |
| MPS state size on this box | 44 bytes; `set_rng_state` round-trips exactly |
| `git ls-files checkpoints/` | **0** files; `.gitignore:14-15` = `checkpoints/`, `*.pt` |

**D-14, recorded honestly.** `torch.backends.mps.is_available()` is **True** on this box (Darwin/arm64, torch 2.7.1), so `test_mps_rng_slot_round_trips` **RAN here rather than skipping** — 12 passed, 0 skipped locally. In CPU-only CI it **will skip**, and the slot stays **required-but-unexercised by the DP path everywhere**, because D-07 locked a dedicated generator whose draw does not move the global MPS state. Those are three different statements and none is substituted for another. The skip `reason=` names `test_old_checkpoint_without_mps_slot_still_loads` and `test_resume_epsilon_bit_identical`'s negative control as what still carries the guarantee.

### With `checkpoints/` absent — the CI shape, executed

Run with the working directory pointed at an empty scratch dir (so `pathlib.Path("checkpoints")` resolves to nothing):

```
8 passed, 4 skipped in 1.44s
```

Zero failures. The 4 skips are the on-disk back-compat leg plus the three V-17 artifact cases; the MPS row still ran. V-17 — DPSGD-07's only validation row — is carried entirely by the two non-skipping legs there.

## Guards Watched Failing

Every mutation was applied to the work-tree source and restored in a `finally`, with sha256 asserted identical before and after. **Three source files, three verified restores:**
`checkpoint.py` `658efb5a814bd933f965511919aa144e1cc33b2c4ce9a257c851e7948593c99a`, `loop.py` `ee063ee00025b2fdbe38b1962072a75dc4047d10408eedcc795a5580d82d98aa`, `layer.py` `f21c7847d9a02ad8a19cdb891b3c995417904583e50cfc0bbf7a5f1b2cbe2daa` — each unchanged.

| # | Mutation | Result | Guard(s) reddened |
|---|---|---|---|
| 0 | control | **12 passed** (local) / 8 passed + 4 skipped (CI shape) | — |
| M1 | `rng.get("mps")` → `rng["mps"]` (the subscript) | 2 failed | `test_old_checkpoint_without_mps_slot_still_loads`, `test_old_on_disk_checkpoint_still_loads` |
| M2 | the `mps` SAVE line dropped | 2 failed | `test_mps_rng_slot_round_trips`, `test_old_checkpoint_without_mps_slot_still_loads` (its "the modern save really carries the key" meta-guard) |
| M3 | the `mps` RESTORE block dropped (a write-only slot) | 1 failed | `test_mps_rng_slot_round_trips` |
| M4 | `loop.py`'s `resume_from` restore dropped | 2 failed | `test_resume_epsilon_bit_identical[1.0]` and `[0.0]` — on the next-draw equality |
| M5 | the **END-OF-CALL** `**_dp_extra(),` splat dropped | 2 failed | both σ rows — on the END-OF-CALL `dp_noise_rng` meta-guard |
| M6 | `start_step = ckpt["step"]` → `start_step = 0` | **first pass: the ε assertion stayed GREEN** → after the fix: 2 failed | both σ rows — `assert (2, 4) == (2, 2)` on the composed-step count |
| M7 | `LoRALinear` restructured into `nn.Linear` submodules (the exact thing DPSGD-07 forbids) | **first pass: the key-set round trip stayed GREEN** → after the fix: 8 failed local / 5 failed CI-shape | `test_lora_linear_holds_bare_parameters`, `test_lora_state_dict_keys_survive_a_round_trip`, both on-disk artifact cases, and collaterally the DPSGD-census tests |
| M8 | `lora_A` renamed out of the `"lora_"` filter | 10 failed | the above plus `test_lora_artifact.py::test_no_base_weight_leak` and `::test_two_artifact_load_reproduces_logits` |

**Two rows changed what shipped, and both are recorded because the first draft would have been a guard nobody had watched.**

**M6 was GREEN against the first ε assertion, and structurally so.** Reading T from the resumed run's end-of-call `step` field gives `4` in *both* arms even when the resume restarts the counter — because the resumed call still stops at `max_steps_override`. The run then composes **6** steps (2 before the kill + 4 after) while reporting a 4-fold composition: an ε that is identical across the arms **and optimistic**. The fix reads T from the count of `finalize` invocations, and the checkpoint field is asserted equal to that count so the two readings are pinned together.

**M7 was GREEN against the first key-set assertion, and structurally so.** The round trip compares a donor and a fresh model both built by the same (mutated) code, so a restructuring moves both sides together and set-equality survives while every key silently becomes `…lora_A.weight`. Set-equality proves the export/load path preserves keys; it does **not** prove they are the historical v3.0 keys. The shipped **form** is now pinned as a literal (`k.endswith(("lora_A", "lora_B"))`), measured against `checkpoints/persona_adapter.pt`'s own 72 keys, and M7 now reddens in **both** the local and the CI shape.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] The ε assertion as specified is blind to a step-counter reset**

- **Found during:** Task 2's mutation probe (M6)
- **Issue:** The plan's V-15 shape compares the reported ε of an uninterrupted run against a resumed one. Read off the checkpoint's `step` field, both are `4` even when `train()`'s `start_step = ckpt["step"]` is mutated to `0` — the resumed process then composes 6 steps and publishes the ε of a 4-fold composition. The published number is **optimistic**, which is the exact failure class DPSGD-05 exists to prevent, and the assertion as written could not see it.
- **Fix:** `_count_composed_steps(dp)` shadows `finalize` per-instance and counts real invocations. T is the count; `blob_c["step"] == steps_b` pins the field to the count; the arm split is asserted as `(_KILL_AT, _TOTAL_STEPS - _KILL_AT)`. The helper's docstring records that it exists *because a mutation measured the field-read version incapable*.
- **Files modified:** `tests/test_phase22_checkpoint.py`
- **Verification:** M6 re-run → 2 failed, `assert (2, 4) == (2, 2)`.
- **Committed in:** `a0c2407`

**2. [Rule 2 - Missing critical functionality] The key-set round trip cannot detect the restructuring DPSGD-07 forbids**

- **Found during:** Task 3's mutation probe (M7)
- **Issue:** The plan assigns `test_lora_state_dict_keys_survive_a_round_trip` the role of V-17's binding half. Applied verbatim, the exact restructuring DPSGD-07 names (bare `nn.Parameter` → `nn.Linear` submodules) leaves it **GREEN**: donor and comparison model are both built by the mutated code, so both key sets become `…lora_A.weight` and remain equal. Only `test_lora_linear_holds_bare_parameters` and the *gitignored* on-disk cases caught it — meaning on a fresh clone the "binding" leg was not binding.
- **Fix:** the shipped v3.0 key **form** pinned as a literal (`all(k.endswith(("lora_A", "lora_B")))`), with the measurement in the comment and `checkpoints/persona_adapter.pt`'s 72 keys as its basis.
- **Files modified:** `tests/test_phase22_checkpoint.py`
- **Verification:** M7 re-run in the CI shape (`checkpoints/` absent) → 5 failed, `test_lora_state_dict_keys_survive_a_round_trip` among them.
- **Committed in:** `02c90b1`

**3. [Rule 3 - Blocking] `make test` / `make lint` still do not resolve the venv**

- **Found during:** verification
- **Issue:** the `Makefile` invokes bare `pytest` / `ruff`, which resolve to a pyenv 3.12.13 with no torch. Sixth confirmation (22-01…22-06). The plan's Task-3 acceptance criterion literally says `make lint` exits 0; it cannot on this box.
- **Fix:** all verification ran through `.venv/bin/`. `.venv/bin/ruff check . && .venv/bin/ruff format --check .` is clean over **201 files**. The `Makefile` is untouched — out of scope.
- **Committed in:** n/a

**4. [Rule 1 - Bug] `gsd-sdk` mutation-handler defects, hand-repaired before commit** — see *Tooling Corruption Encountered*.

### Deliberate departures from the plan text

- **The plan's property (3) is internally contradictory, and the STRONGER reading shipped.** Task 2 asks both that the resume *"run the remaining steps"* and that *"after `train(resume_from=…)` the resumed `DPSGD._g.get_state()` is `torch.equal` to the state saved at the kill point"*. Those cannot both hold — any post-resume step advances the generator past the saved state. Solved for intent: the claim is *the production restore fired and the stream continued*, so the shipped assertion is that the **uninterrupted arm's and the resumed arm's next noise draws are `torch.equal`** end-to-end. The literal zero-further-steps form is already committed as 22-06's `test_dp_noise_rng_round_trips_through_a_kill_and_resume` and is cited in the comment rather than duplicated.
- **The fixture is a TINY GPT, not the 13.9M production one.** `DPSGD.__init__`'s closed-form census is `r * n_layer * 18 * n_embd`, which holds at any shape, so `ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16)` + `LoRAConfig(r=4)` (1,152 trainable params, 6 wrapped projections) exercises exactly the same refusals at a fraction of the cost. The whole file runs in **2.5 s**.
- **The on-disk legs RAN rather than skipped on this box**, because `checkpoints/` here holds 14 GB of real artifacts (73 files, 0 tracked). Both shapes were executed and both are reported: 12 passed / 0 skipped locally, 8 passed / 4 skipped with `checkpoints/` absent.
- **`test_v3_on_disk_artifacts_still_load`'s second case resolves the `*latest.pt` glob to the SMALLEST match** (`phase14_real_latest.pt`, 59.7 MB of 29 matches) rather than the first, so the gated leg costs 0.28 s instead of loading a 278 MB file. The rank is read from the artifact's own `lora_A` shape and the base shape from its embedded `model_config` — nothing about one developer's box is assumed.
- **`_load_v3_adapter` derives the base shape from the ARTIFACT** (`n_embd` from `…c_proj.lora_A`'s second dim, `n_layer` from the max block index) rather than from `ModelConfig()`'s defaults. They happen to coincide for `persona_adapter.pt` (`n_layer=6`, `n_embd=384`); relying on that coincidence would be a guess.
- **Line anchors inside new code are cited by SYMBOL**, continuing 22-02…22-06's habit. The two the plan supplied and this plan repeats — `lora/inject.py:113-118` and `lora/layer.py:41` — were **VERIFIED against HEAD before use**: `:113-118` is the W1 exact-equality comment inside `load_adapter_weights`, and `:41` is the inline matmul `y = y + self.scale * (self.dropout(x) @ self.lora_A.T @ self.lora_B.T)`. **Both are correct** — unlike 22-06's `loop.py:165`. `REQUIREMENTS.md`'s DPSGD-07 anchor therefore needed no correction.
- **`grep -c "skipif"` returning 5 is prose, not sites.** The measured count of `@pytest.mark.skipif` **decorators** is **3** (`:190` on-disk back-compat, `:228` MPS, `:671` inside `_v3_case`, which mints 3 parametrized cases) — 6 gated items in total. The remaining two `skipif` hits are the word appearing inside docstrings.
- **The plan's `test_dp_noise_rng_rides_extra_without_a_schema_bump` asserts `blob["schema_version"] == CKPT_SCHEMA_VERSION == 1`** — the chained form, so a future bump reddens here rather than silently tracking the constant.

---

**Total deviations:** 4 auto-fixed (2 named guards measured incapable and strengthened, 1 blocking environment issue, 1 tooling corruption), 7 deliberate departures.
**Impact on plan:** every correction makes a guard bite MORE or a claim narrower and truer; none weakens a guard or widens a claim. No scope creep — `src/personacore/lora/`, `pyproject.toml` and all three frozen `scripts/mitigation_*.py` are byte-unchanged.

## Tooling Corruption Encountered

Seventeenth consecutive session. Every `gsd-sdk` mutation call was followed by `git diff` on the three planning files and hand-repaired before the metadata commit.

| Handler | Defect observed | Repair |
|---|---|---|
| `state.advance-plan` | rewrote `Status: Executing Phase 22` back to `Status: Ready to execute` — identical to 22-01…22-06 | restored by hand |
| `roadmap.update-plan-progress 22` | wrote the status cell as `In Progress\|  \|` — no space before the pipe, empty date cell where every sibling carries `-` | corrected to `\| 7/11 \| In Progress \| - \|` |
| `state.add-decision --summary` | prefixed every entry `- [Phase ?]:` | prefix corrected to `[Phase 22]` |
| `state.update-progress` | `{"updated": false, "reason": "Progress field not found in STATE.md"}` against a frontmatter that plainly has one | harmless; `advance-plan` had already set the block |
| `requirements.mark-complete DPSGD-05 DPSGD-07` | flipped both checkboxes but left both traceability rows' notes cells **empty** | both cells written by hand with their measured evidence |
| `state.record-metric --flag` / `state.record-session --stopped-at` | **correct** under the `--flag` form | — |

Fifth consecutive confirmation that the corruption lives in the **positional** argument path. The 22-06 workaround held: `22-07-SUMMARY.md` was written to disk **before** `roadmap.update-plan-progress` ran, so the handler reported `summary_count: 7`, wrote the count as `7/11` and flipped this plan's checkbox correctly. Only the status cell needed repair. `state.advance-plan`'s `completed_plans: 34 → 35` was verified by counting `.planning/phases/*/*-SUMMARY.md` before it was accepted: **35**, correct.

## Issues Encountered

- **One `ruff` `E501`** on a docstring summary line (101 > 100). Reworded; no assertion text changed.
- **The `.gitignore` modification present at session start is pre-existing and untouched** — not staged in any commit here.
- **`torch.mps.get_rng_state()` costs nothing measurable** (first call 0.0000 s, second 0.000001 s) and adds 44 bytes per checkpoint on an MPS box, so the save-side addition has no cost worth recording as a trade-off.

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest tests/test_phase22_checkpoint.py -q` | **12 passed, 0 skipped** in 2.50 s |
| the same file with `checkpoints/` ABSENT (the CI shape) | **8 passed, 4 skipped, 0 failed** |
| Task-1 verify set (`test_phase22_checkpoint` + `test_checkpoint` + `test_resume_curve` + `test_fisher_checkpoint`) | **22 passed** |
| Task-3 verify set (+ `test_lora_artifact` / `_inject` / `_layer` / `_merge`) | **56 passed** |
| `grep -n 'rng.get("mps")' src/personacore/checkpoint.py` | `:199` — the restore line |
| `grep -n 'rng\["mps"\]' src/personacore/checkpoint.py` | `:200` only — inside the `.get()`-guarded body (`:28` is docstring prose) |
| `grep -n "CKPT_SCHEMA_VERSION = 1"` | `:61` — **no bump** |
| `grep -n "load_noise_rng_state" tests/test_phase22_checkpoint.py` | **1 hit, docstring prose only** — no direct call anywhere |
| `grep -n "approx\|rel_tol" tests/test_phase22_checkpoint.py` | **1 hit, the tolerance-register prose** — no `pytest.approx`, no `rel_tol` in any assertion |
| `@pytest.mark.skipif` decorators / gated items | **3 / 6** — every path under `checkpoints/` and the MPS row |
| hard-coded generator byte count in tests | **none**; `44` appears only in docstring prose, with its device |
| `git diff --exit-code -- src/personacore/lora/ pyproject.toml` | exit **0** — byte-unchanged |
| Mutation probe | **6 mutations (M1–M8, 8 applied), 6 distinct RED signatures**, 3 sha256-identical restores |
| Full suite `.venv/bin/python -m pytest -q` | **1243 passed, 1 skipped** in 208.02 s (baseline 1231/1, +12 new) |
| `.venv/bin/ruff check . && .venv/bin/ruff format --check .` | clean, **201 files** |

## Known Stubs

None. Every line added to `checkpoint.py` is exercised by a committed test in both directions, and no placeholder was left for a later plan. What this plan does **not** deliver, stated so no reader infers it: `rng["mps"]` is **not exercised by the DP path** anywhere and never will be under D-07's dedicated generator — it is DPSGD-05's literal requirement carried correctly and described honestly, not a load-bearing guard.

## Threat Flags

None. No network endpoint, no auth path, no new file-access pattern (the only I/O is the existing `save_checkpoint` / `load_checkpoint` pair, unchanged in shape), no schema change — `CKPT_SCHEMA_VERSION` stays `1`. Nothing was installed.

Threat register dispositions, each mitigated as planned:

- **T-22-32** (`rng["mps"]` subscript KeyError-ing every pre-Phase-22 checkpoint) — restored via `rng.get("mps")`; the pre-Phase-22 shape is built in-test and its key set asserted equal to the real one; M1 watched RED on both the in-test and the on-disk leg.
- **T-22-33** (a resume test green while the noise RNG was never restored) — the resume runs through `train(resume_from=…)`; the negative control deletes `dp_noise_rng` and the next draw diverges (`-1.255206` vs `1.06912`). M4 watched RED.
- **T-22-34** (`==` and `rel_tol` conflated) — both registers written down in the same docstring and in the module header; V-15 uses `==` with `inject.py:113-118` cited; `grep` confirms no `approx`/`rel_tol` in any assertion.
- **T-22-35** (`rng["mps"]` presented as load-bearing) — the two-slot register in `checkpoint.py`'s docstring and the full-paragraph skip `reason=`; and this SUMMARY says it in *Known Stubs* too.
- **T-22-36** (a `LoRALinear` restructuring silently invalidating every v3.0 artifact) — the structural assertion plus the key-**form** literal added after M7 measured the key-set round trip incapable. Both watched RED.
- **T-22-36b** (V-17 resting on gitignored files) — executed with `checkpoints/` absent: 8 passed, 4 skipped, **0 failed**; M7 still reddens 5 tests in that shape.
- **T-22-37** (a gratuitous schema bump) — `CKPT_SCHEMA_VERSION` asserted `== 1` in the test as a chained equality; `dp_noise_rng` proven not to trip `_RESERVED_CKPT_KEYS`, with the clash refusal watched firing for `rng=`.
- **T-22-SC** (package installs) — accepted; nothing installed, `pyproject.toml` byte-unchanged.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plan 22-08 (the production wiring) inherits a proven resume path and must not re-derive it.** What it owes is still `scripts/teach_persona.py:1167`: no `dp_fn`, no `grad_accum_steps`, no `replay_*`, no fact bin. Two facts it must not re-measure: `TrainConfig.grad_accum_steps` defaults to `1`, where 22-06's D-02 inherited-divide fake is structurally invisible; and `DPSGD.__init__` refuses an enabled scaler and an unfrozen base, so the caller must pass `runtime=` and call `mark_only_lora_trainable`.
- **Any plan that publishes an ε must take T from the composed-step count, not from a checkpoint field.** Measured here: a resume that restarts the step counter leaves the field correct and the composition wrong, and the published ε is optimistic. `tests/test_phase22_checkpoint.py::_count_composed_steps` is the shape to reuse.
- **Plan 22-09 should not credit a key-set round trip with detecting a `LoRALinear` restructuring.** Measured (M7): it is symmetric under a co-moving rename and stays green. The detectors that bite are `test_lora_linear_holds_bare_parameters` and the key-**form** literal.
- **The MPS row is exercised on an M3 box and skipped in CI, and both are true.** Anyone reporting V-16 should say which shape they ran; `22-VALIDATION.md`'s "unverifiable claims" row for this slot can now record *"exercised locally on Darwin/arm64 torch 2.7.1; skipped in CPU-only CI; never fired by the DP path"*.
- **`checkpoints/` on a developer box is not what CI sees.** Every new test touching it must use `pytest.param(marks=skipif(...))` per case plus a declared-count meta-guard, and should be executed once with the directory absent before it is believed.

## Self-Check: PASSED

- `src/personacore/checkpoint.py` — FOUND
- `tests/test_phase22_checkpoint.py` — FOUND
- `.planning/phases/22-dp-sgd-core-accountant-and-the-correctness-battery/22-07-SUMMARY.md` — FOUND
- commit `f8969d0` — FOUND
- commit `a0c2407` — FOUND
- commit `02c90b1` — FOUND

---
*Phase: 22-dp-sgd-core-accountant-and-the-correctness-battery*
*Completed: 2026-08-25*
