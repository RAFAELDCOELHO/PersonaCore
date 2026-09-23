---
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
plan: 06
subsystem: testing
tags: [dp-sgd, mps, apple-silicon, device-parametrization, watched-red, dpsgd-04, venue-transfer]

requires:
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "DPSGD-04's four fake probes and their CPU-observed REDs, the `_mutate` / `_run_live_guard` mutation register, and the two fitted constants this plan re-measured"
  - phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
    plan: 01
    provides: "`_DEVICES` / `_MPS_SKIP` (the phase's single device register) and `_model(device=)` / `_record`'s CPU-draw-move-tensor discipline"
provides:
  - "the four DPSGD-04 fakes' RUNTIME halves watched refusing on MPS — 7 `[mps]` legs in tests/test_phase22_fakes.py, plus 1 function-gated cross-device measurement"
  - "a DEVICE-QUALIFIED watched-RED register: every entry is `(node_id, observed_on)` over cpu / mps / device-invariant, 13 entries, all re-collected"
  - "the AST exemption as a RE-CHECKED property (`test_the_device_invariant_halves_are_named_and_still_device_free`) rather than a comment — 53 of 115, measured over ast.parse"
  - "the venue-transfer ledger, enforced by two tests that assert against this SUMMARY, including a skip count parsed and asserted to be 0"
  - "three measured cross-device divergences published as literals rather than smoothed: `_global_norm`, `_FAKE1_LEAK_RATIO`, `_FAKE3_STD_RATIO_AT_N4`"
