---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
plan: 06
subsystem: training
tags: [differential-privacy, dp-sgd, training-loop, additive-seam, bit-identity, checkpoint-rng]

# Dependency graph
requires:
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-04's src/personacore/privacy/dpsgd.py::DPSGD — begin_step / absorb_record / finalize, the summed accumulator, the dedicated generator, and the five refusal markers this seam drives"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-01/22-04's tests/test_phase22_dpsgd_ast.py closure walk — the same engine the widened re-seed exemption's unreachability proof runs through"
  - phase: 10-the-training-loop-and-the-golden-trajectory
    provides: "tests/fixtures/golden_trajectory_v1.json and tests/test_loop_penalty_fn.py::_run_recipe — the DPSGD-02 fixture and the ONE recipe that drives it"
  - phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
    provides: "loop.py::replay_fn — reused BYTE-UNCHANGED under D-01, and the public term the V-12 differential is run one kwarg apart on"
provides:
  - "src/personacore/training/loop.py::_optimizer_step's dp_fn= parameter — the NEW ADDITIVE GRADIENT-SIDE seam owning everything between accumulation and optimizer.step()"
  - "the structurally-unreachable legacy clip: ONE reachable clip_grad_norm_ call site in loop.py, inside `if dp_fn is None:`"
  - "D-02's bypassed /accum divide on the DP path, with the wrong-sensitivity trap named in the comment"
  - "D-14's dp_noise_rng slot, BOTH halves — a _dp_extra() closure at all three save sites including the end-of-call one, and a .get()-guarded restore in the resume_from block"
  - "DPSGD.noise_rng_state / DPSGD.load_noise_rng_state, the latter refusing a restore into an already-stepped seam"
  - "tests/test_phase22_dpsgd.py — V-14, V-12, D-03's runtime half, D-06's sigma-of-zero identity, the dp_noise_rng round trip, and FAKE 3's magnitude guard; 18 -> 29 tests"
  - "tests/test_phase22_dpsgd_ast.py — the re-seed exemption widened EXPLICITLY and paired with an unreachability proof; 16 -> 17 tests"
