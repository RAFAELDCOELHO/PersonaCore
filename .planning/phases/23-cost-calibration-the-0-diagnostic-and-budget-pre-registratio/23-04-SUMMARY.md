---
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
plan: 04
subsystem: privacy-accounting
tags: [cal-03, d-05, d-06, dp-sgd, epsilon, wiring-probe, positive-control, ancestry-guard]

requires:
  - phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
    provides: "scripts/phase23_prereg.py — n64_leg_is_committable (D-06's BLIND withdrawal rule) and CAL03_WIRING_RECORD (the artifact path), both resolved from that edit-once module and never retyped"
  - phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
    provides: "tests/test_phase23_mps_venue.py::_DEVICES — the phase's single device register, imported so the ε/T pair is measured on BOTH cpu and mps with the mps leg a countable skip rather than an absence"
  - phase: 22-differential-privacy-sgd-and-the-analytic-accountant
    provides: "tests/test_phase22_checkpoint.py — _count_composed_steps (the per-instance finalize shadow T is read from), _tiny_lora_model(device=), _seam, _BATCH, _TINY, _TOTAL_STEPS, _DELTA, _DP_SEED, _MICRO_BS, _NON_BINDING_CLIP"
  - phase: 22-differential-privacy-sgd-and-the-analytic-accountant
    provides: "src/personacore/privacy/accountant.py::epsilon_for(sigma, steps, delta) and ROUND_TRIP_REL_TOL; src/personacore/privacy/dpsgd.py's per-step single-write invariant"
  - phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
    provides: "training/loop.py's replay seam and scripts/teach_persona.py::REPLAY_WINDOWS_PER_FACT — the SECOND path n_facts travels into the loop"
provides:
  - "tests/test_phase23_cal03.py — 11 tests: the measured no-N premise, ε/T bit-identity across capacity on cpu AND mps, the two-size N-leak positive control, the seam-level-finalize refusal, the AST single-verdict-path guard, the watched-RED ledger resolver, and the committed record's completeness/re-derivation check"
  - "results/phase23_cal03_wiring.json — CAL-03's verdict (TRUE) with full provenance; the record D-06's withdrawal decision is taken from and 23-13 reads rather than re-derives"
  - "the FIRST results/phase23_* artifact, which is what makes tests/test_phase20_prereg.py:332 and test_the_prereg_rule_precedes_every_phase23_result non-vacuous"
affects: [23-13 reads the verdict rather than re-deriving it, 23-05/23-08/23-10/23-11/23-14 now write under a LIVE ancestry guard, any plan tempted to edit scripts/phase23_prereg.py — that file is now permanently edit-once]

tech-stack:
  added: []
  patterns:
    - "a WIRING probe recorded as a first-class artifact that declares its own non-sweep-point scope structurally (sweep_point/exports_adapter/scope), so a content-side guard can exempt it without a name-based special case"
    - "the artifact emitted by the test module's own __main__ from the SAME helper the assertions call, then re-derived from its own stored values by a CPU-only test — the published number is re-checked every CI run, not trusted"
    - "ONE verdict producer per module, pinned by an AST guard counting call sites of the blind-committed rule"
    - "a positive control that names WHERE the modelled leak lives and commits the MEASURED refusal that ruled out the alternative shape"

key-files:
  created:
    - tests/test_phase23_cal03.py
    - results/phase23_cal03_wiring.json
  modified:
    - tests/test_phase20_prereg.py