affects: [23-07 resume seam, 23-08, 23-10 (the sigma=0 headline run and DPSGD-06's close), every Phase-23 plan publishing an epsilon produced on the M3]

tech-stack:
  added: []
  patterns:
    - "device claimed by a node id is ASSERTED against the fixture (`_params_of(model, device)`) and against the seam (`_seam_on`) — a parametrization id is not evidence of a device"
    - "an exemption is a re-measured property, never an absence: AST-scan the exempt files for module-scope torch imports, device string constants and their test counts"
    - "a venue transfer is a new OBSERVATION, not a new SIGNATURE — counted separately so coverage claims cannot inflate on re-runs"
    - "sign-off rows carry the SUMMARY they are checked against, so a later phase's finding never forces an edit to a closed earlier artifact"

key-files:
  created: []
  modified:
    - tests/test_phase22_fakes.py
    - tests/test_phase23_mps_venue.py

key-decisions:
  - "23-06: research's BIT-IDENTICAL `_global_norm` row does NOT hold on this file's fixture; the test asserts the MEASURED divergence and its 2,500x headroom instead of asserting a property that is false"
  - "23-06: `_FAKE3_STD_RATIO_AT_N4` and `_FAKE1_LEAK_RATIO` are BYTE-UNCHANGED — both MPS readings land inside their recorded bands, so A1's re-record-never-widen disposition needed no re-record"
  - "23-06: the AST halves run on the `cpu` leg only (`_AST_HALF_RUNS_ON`); an `[mps]` id over `ast.parse` would claim a device pass it did not perform"
  - "23-06: `_DISTINCT_RED_SIGNATURES` stays 9 while the register grows to 13 — the four mps rows are the same invariants refusing on a second device"
  - "23-06: DPSGD-06 was NOT ticked, for the third plan running — it names a RUN that has not happened; 23-10 closes it"

requirements-completed: []

duration: 50min
completed: 2026-08-26
---

# Phase 23 Plan 06: The Four Fakes, Watched Reddening on MPS Summary

**DPSGD-04's four positive controls now refuse on the venue that will publish the ε — 7 `[mps]` legs green with zero skips — and the crossing is recorded as a per-probe ledger with three measured divergences published as literals, including one that contradicts the research doc it was planned from.**

## Performance

- **Duration:** ~50 min. **Evidenced span:** first task commit `3e19510` at `2026-08-26T22:25:05-03:00` to the metadata commit, ~30 min; the plan read and the pre-edit CPU/MPS probe run preceded it by roughly 20 min. Stated as an estimate because no start timestamp was captured, rather than as a figure with no basis.
- **Tasks:** 3
- **Files modified:** 2 (0 created, 2 modified)

## What did and did not cross CPU → MPS

**Phase 22's result is recorded as a Phase-22 result: it was produced on CPU and it has `not transferred to MPS`.** What follows is not that record re-labelled — it is a second, independent set of observations made on the M3, per probe, each one an actual `pytest.raises` that fired. Where a half was NOT re-run, the row says so and says why.

| Probe | Re-watched on | Node id | Outcome |
|---|---|---|---|
| **V-15** kill→resume ε bit-identity | **mps** | `test_phase22_checkpoint.py::test_resume_epsilon_bit_identical[0.0-mps]` and `[1.0-mps]` | 4 passed (2 σ × 2 devices). Wired by 23-01; **re-run here rather than inherited** |
| **FAKE 1** clip the averaged gradient | **mps** (runtime half) | `test_phase22_fakes.py::test_fake_averaged_gradient[mps]` | `[dp-invariant:drain]` observed refusing on step 2; leak ratio re-measured |
| **FAKE 2** wrong sensitivity | **mps** (runtime half) | `test_phase22_fakes.py::test_fake_wrong_sensitivity[mps]` | `[dp-invariant:sensitivity]` observed refusing; the one-sided direction still measured GREEN, as recorded |
| **FAKE 3** noise after averaging | **mps** (runtime half) | `test_phase22_fakes.py::test_fake_noise_after_averaging[mps-1.0-4]` | differential separated the mutation; ratio re-measured. All three blind spots transferred as blind spots |
| **FAKE 4** RNG reuse across steps | **mps** (runtime half) | `test_phase22_fakes.py::test_fake_rng_reuse[mps]` | `[dp-invariant:generator]` observed refusing on step 2, over the **44-byte** MPS state |

### The half that was NOT re-run, and why — the `AST half` exemption

The four fakes' **`AST half`** — the `_mutate` + `_run_live_guard` acts that apply the mutation to the REAL committed `src/personacore/privacy/dpsgd.py` source and run the live guard over it — **was NOT re-run on MPS.** It runs on the `cpu` leg only, gated by `_AST_HALF_RUNS_ON`.

This is a `device-invariant` exemption, and it is now an ASSERTED property rather than a sentence. `ast.parse` over source text has no tensor, no generator and no device; an `[mps]` node id re-executing byte-identical code would be a probe *claiming a device pass it did not perform*, which is T-23-28 — the exact defect D-02 exists to prevent. The two wholly exempt Phase-22 files are `tests/test_phase22_dpsgd_ast.py` (16 tests) and `tests/test_phase22_accountant.py` (37), i.e. **53 of 115** — and `test_the_device_invariant_halves_are_named_and_still_device_free` re-measures all three properties the exemption rests on (no module-scope torch import, no `"cpu"`/`"mps"` string constants, the per-file counts) over `ast.parse`, not over grep, because both files discuss torch at length in prose.

**The denominator moved and is re-recorded rather than left standing.** It was **53 of 113** at Phase 22's close (accountant 37 / checkpoint 9 / dpsgd_ast 16 / dpsgd 23 / fakes 8 / wiring 20). 23-01 added one checkpoint test and this plan added one fakes test, so it is **53 of 115** here. The numerator is asserted exactly; the denominator one-sidedly (it can only grow), because what the exemption claims is a property of the numerator and a two-sided assertion would turn every future Phase-22 test into a failure in this file.

**Consequence, stated plainly rather than left for a reader to infer:** on the MPS leg, no mutation is ever applied to the real committed module. Each fake's runtime half on MPS is expressed by the same object-level subclass (`_DrainDropped`, `_ClipsToASecondConstant`, `_DivideBeforeNoise`, `_ReseedsInStep`) Phase 22 used, whose docstrings record it as the object-level form of the identical source edit. What the MPS legs add — and it is the only thing that could have differed — is the DEVICE-DEPENDENT half: the drawn values, the accumulator, the generator state, and the refusals over them.

### The cross-device state divergence, both devices named

| Quantity | reading, both devices named on the row |
|---|---|
| dedicated generator state, `torch.Generator.get_state()` | **cpu: 5,056 bytes — mps: 44 bytes** |

Both states are resident **on CPU** whatever the generator's device, which is why every `torch.equal(state_a, state_b)` in `dpsgd.py` is device-safe exactly as written and no `.cpu()` plumbing was added anywhere. The two are **mutually refused** by torch. This row exists because `22-07-SUMMARY.md:118` prints `5,056 bytes` in **both** columns — both of its runs were CPU — so the divergence the whole checkpoint boundary rests on is invisible in the artifact that documents it. `test_venue_transfer_ledger_is_recorded` now requires both numbers and both device names on one line, so that table cannot be repeated here.

## The two fitted constants, re-measured

Both were expected to be at risk; only one genuinely was. **Expectation first, measurement second, in that order, so a divergence is visible rather than absorbed.**

| Constant | cpu | mps | \|delta\| | band | disposition |
|---|---|---|---|---|---|
| `_FAKE1_LEAK_RATIO` | `1.7344813665273022` | `1.734481393949083` | `2.742e-08` (rel `1.58e-08`) | `0.02` (rel `1.15e-02`) | **byte-unchanged** |
| `_FAKE3_STD_RATIO_AT_N4` | `3.9999861813196698` | `3.9999995238454056` | `1.334e-05` (rel `3.34e-06`) | `0.01` (rel `2.50e-03`) | **byte-unchanged** |

**FAKE 1 — the expectation was BIT-IDENTITY, and it was not met.** `_record` keeps its CPU generator and moves only the tensor, so the gradients entering the probe *are* byte-identical on both devices; 23-01 recorded that as keeping the constant valid "by construction". Measured, the ratio still moves by `2.742e-08`. The draw is identical; the **fp32 reduction inside `_global_norm` is not**, and every ratio here is a quotient of two such reductions. The band was never in danger — the divergence is five orders of magnitude inside it — but "by construction" was one word too strong and is corrected here.

**FAKE 3 — the one genuinely at risk, and it held.** Its differential is a property of the DRAWN VALUES, and on MPS those come off an MPS generator, so the noise vectors are genuinely different numbers rather than the same numbers reduced differently. The ratio survives because it is **structural** (it is `N`, not a fit), which is what `23-RESEARCH.md` §R1.4 predicted. The MPS reading is in fact the *closer* of the two to `N = 4`. **The band was not widened and could not have been:** `23-RESEARCH.md` Assumption A1 committed the disposition — re-record both readings, never widen — before the number was seen, and since the reading landed inside the band, no re-record was required either.

### A third divergence, measured because the plan's premise assumed it away

`23-RESEARCH.md` §R1.3 records `_global_norm` over a 72-tensor LoRA-shaped fixture as **BIT-IDENTICAL** across cpu and mps at `0.4707888662815094`, and this plan's Task 1 asked for that to be committed as `test_global_norm_is_bit_identical_across_devices` asserting `torch.equal`.

**Measured on the fixture the two fitted constants actually rest on** — `_record(_params_of(_model(device=...)), 1)`, 72 tensors, the same fixture FAKE 1 and FAKE 2 derive their clip from:

| | cpu | mps | absolute | relative |
|---|---|---|---|---|
| `_global_norm` over 72 LoRA-shaped tensors | `0.5771376490592957` | `0.5771377086639404` | `5.960e-08` | `1.033e-07` |

**It is not bit-identical.** The divergence is `1.033e-07` relative — a single float32 rounding step (`eps = 1.192e-07`) — and it is the whole of the cross-device numeric difference in FAKE 1 and FAKE 2. Research's `0.4707888662815094` is not reproducible from any fixture in this file and is not the fixture the dependent constants were fitted to; the two claims are about different tensors.

A test named `..._is_bit_identical_...` would have gone RED, correctly. The committed test is
`test_global_norm_across_devices_diverges_far_below_the_fitted_bands`, which asserts both halves — that the divergence is inside a named bound (`1e-6`), **and** that the bound is at least 100× inside the tighter of the two bands whose validity it is being used to argue for (measured headroom: 2,500×). Either half alone would mislead. Its docstring states the honest bound the plan asked for: **this is ONE FIXTURE, NOT A PROOF** — fp32 reductions differ by reduction order, and reduction order is a backend's choice.

## The skip count, as a number

The literal terminal line from `.venv/bin/python -m pytest tests/test_phase22_checkpoint.py tests/test_phase22_dpsgd.py tests/test_phase22_fakes.py tests/test_phase23_mps_venue.py -q` on the M3:

```
90 passed in 33.27s
```

pytest **omits a zero skip count from that line**, so the absence of the word "skipped" is not evidence. The count is therefore **OBSERVED** from the same run's `--junit-xml` `testsuite` attributes:

```
tests 90   failures 0   errors 0   skipped 0
```

`test_the_ledger_states_a_skip_count_of_zero` parses that line out of this file and asserts the number is `0` — plus `failures == errors == 0`, because a skip count of zero beside a red run is not evidence of a venue pass.

**MPS-executing items in that run: 28 of 90 collected** — measured as (node ids whose bracketed parameter contains `mps`) + (function-level `@_MPS_SKIP` tests), per file:

| File | collected | mps param legs | fn-gated mps-only | MPS items |
|---|---|---|---|---|
| `test_phase22_checkpoint.py` | 15 | 2 | 1 | 3 |
| `test_phase22_dpsgd.py` | 39 | 9 | 0 | 9 |
| `test_phase22_fakes.py` | 20 | 7 | 1 | **8** |
| `test_phase23_mps_venue.py` | 16 | 6 | 2 | 8 |

The **8** in `test_phase22_fakes.py` are this plan's entire addition to the MPS surface; the other 20 predate it. Full suite on the M3, with this SUMMARY on disk so the two ledger tests assert rather than skip: `1463 passed, 1 skipped` (baseline at the plan's base commit: `1452 passed, 1 skipped`). The one skip is **pre-existing and unrelated** — `tests/test_train_loop.py:81: fp16 AMP smoke needs a CUDA GPU`, and there is no CUDA on this machine.

## Task Commits

1. **Task 1: the four fakes, re-applied on MPS and observed RED** — `3e19510` (test)
2. **Task 2: a device column in the watched-RED ledger, and the AST exemption recorded** — `803a19b` (test)
3. **Task 3: the venue-transfer ledger, with the skip count as a number** — `a553ca2` (test)

## Files Created/Modified

- `tests/test_phase22_fakes.py` — the four probes parametrized over `_DEVICES`; `_params_of(model, device)` and `_seam_on` as the two device-honesty tripwires; `_AST_HALF_RUNS_ON`; `test_global_norm_across_devices_diverges_far_below_the_fitted_bands`; `_WATCHED_RED_NODE_IDS` device-qualified to 13 `(node_id, observed_on)` pairs; `_MPS_OBSERVATIONS_PER_FAKE`; `_DEVICE_INVARIANT_HALVES` + its re-checking test; `_LEDGER_SIGN_OFF_ITEMS` extended to 3-tuples carrying their own SUMMARY.
- `tests/test_phase23_mps_venue.py` — `_VENUE_SUMMARY_PATH` (defined once, imported by the fakes file); `test_venue_transfer_ledger_is_recorded` (six independent assertions); `test_the_ledger_states_a_skip_count_of_zero`.

## Decisions Made

- **The device a node id claims is asserted, in two places, because one would not be enough.** `_params_of(model, device)` ties the parametrization *string* to the fixture's actual device — the only check that can catch an `[mps]` leg whose `_model(device=...)` silently fell back. `_seam_on` reads the device off the *model* and asserts the seam's generator AND accumulator followed it — the only check that can catch a CPU generator drawing the noise for an "MPS" probe, which would make FAKE 3's and FAKE 4's device legs vacuous while still reporting green. Neither subsumes the other.
- **The AST halves are gated to `cpu`, which makes the sign-off row TRUE rather than aspirational.** The plan's Task 1 action asks the MPS leg to apply the mutation via `_mutate` and run the guard through `_run_live_guard`; its Task 2(c) asks the sign-off to record that the AST halves were NOT re-run on MPS. Those two cannot both hold — `_mutate` + `_run_live_guard` *is* the AST half. The must-haves resolve it: the exemption is explicit and load-bearing there, the Task 1 sentence is not. Gated, and the conflict is recorded below rather than silently resolved.
- **`_DISTINCT_RED_SIGNATURES` stays 9 while the register grows to 13.** A venue transfer is the same fake tripping the same invariant with the same message on a second device: a new OBSERVATION, not a new SIGNATURE. Folding the four `"mps"` rows into the total would have reported a 44% coverage increase that bought no detection — the inverse of the file's own rule that a shared signature is a coverage gap to name rather than a second win to count. They are counted by `_MPS_OBSERVATIONS_PER_FAKE` and required to be exactly one per fake, so a fake whose venue transfer is dropped fails loudly.
- **`_LEDGER_SIGN_OFF_ITEMS` rows now carry their own SUMMARY path.** The plan asked for two new rows recording Phase-23 facts. Those rows asserted against `22-11-SUMMARY.md` would be RED forever, and the only way to make them pass would be to edit a closed Phase-22 artifact so a Phase-23 test could go green — the pin-corrections-are-continuations defect class. The third column resolves it without weakening either half.
- **The `rng["mps"]` disclosure was REWRITTEN, not deleted.** Phase 22 recorded that slot as required-but-unexercised because the whole battery was CPU-only. After 23-01 and this plan it is exercised on the M3 with a skip count of zero, and it remains unexercised in CI (`ubuntu-latest`, CPU-only wheel). Narrowing a disclosure as evidence arrives is the opposite of dropping it; the required literal is unchanged so 22-11's own sign-off still has to carry it.
- **DPSGD-06 was not ticked.** The plan's frontmatter claims it, and this is the third Phase-23 plan to decline. The requirement reads *"the σ=0 point is the DP arm's **first executed run**"* — a RUN, not a probe. Six plans in this phase claim it; `23-10` is the last in wave order and the correct place to close it.

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 1 — Bug] The module docstring's `CPU-only, GPU-free.` line became false**