affects: [22-07 the MPS RNG slot and the kill-resume epsilon, 22-08 wiring teach_persona.py's DP arms, 22-09 the four fake probes, 23 the frontier sweep]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "An AST exemption granted by NAME must ship PAIRED with an unreachability proof over the same closure walk, or it is a name-based pass a future author can park a fake behind"
    - "A 'did this clip bind' check done by OBSERVATION (compare the gradient buffers before and after the real call) rather than by modelling torch's internal clip_coef arithmetic — the +1e-6 in the denominator makes `norm <= max_norm` insufficient in a razor-thin band"
    - "A bit-identity claim carries its three fingerprints (CSV text, final-loss repr, parameter sha256) explicitly; 'the loss curve matches' is not bit-identity and must not be reported as one"
    - "When the measured gap is exactly 0.0, ship the bitwise assertion and move the documented tolerance to an input where the gap is real — a tolerance nobody needs is a tolerance a future error can hide in"

key-files:
  created: []
  modified:
    - src/personacore/training/loop.py
    - src/personacore/privacy/dpsgd.py
    - tests/test_phase22_dpsgd.py
    - tests/test_phase22_dpsgd_ast.py
    - .planning/REQUIREMENTS.md

key-decisions:
  - "The plan's `accum = 4` documented-tolerance case is UNSATISFIABLE as a tolerance: measured, the identity is BITWISE at every power-of-two lot size (72/72 at 1, 2, 4, 8) because scaling by a power of two is exact in IEEE-754. The tolerance moved to accum = 3, the smallest non-power-of-two, where the gap is real (5.681269e-06) and a non-degeneracy assertion proves it is doing work"
  - "D-17's fake table credits D-06's sigma-of-zero identity with detecting FAKE 3 (noise added after averaging). WATCHED: the mutation leaves the entire suite GREEN, structurally — at sigma = 0 the draw is exactly zero, so the divide's position is unobservable. A new magnitude guard at sigma > 0 was added and watched RED"
  - "The AST re-seed exemption was widened to load_noise_rng_state EXPLICITLY, with the reason in the source, and paired with test_reseed_exempt_methods_are_unreachable_from_the_step_path — a name-only exemption would let a re-seed spelled load_noise_rng_state be called from finalize"
  - "load_noise_rng_state REFUSES a restore into a seam that has already released noise ([dp-refusal:rng-restore]) — Rule 2, not in the plan"
  - "The plan's `grep -rn \"def _run_recipe\" tests/` == 1 criterion is FALSE at HEAD (four definitions, three pre-existing). The property that holds and was asserted instead: exactly ONE recipe drives the GOLDEN fixture, and this plan added none"
  - "requirements.mark-complete WAS called, first time in six plans — for DPSGD-02 only. Its text ('the default path is proven bit-identical when the seam is off, against the Phase-10 golden-trajectory fixture') is fully and provably satisfied here and nothing 22-08 or 22-11 adds changes it. DPSGD-01 waits on 22-08's production wiring, DPSGD-04 on 22-09's four fakes, DPSGD-05 on 22-07's MPS slot"

patterns-established:
  - "Exemption + unreachability: an allowlist entry paired with a closure-walk assertion that the exempt symbol cannot be reached from the protected path"
  - "Power-of-two lot sizes are the bitwise regime for a loss-side-vs-gradient-side divide; assert bitwise there and put the tolerance on a non-power-of-two"

requirements-completed: [DPSGD-02]
requirements-contributed: [DPSGD-01, DPSGD-04, DPSGD-05]

# Metrics
duration: 70min
completed: 2026-08-25
---

# Phase 22 Plan 06: The `dp_fn=` Gradient-Side Seam Summary

**DP enters `train()` through a new additive gradient-side seam whose OFF path is bit-identical to the Phase-10 golden fixture on all three fingerprints — and the legacy averaged-gradient clip now has exactly ONE reachable call site in `loop.py`, inside `if dp_fn is None:`, with six seam mutations producing six distinct REDs and a byte-identical restore.**

## Performance

- **Duration:** ~70 min
- **Started:** 2026-08-25T23:15Z (first read after `1c66280`)
- **Completed:** 2026-08-26T00:25Z
- **Tasks:** 3
- **Files modified:** 5 (0 created)

## Accomplishments

- **`dp_fn=` is genuinely additive.** Appended to `_optimizer_step`'s `def` (`:143-154`) **and** to its POSITIONAL call site (`:619-630`) in the same diff, and to `train()`'s keyword-only signature. Every existing caller is unchanged in behaviour: the full suite went 1219 → 1231 passed with 0 regressions.
- **V-14 is proven with EXACT comparison evidence, not a loss curve.** On this box (Darwin/arm64/torch 2.7.1 = the capture platform) the golden replay **RUNS rather than skips**, and `dp_fn=None` reproduces `tests/fixtures/golden_trajectory_v1.json` on all three fingerprints — see the table below for the actual values.
- **The legacy clip is structurally unreachable and it was WATCHED.** `grep -n "clip_grad_norm_" loop.py` returns 4 lines but exactly **ONE call site** (`:215`); the line immediately above it is `if dp_fn is None:`. The runtime half observes 2 calls over 2 optimizer steps with the seam off and **0** with it on.
- **Six seam mutations, six distinct REDs, byte-identical restore** (`loop.py` sha256 `ee063ee0…` before and after; `dpsgd.py` `140f5108…`). Two of them produced findings that changed the shipped tests — see *Guards Watched Failing*.
- **D-14's slot is wired BOTH ways.** `**_dp_extra(),` appears at exactly **3** splat sites against exactly **3** `save_checkpoint(` call sites, `def _dp_extra` appears **1** time, and the `resume_from` block restores through `ckpt.get("dp_noise_rng")`. `CKPT_SCHEMA_VERSION` is still `= 1`.
- **`replay_fn` is byte-unchanged.** `git diff loop.py | grep -c "^-[^-]"` returns **6**: the `/accum` line (replaced by the conditional), the clip line (moved inside the branch), and 4 rewritten docstring lines. Zero lines inside `replay_fn`'s body changed.
- `pyproject.toml`, `scripts/mitigation_gate.py`, `scripts/mitigation_unit.py`, `scripts/mitigation_accountant.py` and `src/personacore/checkpoint.py` are all byte-unchanged (`git diff --exit-code` exits 0). RPT-03 and DPSGD-07 hold; nothing was installed.

## Task Commits

1. **Task 1: the `dp_fn=` seam in `_optimizer_step` and `train()`, and both halves of the noise-RNG slot** — `8ecb789` (feat)
2. **Task 2: V-14 — seam off is bit-identical to the Phase-10 golden trajectory** — `3e1c71e` (test)
3. **Task 3: V-12, D-03's runtime half, D-06's σ=0 identity, and FAKE 3's magnitude guard** — `e2d4b0a` (test)

## Files Created/Modified

- `src/personacore/training/loop.py` (+125 / −25) — module docstring gains the DPSGD-01 paragraph; `_optimizer_step` gains `dp_fn=None` plus four surgical branch points; `train()` gains `dp_fn=None`, the `_dp_extra()` closure, three splats and the resume restore; the `replay_bin` docstring's Phase-22 forward reference is discharged and the measured 67.1% mixing figure recorded; a full `dp_fn:` Args register with the DOES / DOES NOT / rejected-alternatives shape.
- `src/personacore/privacy/dpsgd.py` (+68 / −11) — `noise_rng_state` / `load_noise_rng_state` with the measured **5,056-byte CPU / 44-byte MPS** state size carried with its denominator; a sixth refusal marker `[dp-refusal:rng-restore]`; the module docstring's own stale claim about `loop.py` corrected. Still **25 `raise`, 0 `assert`, 0 `_prove`**.
- `tests/test_phase22_dpsgd.py` (+646 / −5, 18 → **29 tests**) — the V-14 / D-06 docstring register, three V-14 tests, `test_side_channel_negative_control`, `test_legacy_clip_is_unreachable_on_the_dp_path`, `test_sigma_zero_non_binding_clip_reproduces_the_default_path` ×3, `test_dp_noise_rng_round_trips_through_a_kill_and_resume`, and `test_noise_is_scaled_by_the_lot_size_because_the_divide_comes_LAST` ×2.
- `tests/test_phase22_dpsgd_ast.py` (+121 / −29, 16 → **17 tests**) — `_ALLOWED_RESEED_SITES` hard-equality allowlist replacing the `outside == {}` name exemption, plus `test_reseed_exempt_methods_are_unreachable_from_the_step_path` with its own closure meta-guard.
- `.planning/REQUIREMENTS.md` — DPSGD-04's stale `loop.py:165` anchor corrected in place with a dated note (see Deviation 4).

## The Evidence

### V-14 — bit-identity, with the actual comparison

Platform gate: `(Darwin, arm64, 2.7.1)` matches `meta.platform`, so `test_seam_off_bit_identical` **RAN** (0 skips in this file). Fixture: `tests/fixtures/golden_trajectory_v1.json`, `meta.captured_at_sha = 6a46441cc17b6fc3c951a12ee0b6620b88b82d91`.

| Fingerprint | Replay with `dp_fn=None` | Golden | Comparison |
|---|---|---|---|
| CSV text (6 rows: header + 5 steps) | sha256 `2f4b95ac4c05add4…` | sha256 `2f4b95ac4c05add4…` | `==` **True** |
| final loss `repr` | `9.435891151428223` | `9.435891151428223` | `==` **True** |
| parameter bytes sha256 | `647f5981027bfce1ad1d38867c3f9aa293e95c9bb27101a3c096517d7ace23ac` | identical | `==` **True** |
| omitted vs `dp_fn=None` (all 3, in-process) | — | — | `==` **True** |

This compares **8,192 × 8,192 = 67,108,864 parameter values** through their sha256 plus **5 logged steps × 6 CSV columns**. It is not a loss-curve comparison.

### The σ=0 / non-binding-C identity — the full measured table

Two runs of the same GPT+LoRA recipe (2 optimizer steps, `batch_size=2`, `grad_clip=1e6`), one `dp_fn=None` and one `dp_fn=DPSGD(sigma=0.0, clip_norm=1e6)`; deviation is `‖θ_default − θ_dp‖ / ‖θ_default‖` over all 72 concatenated LoRA tensors (331,776 params).

| `grad_accum_steps` | bitwise tensors | global relative deviation |
|---|---|---|
| 1 | **72/72** | 0.000000e+00 |
| 2 | **72/72** | 0.000000e+00 |
| 4 | **72/72** | 0.000000e+00 |
| 8 | **72/72** | 0.000000e+00 |
| 3 | 0/72 | **5.681269e-06** |
| 5 | 0/72 | 8.573839e-05 |
| 6 | 0/72 | 1.737541e-04 |
| 7 | 0/72 | 5.290843e-06 |

Both clips asserted NOT to bind, before comparing: the legacy clip observed through a spy comparing the gradient buffers before/after the real call (`unchanged is True` on both steps, pre-clip norms `2.0937681198120117` / `2.0755295753479004` against `max_norm = 1e6`), and `dp._clip_bind_count == 0`. **At `TrainConfig`'s default `grad_clip = 1.0` the legacy clip DOES bind on this fixture** (2.0938 > 1.0), which is why non-binding is arranged and observed rather than assumed.

### V-12 — the one-kwarg-apart differential

Same `_optimizer_step` call site, `replay_fn=None` vs `replay_fn=<a real un-clipped public pass>`, `grad_accum_steps=2`, σ=1.0, C=1.0, DP seed 4242.

| Quantity | Measured |
|---|---|
| mixed `.grad` buffers that DIFFER between branches | **36 / 72** (exactly the `lora_B` half) |
| private noised term, `torch.equal` across branches | **72 / 72** |
| `torch.allclose(mixed_a, mixed_b)` | **False** |
| ‖mixed, no replay‖ / ‖mixed, with replay‖ | 288.026520 / 288.030396 |
| generator state after the step, both branches | `torch.equal` **True** |
| `_records` / `_clip_bind_count`, both branches | 2 / 2 and equal |

The 36 that do NOT differ are the `lora_A` gradients: `dL/dA` carries a factor of `B` and LoRA initialises `B` to zeros, so the replay pass contributes exactly `0.0` there. That is a structural fact about LoRA init, and the test asserts `_FROZEN_TENSORS // 2` for that stated reason rather than "at least one".

### The `dp_noise_rng` round trip

| Check | Measured |
|---|---|
| generator state size, CPU | **5,056 bytes** (`torch.uint8`) |
| generator state size, MPS (per D-14's probe) | 44 bytes — the figure a CPU test must NOT assert |
| `set_state` round trip | draws after restore `torch.equal` to draws before |
| `dp_noise_rng` present in the END-OF-CALL save | **True** |
| saved value == live `noise_rng_state()` | **True** |
| `schema_version` in the checkpoint | **1** (unchanged) |
| fresh seam (seed 999) vs saved state, pre-resume | differs — the positive control |
| post-resume seam state == saved state | **True** |
| pre-Phase-22 checkpoint (key deleted) + live seam | resumes; generator untouched |

### FAKE 3's magnitude guard

Every record's gradient set to exactly zero, so the accumulator is the zero vector and the released term is pure noise / N. σ=1.0, C=1.0, over all 331,776 released elements:

| N | released `std` | expected `σ·C/N` | ratio |
|---|---|---|---|
| 1 | 1.00069046 | 1.00000000 | 1.000690 |
| 4 | 0.25017262 | 0.25000000 | 1.000690 |

The 0.069% deviation is one draw's sampling error, inside the 0.123% standard error of a sample standard deviation at n = 331,776. Band asserted: 1% — ~8× the standard error and ~400× below the factor-of-N error the test exists to catch.

## Guards Watched Failing

Six mutations, each one line or one block away from the committed source, applied to the work-tree file and restored in a `finally`. Restore verified by sha256: `loop.py` `ee063ee00025b2fdbe38b1962072a75dc4047d10408eedcc795a5580d82d98aa` before and after; `dpsgd.py` `140f51082ab188a06de5426e8e1827c85423f19c43e45d45bca90515a96013eb` before and after. Probe target: `tests/test_phase22_dpsgd.py tests/test_loop_penalty_fn.py tests/test_train_loop.py`.

| # | Mutation | Result | Guard(s) reddened |
|---|---|---|---|
| 0 | control (unmutated) | **35 passed, 1 skipped** | — |
| 1 | **FAKE 2** — the DP path INHERITS `loop.py`'s `/accum` divide (D-02's trap) | 2 failed | `test_sigma_zero_…[4]`, `test_sigma_zero_…[3]` |
| 2 | **FAKE 1** — the legacy clip made reachable on the DP path | 1 failed | `test_legacy_clip_is_unreachable_on_the_dp_path` |
| 3 | `dp_fn` appended to the `def` but NOT to the positional call site | 4 failed | `test_legacy_clip_…`, `test_sigma_zero_…[1]`, `[3]`, `[4]` |
| 4 | the **END-OF-CALL** `**_dp_extra(),` splat dropped (in-loop only) | 1 failed | `test_dp_noise_rng_round_trips_through_a_kill_and_resume` |
| 5 | the `resume_from` restore dropped (a WRITE-ONLY slot) | 1 failed | `test_dp_noise_rng_round_trips_through_a_kill_and_resume` |
| 6 | **FAKE 3** — the `/N` divide moved BEFORE the noise | **35 passed — GREEN** → after the new guard: **1 failed** | `test_noise_is_scaled_by_the_lot_size_because_the_divide_comes_LAST[4]` |

**Two rows changed what shipped.**

**Row 1 is GREEN at `accum = 1`.** The inherited-divide fake is invisible at a lot size of one, because `total / 1` is `total` exactly. The identity at `accum = 1` alone therefore CANNOT catch D-02's trap; only `N > 1` can. That is why the parametrization over `(1, 4, 3)` is load-bearing rather than decorative, and it is worth stating because `TrainConfig.grad_accum_steps` defaults to `1` and `teach_persona.py` currently inherits that default (22-CONTEXT's measured gap #2).

**Row 6 was GREEN before the guard this plan added, and structurally so.** D-17's fake table credits D-06's CPU identity with detecting *noise added after averaging* — *"build divide → noise; watch the identity break"*. Watched: it does **not** break. At σ=0 the drawn values are exactly zero, so `(sum + 0)/N` and `(sum/N) + 0` are the same number for every N; an identity taken at the one σ where the noise vanishes can never see where the noise was added. `test_side_channel_negative_control` runs at σ>0 but compares two branches that both carry the mutation, so it cannot see it either. The order is now pinned where it IS observable — at σ>0, over the noise magnitude — and the mutation reddens.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The plan's `accum = 4` "documented relative tolerance" case has a measured gap of exactly ZERO**

- **Found during:** Task 3
- **Issue:** The plan's acceptance criterion requires *"the `4` case asserts a documented relative tolerance whose MEASURED value appears in the docstring"*, on the stated basis that *"the default path divides the LOSS by `accum` before backward while the DP path divides the summed GRADIENT after, and `(g1+g2)/2` is not bit-identical to `g1/2 + g2/2` in IEEE-754."* The premise is false at powers of two. Measured across `accum ∈ {1,2,3,4,5,6,7,8}`, every power of two is **72/72 bitwise identical with relative deviation exactly `0.000000e+00`** and every non-power-of-two is 0/72. Scaling by a power of two is exact in IEEE-754, so the loss-side and gradient-side divides commute bit-for-bit there.
- **Fix:** The parametrization is `(1, 4, 3)`. `1` and `4` assert BITWISE (`torch.equal` on all 72 tensors and `rel == 0.0`); `3`, the smallest non-power-of-two, carries the documented tolerance with its measured `5.681269e-06` and a **non-degeneracy assertion** (`bitwise == []`) proving the tolerance branch is not green over a sample `==` would have passed. The branch predicate is `n & (n-1) == 0`, so the two regimes are named structurally rather than by a hard-coded list. Same reasoning 22-04 recorded for its own N=2 case: a tolerance nobody needs is a tolerance a future error can hide in.
- **Files modified:** `tests/test_phase22_dpsgd.py`
- **Verification:** the full 8-row table above; mutation 1 reddens `[4]` and `[3]` and is green at `[1]`.
- **Committed in:** `e2d4b0a`

**2. [Rule 2 - Missing critical functionality] FAKE 3's named detector is measurably incapable of detecting it**

- **Found during:** Task 3's mutation probe
- **Issue:** D-17's table assigns FAKE 3 (*noise added after averaging*) to *"D-06's CPU identity"* with the positive control *"build divide → noise; watch the identity break"*. Applied verbatim — `finalize` rewritten to divide the accumulator before `_noised_private` and then divide by 1 — the entire target suite stays **GREEN (35 passed)**, including every σ=0 identity in this plan and 22-04's `test_sum_then_noise_then_divide`. The reason is structural: at σ=0 `torch.normal(std=0.0)` returns exact zeros, so the divide's position is unobservable in the released value. Shipping the identity while a downstream plan believes it covers FAKE 3 is the "guard nobody has watched fail" problem this phase exists to prevent.
- **Fix:** `test_noise_is_scaled_by_the_lot_size_because_the_divide_comes_LAST`, parametrized over N ∈ {1,4}. Every record's gradient is set to exactly zero (positive control: `_global_norm(_accum) == 0.0`), so the released term is pure noise/N and its standard deviation must be `σ·C/N`. Under the wrong order it is `σ·C` — a factor of N. The test docstring records that it exists *because a mutation probe measured the guard it replaces to be incapable*, so 22-09 does not inherit the false table entry.
- **Files modified:** `tests/test_phase22_dpsgd.py`
- **Verification:** mutation 6 re-run against the new guard → **1 failed**, `[4]` RED (`[1]` correctly stays green: dividing by 1 is a no-op).
- **Committed in:** `e2d4b0a`

**3. [Rule 2 - Missing critical functionality] The AST re-seed exemption the plan sanctions would be a NAME-BASED pass, and the restore had no runtime refusal**

- **Found during:** Task 1
- **Issue:** `load_noise_rng_state`'s body is `self._g.set_state(state)` — literally FAKE 4's shape — and `set_state` is in `_RESEED_CALLS`, so `test_dpsgd_never_reseeds_its_generator` goes RED on correct code. The plan anticipates this and says *"the guard's exemption list is the thing to widen explicitly, with the reason recorded."* But widening `outside == {}` to skip a method NAME lets a future author park a re-seed in a method spelled `load_noise_rng_state` and call it from `finalize` — the guard getting weaker while looking bigger. Separately, nothing prevented a caller restoring a state into a seam that had already released noise, which rewinds a stream that has already been drawn from.
- **Fix:** Two paired strengthenings. (a) `_ALLOWED_RESEED_SITES` is a **hard-equality allowlist** naming which method is credited with which call (`{"__init__": ["manual_seed"], "load_noise_rng_state": ["set_state"]}`) — the `_ALLOWED_GRAD_WRITES` discipline 22-04 established — and it ships alongside `test_reseed_exempt_methods_are_unreachable_from_the_step_path`, which runs the SAME closure walk the `.grad` guards use with the exempt names as the forbidden set. `begin_step` is a LEAF, so the helper's own `len(seen) > 1` meta-guard correctly refuses it as an entry; that refusal is honoured (not worked around) with a direct leaf assertion plus an instruction to move it into `_STEP_ENTRIES` if it ever stops being one. The new test carries its own meta-guard that the closure really resolves `self.<method>()` calls. (b) `load_noise_rng_state` raises `[dp-refusal:rng-restore]` when `_prev_gen_state is not None`, converting a confusing downstream `[dp-invariant:generator]` into a named refusal at the call site — and structurally guaranteeing the "restore only into a fresh seam" shape the production path uses.
- **Files modified:** `tests/test_phase22_dpsgd_ast.py`, `src/personacore/privacy/dpsgd.py`
- **Verification:** the allow-set and both meta-guards pass on the shipped bytes; the refusal was observed raising in an inline probe before it was committed.
- **Committed in:** `8ecb789`

**4. [Rule 1 - Bug] `REQUIREMENTS.md`'s DPSGD-04 carries a line anchor that is wrong AND a claim this plan makes false**

- **Found during:** state updates
- **Issue:** DPSGD-04's text cited *"`loop.py:165` already clips exactly the LoRA grads on the **averaged** gradient"*. 22-CONTEXT already measured `:165` to be `accum = max(1, train_cfg.grad_accum_steps)` with the clip at `:181`; and as of this plan the clip is inside `if dp_fn is None:`, so the sentence's substance is also no longer true on the DP path. Leaving a measurably false anchor inside a requirement is the exact defect class this phase names (Phase 21 IN-02).
- **Fix:** The anchor removed from the requirement's body and replaced with a **dated in-place note** recording what `:165` actually was, where the clip actually was, and where it is now — cited by SYMBOL (`training/loop.py::_optimizer_step`). The requirement's own substance is unchanged; only the false anchor moved. Precedent: `20-16` corrected in place the one `REQUIREMENTS.md` sentence its verification measured false.
- **Files modified:** `.planning/REQUIREMENTS.md`
- **Verification:** `grep -n "loop.py:165" .planning/REQUIREMENTS.md` → no matches.
- **Committed in:** the plan metadata commit

**5. [Rule 1 - Bug] The plan's `grep -rn "def _run_recipe" tests/` == 1 criterion is false at HEAD**

- **Found during:** Task 2 verification
- **Issue:** The acceptance criterion asserts *"exactly ONE definition, in `tests/test_loop_penalty_fn.py`"*. Measured, there are **four**: `test_loop_penalty_fn.py:73`, `test_extra_eval_fns.py:42` and `test_masked_train_seam.py:150` (three pre-existing), plus a comment hit in this file. My first draft copied the false claim into a source comment.
- **Fix:** The comment now states the measurement precisely — four definitions, which three, and that the other two predate Phase 22 and drive DIFFERENT fixtures (the telemetry seam and the mask seam), touching `golden_trajectory_v1.json` not at all. The property that actually matters is asserted instead: **exactly one recipe drives the GOLDEN fixture, and this plan added none.** The plan's intent (no second golden recipe free to drift from the fixture's own `meta` block) is fully satisfied.
- **Files modified:** `tests/test_phase22_dpsgd.py`
- **Committed in:** `e2d4b0a`