key-decisions:
  - "23-04: CAL-03 CONFIRMED by a run — ε bit-identical at 24.38161088311366 across n_facts 8 and 64, T = 4/4 counted from the mechanism, at σ = 0.5 / δ = 1e-05 on MPS. The n=64 leg is COMMITTABLE; D-06's withdrawal branch does not fire."
  - "23-04: the probe drives BOTH paths N travels — grad_accum_steps = n_facts AND the REPLAY_WINDOWS_PER_FACT * n_facts replay budget. train(n_facts=...) alone is REFUSED by loop.py:512-524, so the fact-aligned loader path is out of a wiring probe's scope and is named as such rather than silently skipped."
  - "23-04: the N-leak positive control lives in the CALLER'S WIRING (extra optimizer steps derived from n_facts), not in a seam wrapper — an extra finalize per step is refused by [dp-invariant:single-write], measured and committed as a watched refusal."
  - "23-04: RETRACTED the plan's premise that a one-step T leak would vanish under a relative tolerance — measured 0.16372433057359725 at T 4→5 and 0.004427647757928591 at T 200→201, i.e. 1.6e11x and 4.4e9x ROUND_TRIP_REL_TOL. What a tolerance admits is the sub-ULP case the blind rule already pins."
  - "23-04: σ = 0.5 pinned with a reason resolvable from code (mu_eff = sqrt(T)/σ = 4.0, plus a value already in tests/test_phase23_prereg.py:467), NOT by the plan's 'σ ≥ 0.42' citation — that sentence was retracted in place at tests/fixtures/phase22_reference.py:243-269."
  - "23-04: ONE of the three Phase-23 ordering guards went live at the first artifact; the other two stay vacuous BY DESIGN, and the CONTENT guard now scans 1 record and admits it through its own sweep_point:false declaration."

patterns-established:
  - "Retract-in-place applied to a TEST DOCSTRING: test_phase20_prereg.py's 'Vacuous TODAY BY CONSTRUCTION' paragraph is left standing and a dated addendum records the measurement that ended it, rather than editing it to read as though it always bit."
  - "A plan-proposed mechanism that a committed invariant refuses is recorded as a RUNNABLE test, not as a SUMMARY sentence."

requirements-completed: [CAL-03]

duration: 50min
completed: 2026-08-26
---

# Phase 23 Plan 04: CAL-03 — ε Is Independent of N, Confirmed by a Run Summary

**CAL-03 is CONFIRMED and committed: ε is bit-identical at `24.38161088311366` between n_facts=8 and n_facts=64 at σ=0.5, with T=4/4 counted from `DPSGD.finalize` invocations rather than from a checkpoint field — so the n=64 leg is committable, and `results/phase23_cal03_wiring.json` is now the first `results/phase23_*` artifact, which is what arms the phase's ancestry guards.**

## Performance

- **Duration:** ~50 min
- **Tasks:** 3 of 3
- **Files created:** 2 · **modified:** 1
- **Suite:** `1409 passed, 1 skipped` (baseline `1398 passed, 1 skipped`; delta = the 11 new tests). `make lint` exits 0.
- **`tests/test_phase23_cal03.py`:** `11 passed in 13.09s`, **zero skips** on this M3 (MPS available, so the `mps` legs run).

## Task Commits

1. **Task 1: ε and T bit-identical across capacity at fixed σ** — `4377db4` (test)
2. **Task 2: the watched N-leak positive control** — `5faaec4` (test)
3. **Task 3: emit and commit `results/phase23_cal03_wiring.json`** — `bd81b44` (feat)
4. **Follow-on (Rule 1, caused by Task 3): retract the phase-20 guard's vacuity note in place** — `77649f1` (docs)

## The Verdict