- **Found during:** Task 1
- **Issue:** `tests/test_phase22_fakes.py:29` read `CPU-only, GPU-free.` — accurate through Phase 22 and false the moment the four probes gained `[mps]` legs. `tests/test_phase22_dpsgd_ast.py:41` and `tests/test_phase22_accountant.py:16` carry the same sentence and are still correct there, which is exactly what would make a stale copy here hard to spot.
- **Fix:** rewritten to state what is now true — the runtime halves run on both devices, the AST halves are exempt at the point of use, and the file is GPU-free in the CUDA sense with the MPS legs `skipif`-gated so CI stays green.
- **Committed in:** `3e19510`

### Plan/code discrepancies, recorded rather than silently absorbed

**2. Research's bit-identical `_global_norm` row does not hold here — the largest one**

Covered in full above. The plan's Task 1 named a test `test_global_norm_is_bit_identical_across_devices` and prescribed `torch.equal`. Measured, the property is false on this file's fixture (`1.033e-07` relative divergence), and research's `0.4707888662815094` is not reproducible from any fixture in this file. The test ships under an honest name asserting the measured bound and its headroom. **The two fitted constants are byte-unchanged because the measurement supports them, not because the check was relaxed to fit** — the divergence is four orders of magnitude inside both bands.

**3. Task 1 and Task 2(c) contradict each other on the AST halves**