**6. [Rule 3 - Blocking] `make test` / `make lint` still do not resolve the venv**

- **Found during:** verification
- **Issue:** `Makefile` invokes bare `pytest` / `ruff`, which resolve to a pyenv 3.12.13 with no torch. Fifth confirmation (22-01 deviation 3, 22-02, 22-03, 22-04, 22-05). The plan's Task-3 acceptance criterion literally says `make lint` exits 0; it cannot on this box.
- **Fix:** all verification ran through `.venv/bin/`. `.venv/bin/ruff check . && .venv/bin/ruff format --check .` is clean over 200 files. The Makefile is untouched — out of scope.
- **Committed in:** n/a

**7. [Rule 1 - Bug] `gsd-sdk` mutation-handler defects, hand-repaired before commit**

- **Found during:** state updates
- See *Tooling Corruption Encountered* below — sixteenth consecutive session.

### Deliberate departures from the plan text

- **Test-count acceptance criteria (13 / 14 / 17 / 18) were computed for a file that starts at 6 tests; it starts at 18.** 22-04's SUMMARY explicitly said *"Plan 22-06's bounds should be computed off 18 for this file, not 6 or 11."* The file ends at **29**, so every count criterion is trivially met. Recorded so a reader does not mistake the number for scope creep. Actual additions: 3 (Task 2) + 5 (Task 3's three named tests, one of them ×3) + 1 (the RNG round trip) + 2 (FAKE 3 ×2) = **11**.
- **A `test_dp_noise_rng_round_trips_through_a_kill_and_resume` was added, which the plan does not list.** The plan wires both halves of D-14's slot but assigns no test to either; a splat that only a `grep` verifies is a wiring nobody has executed, and mutations 4 and 5 are only watchable because this test exists. It deliberately does NOT claim DPSGD-05's *bit-identical reported ε* — that is 22-07's, and it needs the accountant.
- **The σ=0 identity recipe sets `TrainConfig.grad_clip` to the same non-binding bound as `C`.** The plan's requirement (3) says to *"assert its returned norm is `<= train_cfg.grad_clip`"*; at the default `grad_clip = 1.0` this fixture's pre-clip norm is `2.0938` and the assertion simply fails. `C = ∞` on the DP side is meaningless for the identity unless the legacy clip is equally inert on the control side, so non-binding is arranged and then OBSERVED.
- **"Did the clip bind" is measured by OBSERVATION, not by `norm <= max_norm`.** torch computes `clip_coef = max_norm / (total_norm + 1e-6)`, so a `total_norm` in a razor-thin band just below `max_norm` yields `clip_coef < 1` and the clip binds while `norm <= max_norm` is True. The spy compares the gradient buffers before and after the real call instead. Both assertions ship; the buffer comparison is the load-bearing one.
- **Line anchors inside new code are cited by SYMBOL, never by line number**, continuing 22-02/22-03/22-04/22-05's habit. The plan's own `loop.py` anchors were all VERIFIED correct against HEAD before use (`:164`, `:165`, `:175`, `:176`, `:178-179`, `:180`, `:181`, `:182`, `:188-220`, `:252-291`, `:454-473`, `:475-487`, `:510-519`, and the three `save_checkpoint(` sites at `:577`/`:599`/`:625` with splats at `:589`/`:611`/`:637`) — the first Phase-22 plan whose anchors did not drift.
- **`dpsgd.py`'s module docstring was corrected in the same commit.** It claimed *"making it structurally unreachable inside an `if dp_fn is None` branch is plan 22-06's edit, not this module's"* — a forward reference this plan discharges. Rewritten to state what is now true and to name `loop.py`'s guard rather than implying the mechanism enforces it.
- **`math.inf` audit.** `grep -n "math.inf" tests/test_phase22_dpsgd.py` returns 6 hits: 3 in `test_inf_clip_norm_really_would_crash_the_noise_draw` (the positive control 22-04 hoisted into its own test), 2 in `test_clip_norm_must_be_finite`'s parametrize + docstring, 1 in a comment. The load-bearing half of the criterion holds exactly: **no `DPSGD(...)` construction anywhere passes `clip_norm=math.inf`** outside a `pytest.raises` refusal.