`results/phase23_cal03_wiring.json`, produced on MPS (D-01's venue) at `git_sha 5faaec4`:

| field | value |
|---|---|
| `verdict` | **`true`** — the n=64 leg is committable |
| `epsilon_n8` / `epsilon_n64` | `24.38161088311366` / `24.38161088311366` (exact `==`) |
| `t_n8` / `t_n64` | `4` / `4` |
| `sigma` / `delta` | `0.5` / `1e-05` |
| `t_source` | `_count_composed_steps` |
| `n_facts_arms` | `[8, 64]` |
| `replay_windows_arms` | `[32, 256]` |
| `sweep_point` / `exports_adapter` | `false` / `false` |
| `device` / `torch_version` / `python_version` | `mps` / `2.7.1` / `3.11.15` |

D-06's withdrawal branch does **not** fire. The n=64 leg stands, with the measurement that stands it up committed.

**What this does and does not establish.** `epsilon_for`'s live signature is asserted to be exactly `["sigma", "steps", "delta"]` — three parameters, no N — so ε is N-independent *by construction of the accountant* and **this run cannot test the mathematics**. What it tests is the **wiring**: whether N leaks into the composed step count T. It does not. Both paths N travels were driven at both capacities: `grad_accum_steps = n_facts` (8 vs 64 micro-steps per optimizer step) and the replay budget `REPLAY_WINDOWS_PER_FACT * n_facts` (32 vs 256 windows per step, micro-batched to 16 vs 128 draws). T came out 4 on both, on **both devices**.

## Watched RED — both detectors, both leak sizes

Observed out-of-tree by wrapping `_run_capacity` with the leak and re-running the two committed detectors. Four distinct assertion messages; nothing about the harness is committed.

| leak | node id | observed RED |
|---|---|---|
| one-step (`n_facts // 64`) | `test_composed_step_count_is_equal_across_capacity[cpu]` | `T differs across capacity on cpu: n=8 composed 4 step(s), n=64 composed 5 … assert 4 == 5` |
| one-step | `test_epsilon_is_bit_identical_across_capacity[cpu]` | `ε differs across capacity on cpu: 24.38161088311366 (n=8) against 28.373473803257376 (n=64) at σ = 0.5, T = 4 / 5 … assert 24.38161088311366 == 28.373473803257376` |
| gross (`n_facts // 8`) | `test_composed_step_count_is_equal_across_capacity[cpu]` | `n=8 composed 5 step(s), n=64 composed 12 … assert 5 == 12` |
| gross | `test_epsilon_is_bit_identical_across_capacity[cpu]` | `28.373473803257376 (n=8) against 52.77062707609058 (n=64) at σ = 0.5, T = 5 / 12` |

The two detectors are genuinely independent in what they read — T is a count of mechanism invocations, ε is a function evaluated on that count. **Named rather than counted as a doubled win:** the two leak *sizes* redden the SAME two node ids. That is a coverage fact, not four detectors; what separates the sizes is the recorded relative ε difference below.

## The one-step number, and the claim it does NOT support

The plan asked for the one-step relative ε difference "so the SUMMARY can quote the number a tolerance would have swallowed". Measured, that framing is **false**, and it is retracted here rather than restated:

| pair | ε | relative difference | vs `ROUND_TRIP_REL_TOL = 1e-12` |
|---|---|---|---|
| T = 4 → 5 (this probe's scale) | `24.38161088311366` → `28.373473803257376` | **`0.16372433057359725`** | 1.6e11 × |
| T = 200 → 201 (production scale) | `519.6981942303134` → `521.9992347747968` | `0.004427647757928591` | 4.4e9 × |

A one-step leak is **not** what a relative tolerance hides — 16.4% would be caught by any tolerance below 16%, and even at production T it is 0.44%. ε is a deterministic function of T, so *any* integer change in T moves ε far above float noise; the ε detector is coarse-but-certain. What a tolerance actually admits is the **sub-ULP** case, and `phase23_prereg`'s own parametrized `math.nextafter(1.25, math.inf)` case is what pins that. The exact-`==` requirement stands; its stated justification is corrected.

Denominator and bound for the four figures above: each is one call to the committed `epsilon_for` at the stated `(σ, T, δ)`, reproducible from the record's own stored values — `test_the_cal03_record_is_complete_and_declares_its_scope` re-derives both published epsilons that way on every CI run, CPU-only.

## Vacuous → live: the guards this commit armed

`git ls-files 'results/phase23_*'` **before** `bd81b44`: **empty** (0 paths). **After**: `results/phase23_cal03_wiring.json` (1 path).

| guard | before | after |
|---|---|---|
| `tests/test_phase20_prereg.py::test_phase22_prereg_is_frozen_before_every_phase23_result` | `1 passed`, **0 ordering pairs** | `1 passed`, **1 ordering pair** — LIVE |
| `test_phase23_prereg.py::test_the_prereg_rule_precedes_every_phase23_result` | `checked = 0` | `checked = 1` — LIVE |
| `test_phase23_prereg.py::test_control_precedes_sigma_zero` | `checked = 0` | `checked = 0` — **still vacuous BY DESIGN** (`SIGMA_ZERO_RECORD` lands in 23-10) |
| `test_phase23_prereg.py::test_sigma_zero_precedes_every_noised_point` | `checked = 0` | `checked = 0` — **still vacuous BY DESIGN**; the CAL-03 record sits outside `NOISED_RECORD_GLOB`, which is the designed exemption |
| `test_phase23_prereg.py::test_every_noised_sweep_point_is_under_the_noised_glob` | scanned 0 records | **scanned 1** record and ADMITTED it via its explicit `sweep_point: false` — LIVE |

**Correction to the plan's framing:** it said "the three ordering guards survive the first artifact". They do, but only **one** of the three became non-vacuous; the other two cannot until their own endpoints exist. Stating "three went live" would have been a coverage over-claim. `tests/test_phase20_prereg.py -q`: `25 passed`. `tests/test_phase23_prereg.py -q`: `32 passed`.

Ancestry verified explicitly: the artifact's earliest add is `bd81b44b45246b14e4a6a7f209a72a4341bafc6b`, and **every** commit touching `scripts/phase23_prereg.py` (1), `scripts/mitigation_accountant.py` (1) and `scripts/mitigation_gate.py` (9) is a **strict** ancestor of it.

**`scripts/phase23_prereg.py` is now permanently edit-once.** `git diff --exit-code -- scripts/phase23_prereg.py` exits 0 for this plan; from this commit forward any edit to it turns `test_the_prereg_rule_precedes_every_phase23_result` permanently RED with no recovery path (`adds[-1]` takes the EARLIEST add, so delete-and-re-add cannot launder it). Corrections go through `scripts/_addendum.py`.

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 3 — Blocking] `train(n_facts=…)` is REFUSED without the three-bin fact seam**

- **Found during:** Task 1
- **Issue:** the plan's `_run_capacity` spec passes `n_facts=n_facts` to `train()` alongside `fixed_batch`. `training/loop.py:512-524` refuses that: the D-08 fact-aligned seam needs **all four** of `fact_bin`, `n_facts`, `train_bin`, `train_mask_bin` together, and raises `ValueError` on a partial set. Supplying them would require a real three-bin corpus — a full-fidelity arm, not a wiring probe.
- **Fix:** N is wired through the two paths **production** actually uses at this shape — `grad_accum_steps = n_facts` (`teach_persona.py:1352`) and `replay_windows = REPLAY_WINDOWS_PER_FACT * n_facts` (`teach_persona.py:1376`), the latter against synthetic replay bins built in-test in `tests/test_phase21_replay_volume.py:146-155`'s shape. `REPLAY_WINDOWS_PER_FACT` is imported from `teach_persona`, not retyped as `4`.
- **Scope named rather than glossed:** the fact-aligned **loader** path (`get_batch_fact_aligned`) is NOT exercised here. It is a data-selection path, not a step-count path, and its own per-window invariant (`sorted(seen) == list(range(n_facts))`) already lives in `loop.py:843`.
- **Files:** `tests/test_phase23_cal03.py` · **Commit:** `4377db4`

**2. [Rule 3 — Blocking] the plan's `_LeakySeam` shape is refused by a committed DP invariant**

- **Found during:** Task 2
- **Issue:** the plan asked for a seam wrapper "composing an extra `finalize` for every k records". MEASURED, `DPSGD._write_once` refuses it: `RuntimeError: [dp-invariant:single-write] 24 writes for 12 trainable parameters`. A second `finalize` inside one optimizer step re-releases private data the accountant charged for once, which is exactly what that invariant exists to stop. The plan's own stated reason for the wrapper — *"the leak being modelled is in the caller's wiring, not in `dpsgd.py`"* — is satisfied better by a caller-side leak anyway.
- **Fix:** the leak is a caller deriving `n_facts // divisor` **extra optimizer steps** — the single most common way N reaches T in a training script. The refusal that ruled out the alternative is committed as a runnable test (`test_a_seam_level_extra_finalize_is_refused_by_the_single_write_invariant`) rather than left as a sentence here.
- **Files:** `tests/test_phase23_cal03.py` · **Commit:** `5faaec4`

**3. [Rule 1 — Stale citation] the plan's σ justification points at a RETRACTED sentence**

- **Found during:** Task 1
- **Issue:** the plan says "σ ≥ 0.42 is the regime the Phase-22 band work characterized". That sentence was **retracted in place** on 2026-08-26 at `tests/fixtures/phase22_reference.py:243-269`: the error is not zero at σ ≥ 0.42, it reaches machine epsilon only past σ ≈ 0.425 and is ~1e-16 even there. Pinning a constant on a retracted claim is the defect class this repository has been closing all phase.
- **Fix:** `_SIGMA = 0.5` with a reason resolvable from code — `mu_eff = sqrt(steps)/σ = 4.0` at T=4, far from both the erfc-subnormal band and `EPSILON_OVERFLOW_REGIME`'s σ ∈ {0.30, 0.40} / T=200 rows; and it is a value this phase already wrote down before any CAL-03 number existed (`tests/test_phase23_prereg.py:467`). The retraction is recorded in the constant's own comment. σ was **not** retried: one value, chosen before the run (T-23-22).
- **Files:** `tests/test_phase23_cal03.py` · **Commit:** `4377db4`

**4. [Rule 1 — False premise, retracted in place] "a one-step leak would vanish under any plausible relative tolerance"**

- **Found during:** Task 2 — see the table above. Measured `0.16372433057359725`, not a sub-tolerance quantity.
- **Fix:** the number is recorded as asked, and the claim it was asked to support is corrected in the test docstring and here. The `==` requirement is unchanged; only its justification moves to the sub-ULP case.
- **Files:** `tests/test_phase23_cal03.py` · **Commit:** `5faaec4`

**5. [Rule 2 — Correctness] `_run_capacity` returns `_Arm(t, epsilon)`, not `(len(calls), ckpt_dict)`**

- **Issue:** the plan's signature hands back the checkpoint dict, which invites the `ckpt["step"]` read T-23-19 exists to forbid — and `grep -c 'ckpt\["step"\]'` is an acceptance criterion returning **0**.
- **Fix:** the helper returns only the counted T and the ε derived from it. The meta-guard the ckpt would have served is asserted directly instead: `dp._records == n_facts` (`tests/test_phase22_checkpoint.py:469`'s own guard), so a run where `dp_fn` was silently dropped cannot report T=0 for both arms and pass "bit-identical" while measuring nothing.
- **Files:** `tests/test_phase23_cal03.py` · **Commit:** `4377db4`

**6. [Rule 1 — Stale claim, directly caused by Task 3] `tests/test_phase20_prereg.py`'s vacuity paragraph**

- **Issue:** `test_phase22_prereg_is_frozen_before_every_phase23_result` documented itself as *"Vacuous TODAY BY CONSTRUCTION … Nothing matches `results/phase23_*` yet"*. Commit `bd81b44` made that false.
- **Fix:** the original paragraph is **left standing** as the record of what was true when written; a dated `SUPERSEDED 2026-08-26 (plan 23-04)` addendum records the measurement that ended it. Same discipline the accountant's own reference fixture uses.
- **Files:** `tests/test_phase20_prereg.py` · **Commit:** `77649f1`

### Structural notes (not defects)

- `test_the_verdict_uses_the_blind_committed_rule` sits ahead of the leak block in the file so Task 1 could be committed as a standalone green increment.
- The record's `governs` field names `scripts/mitigation_budget.py` as the consumer. **That module does not exist yet** — 23-09 writes it, under the zero-import ceiling 23-02 measured. The reference is forward-looking by design and is named as such here so nobody reads it as a broken link.

## Known Stubs

None. Every value in `results/phase23_cal03_wiring.json` is produced by the same `_run_capacity` the assertions run on; no placeholder, no hardcoded empty, no TODO.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema at a trust boundary. The one new file under `results/` is inside the `results/phase23_` prefix every Phase-23 ancestry guard binds on, which is the opposite of new unwatched surface.

Threat register dispositions discharged: **T-23-17** (`grep -c "rel_tol\|isclose\|approx\|pytest.approx"` → **0**, and the one-step relative difference is recorded), **T-23-18** (both detectors watched reddening at two leak sizes), **T-23-19** (`grep -c 'ckpt\["step"\]'` → **0**; T from `_count_composed_steps`), **T-23-20** (`math.isfinite` asserted on both arms before the `==`), **T-23-21** (`sweep_point: false` / `exports_adapter: false` / `scope`, outside `NOISED_RECORD_GLOB`, and the content-side guard observed admitting it), **T-23-22** (σ pinned with its reason before the run; not retried), **T-23-SC** (zero installs; `git diff --exit-code -- pyproject.toml` exits 0).

## Verification

```
.venv/bin/python -m pytest tests/test_phase23_cal03.py -v      → 11 passed, 0 skipped (13.09s)
.venv/bin/python -m pytest tests/test_phase23_prereg.py -q     → 32 passed
.venv/bin/python -m pytest tests/test_phase20_prereg.py -q     → 25 passed
.venv/bin/python -m pytest tests/ -q                           → 1409 passed, 1 skipped
make lint                                                      → All checks passed; 234 files already formatted
git diff --exit-code -- scripts/phase23_prereg.py scripts/mitigation_accountant.py \
                        scripts/mitigation_gate.py pyproject.toml   → exit 0
grep -c "rel_tol\|isclose\|approx\|pytest.approx" tests/test_phase23_cal03.py  → 0
grep -c 'ckpt\["step"\]' tests/test_phase23_cal03.py                          → 0
```

The single skip is pre-existing: `tests/test_train_loop.py:81`, the fp16-AMP smoke that needs a CUDA GPU.

## gsd-sdk hazards — THIRTEENTH session in a row, profile shifted again

Every handler's output was diffed against a pre-call snapshot and hand-repaired line-exactly in this commit. Nothing was fixed by calling a second handler.

- `state.advance-plan` — counters CORRECT (`Plan: 4 of 14` → `5 of 14`), but **`completed_plans` did NOT increment** (stayed `50`; hand-set to `51`) — the increment worked in 23-02 and regressed here. Flattened the body `Status:` prose from `Executing Phase 23` to `Ready to execute`. Returned `last_updated` **QUOTED**. Did **not** regress `stopped_at` this time.
- `state.update-progress` — `{"updated": false, "reason": "Progress field not found in STATE.md"}`, the same string since 22-12, and its **claimed no-op still re-stamped and re-quoted `last_updated`**. `percent`/`completed_phases` untouched.
- `state.record-metric` — refused positional args (`{"error": "phase, plan, and duration required"}`); with `--phase/--plan/--duration/--tasks/--files` it was CLEAN.
- `state.add-decision` — **NEW FAILURE MODE: a silent total no-op.** Six positional calls all returned without error and wrote **nothing** (`git diff` showed 0 decision lines). Previous sessions corrupted the label to `- [Phase ?]: `; this one dropped the content entirely, which is worse because the corruption was visible and this is not. All six decisions hand-appended, plus a seventh recording these hazards.
- `state.record-session` — updated the body `Last session` but **left `stopped_at` at `Completed 23-03-PLAN.md`**; hand-corrected to `23-04`. (In 23-02 this handler set both.)
- `roadmap.update-plan-progress 23` — mangled the phase row's trailing cells from `| In Progress | -          |` to `| In Progress|  |`, dropping the `-` placeholder, exactly as in 23-02. Run before the SUMMARY existed it also reported `summary_count: 3`; the row was restored from snapshot and the count hand-set to `4/14`.
- `requirements.mark-complete CAL-03` — ticked the checkbox CORRECTLY but left the traceability row `| CAL-03 | Phase 23 | |` **empty**; hand-filled.

Line counts verified: `STATE.md` 662 → **670** (1 metric row + 7 decisions), `ROADMAP.md` 804 → **804** (one row edited in place).

## Self-Check: PASSED

- `tests/test_phase23_cal03.py` — FOUND
- `results/phase23_cal03_wiring.json` — FOUND, tracked (`git ls-files` returns it)
- `4377db4`, `5faaec4`, `bd81b44`, `77649f1` — all FOUND in `git log`