Task 1: *"the MPS leg must perform the SAME two acts the CPU leg performs: apply the mutation … via `_mutate`, run the guard through `_run_live_guard`"*. Task 2(c): record *"the four fakes' AST halves were NOT re-run on MPS because they cannot differ by device"*. `_mutate` + `_run_live_guard` **is** the AST half, so at most one is satisfiable. Resolved toward the exemption, which the must-haves state twice and which T-23-28 exists to enforce. The consequence — no source mutation occurs on the MPS leg — is stated in the ledger above rather than left to be discovered.

**4. `_lot_sum` / `_released` / `_two_steps` needed no `device` parameter**

Task 1 asked for `device` to be threaded into all three. Measured: each constructs its seam from the model, and `DPSGD.__init__` derives both the accumulator and the generator device from `params[0].device` (D-14), so placement was already correct with zero threading. What they *did* need was the assertion that placement happened, which `_seam_on` supplies by reading the device off the model — so no call site can pass it wrong, the same discipline `_record` already uses. Threading a parameter would have added the one thing that can be got wrong.

**5. The plan's `_seam(..., runtime=RuntimeConfig(device=device))` does not exist in this file**

`_seam` is `tests/test_phase23_mps_venue.py`'s helper. `tests/test_phase22_fakes.py` constructs `DPSGD` (and its four fake subclasses) directly and passes no `runtime` at all. None was added: `RuntimeConfig.__post_init__` forces `amp=False` for both `cpu` and `mps` (`config.py:56-59`), so D-04's live-scaler refusal is inert either way and a `runtime` here would be a knob with no effect.