---

**Total deviations:** 7 auto-fixed (1 unsatisfiable tolerance instruction, 1 named guard measured incapable, 1 name-based exemption strengthened, 2 false statements in planning artifacts, 1 blocking environment issue, 1 tooling corruption), 7 deliberate departures.
**Impact on plan:** every correction makes a guard bite MORE or a claim narrower and truer; none weakens a guard or widens a claim. No scope creep — `pyproject.toml`, `checkpoint.py` and all three frozen `scripts/mitigation_*.py` are byte-unchanged.

## Tooling Corruption Encountered

Sixteenth consecutive session. Every `gsd-sdk` mutation call was followed by `git diff` on the three planning files and hand-repaired before the metadata commit. Recorded per the session's standing instruction:

| Handler | Defect observed | Repair |
|---|---|---|
| `state.advance-plan` | rewrote `Status: Executing Phase 22` back to `Status: Ready to execute` — identical to 22-01…22-05 | restored by hand |
| `roadmap.update-plan-progress 22` | wrote the status cell as `In Progress\|  \|` — no space before the pipe, empty date cell where every sibling carries `-`. Identical to all five prior plans | corrected to `\| 6/11 \| In Progress \| - \|` |
| `state.add-decision --summary` | prefixed every entry `- [Phase ?]:` | prefix corrected to `[Phase 22]`; `grep -c "Phase ?"` → **0** |
| `state.update-progress` | `{"updated": false, "reason": "Progress field not found in STATE.md"}` against a frontmatter that plainly has one | harmless; `advance-plan` had already set the block |
| `requirements.mark-complete DPSGD-02` | flipped the checkbox correctly but left the traceability row's notes cell **empty** — every sibling row carries its evidence | the cell was written by hand with the three fingerprints and their values |
| `state.record-metric --flag` / `state.record-session --stopped-at` | **correct** under the `--flag` form | — |

Fourth consecutive confirmation that the corruption lives in the **positional** argument path.

**Two behaviours DIVERGED from the prior five plans' records and are published rather than smoothed.** (a) `roadmap.update-plan-progress` **did** flip this plan's `- [ ] 22-06-PLAN.md` checkbox and **did** write the count correctly as `6/11` — both of which 22-04 and 22-05 recorded it failing at. The difference is ordering: this plan wrote `22-06-SUMMARY.md` **before** calling the handler, and the handler counts SUMMARY files on disk. That is a usable workaround, not a fix. (b) `state.advance-plan` wrote `completed_plans: 32 → 34`, a jump of two, which looks like corruption and is **not**: measured, there are exactly **34** `*-SUMMARY.md` files under `.planning/phases/` against 39 `*-PLAN.md`, so `34` is correct and the previous `32` was the stale value. Verified by count before accepting it.

## Issues Encountered

- **Three `ruff` `E501` wraps** (two docstring summary lines, one module-docstring paragraph). No assertion text or semantics changed; two `ruff format` passes re-wrapped a comprehension and an import block.
- **The `.gitignore` modification present at session start is pre-existing and untouched** — not staged in any commit here.
- **The V-12 fixture needed σ and C at 1.0, not the non-binding 1e6.** At `σ·C = 1e6` the noise std swamps the public replay term: float32's ULP at `1e6` is `0.0625`, so a replay contribution below ~0.03 is rounded away entirely and only 35 of 36 `lora_B` buffers differed. Measured and corrected before the test was written; recorded because the same trap will bite anyone building a differential over a noised buffer.

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest tests/test_phase22_dpsgd.py -q` | **29 passed, 0 skipped** (was 18) |
| `.venv/bin/python -m pytest tests/test_phase22_dpsgd_ast.py -q` | **17 passed** (was 16) |
| Task-1 verification set (`test_loop_penalty_fn` + `test_train_loop` + `test_masked_train_seam` + `test_extra_eval_fns` + both phase-22 files) | **53 passed, 1 skipped** (the skip is `test_amp_fp16_smoke`, needs CUDA) |
| `test_golden_trajectory_bit_identity` (Phase 10's own) | **RAN, passed** — not skipped on this box |
| `grep -c "dp_fn" src/personacore/training/loop.py` | **23** (criterion: ≥ 10) |
| `dp_fn` position on the `def` / at the call site | last parameter (`:153`) / last positional arg (`:629`) |
| `grep -n "clip_grad_norm_" loop.py` — CALL SITES | **1** (`:215`); the line above is `if dp_fn is None:`. 3 further grep hits are docstring prose |
| `grep -c "^\s*\*\*_dp_extra()," loop.py` == `grep -c "save_checkpoint(" loop.py` | **3 == 3** |
| `grep -c "def _dp_extra" loop.py` | **1** |
| the D-14 comments contain the literal `save_checkpoint(` | **no** — `save_checkpoint(` still counts 3 |
| `load_noise_rng_state` call in `loop.py` | inside `resume_from`, guarded by `ckpt.get("dp_noise_rng") is not None` |
| `grep -n "CKPT_SCHEMA_VERSION = " checkpoint.py` | **`= 1`** — unchanged |
| `git diff loop.py \| grep -c "^-[^-]"` | **6** — the `/accum` line, the clip line, 4 rewritten docstring lines. `replay_fn`'s body: **0 changed lines** |
| `ast.Raise` / `ast.Assert` in `dpsgd.py` | **25** / **0** |
| Seam mutation probe | **6 mutations, 6 distinct REDs** (row 6 after its new guard), control GREEN, sha256-identical restore of both source files |
| `git diff --exit-code -- pyproject.toml scripts/mitigation_{gate,unit,accountant}.py src/personacore/checkpoint.py` | exit 0 — byte-unchanged |
| Full suite `.venv/bin/python -m pytest -q` | **1231 passed, 1 skipped** in 208.95 s (baseline 1219/1 + 12 new) |
| `.venv/bin/ruff check . && .venv/bin/ruff format --check .` | clean, **200 files** formatted |

## Known Stubs

None. Every parameter added is consumed by a committed test, both new `DPSGD` accessors are exercised in both directions, and no placeholder was left for a later plan. The `dp_fn` seam is complete at `train()`; what it does NOT yet have is a **production caller** — `scripts/teach_persona.py:1167` still passes no `dp_fn`, which is D-08's wiring and plan 22-08's scope, recorded here so no reader mistakes a wired seam for a wired arm.

## Threat Flags

None. This plan adds no network endpoint, no auth path, no new file-access pattern (the only file I/O is the existing `save_checkpoint`/`load_checkpoint` pair, unchanged in shape), and no schema — `dp_noise_rng` rides the open `**extra` dict and `CKPT_SCHEMA_VERSION` stays `1`. Nothing was installed.

Threat register dispositions, each mitigated as planned:

- **T-22-26** (legacy clip still reachable on the DP path) — STRUCTURAL: one call site, inside `if dp_fn is None:`. RUNTIME: the spy observes 2 calls with the seam off and 0 with it on. Both halves; mutation 2 watched RED.
- **T-22-27** (`/accum` inherited on the DP path) — `loss = total if dp_fn is not None else total / accum` with the trap named in the comment; mutation 1 watched RED at `accum ∈ {3, 4}`, **and its blind spot at `accum = 1` is recorded rather than glossed**.
- **T-22-28** (released private magnitude becoming a function of public data) — `scaler.step(optimizer)` is the very next statement after `finalize`; V-12 measures the private term `torch.equal` across both branches, 72/72.
- **T-22-29** (a differential green because the fixture does not vary) — the mixed buffers are asserted to differ FIRST, at the exact structural count `_FROZEN_TENSORS // 2`, with the `lora_A`-is-zero reason stated.
- **T-22-30** (stale reported ε after resume) — `_dp_extra()` refreshes the LIVE state at all three sites; the saved value is asserted `torch.equal` to the live one; mutation 4 (end-of-call splat dropped) watched RED.
- **T-22-31** (σ=0 identity silently borrowing a non-binding clip) — BOTH clips asserted not to bind before the comparison, the legacy one by before/after buffer observation rather than by modelling `clip_coef`; and the default `grad_clip = 1.0` is recorded as genuinely BINDING on this fixture, so nothing is inert by accident.
- **T-22-31b** (a write-only `dp_noise_rng` slot) — the `.get()`-guarded restore, plus a runtime refusal against restoring into an already-stepped seam; mutation 5 watched RED.
- **T-22-SC** (package installs) — accepted; nothing installed, `pyproject.toml` byte-unchanged.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plan 22-07 (DPSGD-05) inherits a working `dp_noise_rng` slot and must not re-derive it.** The save is `_dp_extra()` at three sites, the restore is in the `resume_from` block, and both are watched RED. What 22-07 still owes: `checkpoint.py`'s **MPS RNG slot** (`rng["mps"]`, backward-compatible via `rng.get("mps")`, recorded as required-but-UNEXERCISED) and the kill→resume reproducing a **bit-identical reported ε**, which needs `accountant.epsilon_for` and — per 22-05's TOLERANCE REGISTER — **exact `==`, never `ROUND_TRIP_REL_TOL`**.
- **Plan 22-08 owns the production wiring, and it is the only thing between `dp_fn` and a real DP arm.** `scripts/teach_persona.py:1167` still passes no `dp_fn`, no `grad_accum_steps`, no `replay_*` and no fact bin. Two inherited facts it must not re-derive: (i) `TrainConfig.grad_accum_steps` defaults to `1`, and at `1` the D-02 inherited-divide fake is **structurally invisible** (mutation 1, row `[1]`, GREEN) — so `grad_accum_steps = n_facts` is not merely SC2 prose, it is what makes the trap detectable at all; (ii) `DPSGD.__init__` refuses an enabled scaler and an unfrozen base, so the caller must pass `runtime=` and must call `mark_only_lora_trainable`.
- **Plan 22-09 must not inherit D-17's FAKE 3 table entry.** Measured here, D-06's σ=0 identity does **not** detect *noise added after averaging*; the mutation leaves the whole suite green. `test_noise_is_scaled_by_the_lot_size_because_the_divide_comes_LAST` is the detector that does work, and 22-09's positive control for FAKE 3 should be run against it, not against the identity. The other three fakes already have live counterparts watched biting (FAKE 1 here, FAKE 2 here + 22-04 mutation 3, FAKE 4 22-04 mutation 2).
- **Plan 22-09 should also know the AST guard's re-seed exemption changed shape.** It is now a hard-equality `_ALLOWED_RESEED_SITES` dict, not `outside == {}`, and it is paired with an unreachability proof. A fake probe that inserts `manual_seed` into a step method still reddens it; one that inserts a *third* exempt-looking method reddens it too.
- **Anything asserting the generator state's byte count must assert the CPU figure.** Measured 5,056 bytes on CPU, 44 on MPS, and every Phase-22 test runs on CPU. The 44 that appears in planning prose came from an MPS probe.

## Self-Check: PASSED

- `src/personacore/training/loop.py` — FOUND
- `src/personacore/privacy/dpsgd.py` — FOUND
- `tests/test_phase22_dpsgd.py` — FOUND
- `tests/test_phase22_dpsgd_ast.py` — FOUND
- `.planning/phases/22-.../22-06-SUMMARY.md` — FOUND
- commit `8ecb789` — FOUND
- commit `3e1c71e` — FOUND
- commit `e2d4b0a` — FOUND

---
*Phase: 22-dp-sgd-core-accountant-and-the-correctness-battery*
*Completed: 2026-08-25*