**6. The exemption's denominator was stale before this plan touched it**

The plan specifies "53 of 113" throughout. Measured at the base commit it was already **53 of 114** — 23-01 added `test_cpu_written_dp_noise_rng_is_refused_on_mps` to the checkpoint file without updating the count 23-01 itself had written. It is **53 of 115** after this plan's own added test. Re-recorded with the breakdown and the reason it moved, and the per-file counts are now asserted so the next drift fails a test instead of surviving into a third plan.

---

**Total deviations:** 1 auto-fixed (Rule 1) + 5 plan/code discrepancies recorded.
**Impact on plan:** none on scope. Every task's underlying obligation was met; two of the discrepancies (2 and 6) are findings the plan's own premises would have concealed, and both are published rather than smoothed.

## Issues Encountered

None requiring problem-solving. One `NameError` on `ast` between Task 1 and Task 2 (the import was removed to satisfy `ruff` F401 in Task 1's commit, where it was not yet used, and restored in Task 2) — caught by the suite, one line.

## Threat Register Coverage

| Threat ID | Disposition | How it is discharged |
|---|---|---|
| T-23-28 (a probe claiming a device pass it did not perform) | mitigated | `_params_of(model, device)` + `_seam_on` assert the claimed device against the fixture AND the seam; the AST halves are gated to `cpu` rather than run under an `[mps]` id; the exemption is re-measured by `test_the_device_invariant_halves_are_named_and_still_device_free` |
| T-23-29 (a band widened to absorb an MPS divergence) | mitigated | both bands byte-unchanged and both readings published with deltas; `_REQUIRED_CONSTANT_LITERALS` makes all six numbers required literals of this file |
| T-23-30 (a green suite on the M3 that skipped the venue tests) | mitigated | `test_the_ledger_states_a_skip_count_of_zero` parses the junit attributes above and asserts `0` |
| T-23-31 (a transient mutation surviving into the commit) | mitigated | `git diff --exit-code -- src/personacore/privacy/dpsgd.py` exits **0** |
| T-23-32 (the honest `rng["mps"]` disclosure deleted rather than made precise) | mitigated | rewritten to distinguish CI from the M3; the literal is unchanged and `test_fakes_ledger_names_its_blind_spots` still requires it in 22-11's sign-off |
| T-23-SC (package installs) | accepted | **zero installs.** `git diff --exit-code -- pyproject.toml` exits 0 |

## Frozen-pin verification

`git diff --exit-code -- src/personacore/privacy/dpsgd.py scripts/mitigation_accountant.py scripts/mitigation_gate.py scripts/phase23_prereg.py pyproject.toml` exits **0**. `scripts/phase23_prereg.py` is permanently edit-once now that `results/phase23_cal03_wiring.json` exists; nothing in this plan reads or writes it.

## Known Stubs

None. Every test committed by this plan asserts a measured property and runs green.

## Next Phase Readiness

Ready. What downstream plans can now rely on:

- **23-07** (the resume seam) inherits a battery whose four positive controls have been watched refusing on MPS, so a RED it sees there is attributable to its own change rather than to an untested venue.
- **23-10** (the σ=0 headline run, and DPSGD-06's close) can cite a venue-transfer ledger that is enforced by tests, names its exemption with a measured count, and records a skip count of `0` as a parsed number.
- Any plan asserting a float equality across devices should read the `_global_norm` row first: **fp32 reductions on this machine differ in the last ULP between cpu and mps**, so `torch.equal` across devices is the wrong predicate and a named bound with stated headroom is the right one.

No blockers.

## Self-Check: PASSED

Files claimed modified — both present:

- `tests/test_phase22_fakes.py` — FOUND
- `tests/test_phase23_mps_venue.py` — FOUND

Commits claimed — all resolve in `git log`:

- `3e19510` — FOUND
- `803a19b` — FOUND
- `a553ca2` — FOUND

All 13 watched-RED anchors re-collected individually against HEAD by collection (not by `test_watched_red_node_ids_resolve`, which is structurally blind inside `[...]`): **13 OK, 0 stale**.

---
*Phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio*
*Completed: 2026-08-26*
