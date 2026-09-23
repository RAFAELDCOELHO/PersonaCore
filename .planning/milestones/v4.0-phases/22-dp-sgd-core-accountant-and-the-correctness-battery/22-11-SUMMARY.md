---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
plan: 11
subsystem: privacy
tags: [differential-privacy, dp-sgd, positive-controls, mutation-probes, ast-guards, phase-sign-off]

# Dependency graph
requires:
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-04/22-06's src/personacore/privacy/dpsgd.py — the mechanism all four fakes are applied to, and D-16's four runtime invariants"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-01/22-04/22-06/22-09's tests/test_phase22_dpsgd_ast.py — the text-taking guards and the _DPSGD_PATH repointing pattern the AST halves run through"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-06's measurement that the sigma-of-zero identity CANNOT detect FAKE 3, and that D-02's inherited-divide fake is invisible at accum = 1"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-10's dp_n8/dp_n64 arms at grad_accum_steps = n_facts (8 / 64), which is what keeps the accum > 1 detection regime reachable in production"
provides:
  - "tests/test_phase22_fakes.py — V-18…V-21, the four committed RED-then-GREEN probes plus the ledger locks; 11 collected"
  - "tests/test_phase22_dpsgd_ast.py::_assert_noise_precedes_divide — FAKE 3's STRUCTURAL detector, the only one that bites at sigma = 0 and at accum = 1"
  - "the DPSGD-04 evidence ledger below: four fakes applied to the REAL committed module, nine distinct RED signatures captured verbatim, four byte-identical restores"
  - "the measured correction that `make lint` DOES exit 0 on this box — four prior summaries recorded the opposite"
affects: [23 the frontier sweep and DPSGD-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A fake probe that runs the LIVE guard TEST FUNCTION over mutated bytes by monkeypatching the guard module's own _DPSGD_PATH — stronger than re-calling the helper, because it also proves the assertion CI runs is the assertion that reddens"
    - "A consequence measured as the ADD/REMOVE-ONE SENSITIVITY (the quantity the accountant is told), not as an accumulator norm — the accumulator legitimately reaches N*C, so its norm cannot discriminate"
    - "A guard's blind spots enumerated as a committed TABLE with expected-to-see booleans, so a cell that unexpectedly starts detecting reddens instead of silently widening the claim"
    - "Counting DISTINCT RED signatures rather than RED tests: two fakes tripping one guard with one message is a coverage gap to name, not a second win"

key-files:
  created:
    - tests/test_phase22_fakes.py
  modified:
    - tests/test_phase22_dpsgd_ast.py

key-decisions:
  - "D-17's FAKE 3 row was used in its CORRECTED form and RE-MEASURED here directly: under the real-module FAKE 3 mutation, every sigma-of-zero identity in the suite stayed GREEN. The row is false for a structural reason, not a fixture reason"
  - "A SECOND blind spot was measured that no prior plan had named for FAKE 3: at accum = 1 the divide is a no-op at EVERY sigma, so the runtime differential is blind there too. Three of the four (sigma, N) cells are blind; only (sigma>0, N>1) detects"
  - "The plan's `_assert_noise_precedes_divide(..., method=\"finalize\")` is UNSATISFIABLE — `finalize` contains neither a torch.normal call nor any division. The guard LOCATES the divide-bearing method (`_noised_private`) instead of taking a name"
  - "The plan's stated FAKE 1 consequence ('the accumulated norm after two records exceeds C') does NOT discriminate: the honest accumulator holds the SUM and legitimately reaches N*C. The neighbouring-lot sensitivity is asserted instead — 1.000000*C honest against 1.734481*C faked"
  - "The four real-source mutations were driven by a script with a `finally: git checkout --` and a double restore proof (work-tree sha256 AND `git rev-parse HEAD:<path>` blob), rather than by bare Edit calls. A crashed Edit flow leaves a fake applied on a privacy mechanism"
  - "requirements.mark-complete WAS called: DPSGD-01, DPSGD-03 and DPSGD-04 are closed. DPSGD-06 explicitly owns 'the first executed run', so DPSGD-01's text (mechanism + additive seam) is fully evidenced without one"

patterns-established:
  - "Watched deliberate-RED over the real module, driven by a finally-guarded script with a blob-hash restore proof"
  - "Distinct-RED-signature accounting, with near-collisions named in the register"

requirements-completed: [DPSGD-01, DPSGD-03, DPSGD-04]
requirements-contributed: []

# Metrics
duration: 75min
completed: 2026-08-26
---

# Phase 22 Plan 11: The Four Positive Controls, Watched Summary

**All four silent-non-privacy fakes were applied to the REAL committed `dpsgd.py`, each watched reddening a named test with its message captured verbatim, each restored to a byte-identical blob (`sha256 140f5108…`, `blob f0e267c2`) — nine detectors, nine distinct RED signatures, and the two guards D-17 credits that CANNOT fire are published rather than smoothed.**

## Performance

- **Duration:** ~75 min
- **Tasks:** 3
- **Files:** 1 created, 1 modified
- **Full suite:** 1268 → **1278 passed, 3 skipped** (2 of the 3 skips lift to passes once this file is on disk)

## Accomplishments

- **Four fakes, four watched REDs over the real module, four byte-identical restores.** Every mutation's pre- and post-restore `sha256` and `git rev-parse HEAD:<path>` blob hash are recorded per fake in the ledger below, and every RED/GREEN verdict is read from **pytest's own summary line**, never from `$?` after a pipe (T-22-56).
- **Nine detectors, nine DISTINCT assertion messages.** No two fakes are caught by the same guard with the same message. The one near-collision — `test_dpsgd_step_reaches_no_forbidden_call` catching FAKE 1 and FAKE 4 — fires at two different parametrizations reporting two different offender dicts, and is named in the register instead of counted twice.
- **D-17's FAKE 3 row was re-measured FALSE directly, not inherited.** Under the real-module `divide → noise` mutation, `test_sum_then_noise_then_divide` and all three `test_sigma_zero_non_binding_clip_reproduces_the_default_path` parametrizations stayed **GREEN**. The sigma-of-zero identity is structurally incapable of seeing where the noise was added.
- **A SECOND FAKE-3 blind spot was found that no prior plan had named:** at `accum = 1` the divide is a no-op at **every** sigma, so the magnitude differential is blind there too. Three of the four `(sigma, N)` cells are blind; only `(sigma > 0, N > 1)` detects. The `_assert_noise_precedes_divide` statement-order guard added here covers all four.
- **The plan's own FAKE 1 consequence was measured non-discriminating and replaced with one that is.** "The accumulated norm exceeds C" is true of the HONEST mechanism too (the accumulator holds the SUM). The add/remove-one sensitivity — the quantity D-18 says the accountant is told — separates them: `1.000000 * C` honest against `1.734481 * C` with the drain dropped.
- **`make lint` DOES exit 0 on this box.** Measured: exit `0`. Four prior Phase-22 summaries (22-04, 22-06, 22-09, 22-10) and this session's own prompt record it as broken; what is broken is **`make test`** (exit `2`). Correction published below.
- `scripts/mitigation_gate.py`, `scripts/mitigation_unit.py`, `scripts/mitigation_accountant.py` and `pyproject.toml` are **byte-unchanged**; `git diff --exit-code -- src/ scripts/` exits **0**; `git status --porcelain results/` is **empty**.

## Task Commits

1. **Task 1: the four committed RED-then-GREEN probes** — `be3f1a0` (test)
2. **Task 2: FAKE 1 and FAKE 3 watched over the real source; the node-id lock** — `a0f01f4` (test)
3. **Task 3: FAKE 2 and FAKE 4 watched; the distinct-signature register** — `3008a48` (test)

## Files Created/Modified

- `tests/test_phase22_fakes.py` (new, **849 lines**, **11 collected**) — the four probes with their subclass fakes, the `_run_live_guard` harness that repoints `_DPSGD_PATH`, the `_mutate` applied-assertion helper, `_FAKE3_DIFFERENTIAL_SEES`'s four-cell coverage table, `_WATCHED_RED_NODE_IDS` and the three ledger locks.
- `tests/test_phase22_dpsgd_ast.py` (+126 / −0, 19 → **20 collected**) — `_NOISE_CALL`, `_called_names`, `_divides_by`, `_assert_noise_precedes_divide` (ONE definition, imported by the probe file) and its live green test `test_dpsgd_draws_the_noise_before_it_divides`.

---

# DPSGD-04 Evidence Ledger

Four fakes, applied to `src/personacore/privacy/dpsgd.py` **on disk**, one at a time. Common to all four:

| | |
|---|---|
| pre-mutation `sha256` | `140f51082ab188a06de5426e8e1827c85423f19c43e45d45bca90515a96013eb` |
| pre-mutation blob (`git rev-parse HEAD:src/personacore/privacy/dpsgd.py`) | `f0e267c294b99f9be996b3dc15dc808a87e1bd52` |
| command | `.venv/bin/python -m pytest tests/test_phase22_dpsgd.py tests/test_phase22_dpsgd_ast.py tests/test_phase22_fakes.py tests/test_phase22_wiring.py -q --no-header` |
| verdict source | pytest's **own summary line**, parsed out of captured stdout — never `$?` after a pipe |
| restore | `git checkout -- src/personacore/privacy/dpsgd.py` in a `finally`, then `sha256` **and** blob hash re-compared, then `git diff --exit-code` |

**Baseline (unmutated) for this command set: `78 passed, 2 skipped`.**

---

### FAKE 1 — clip the AVERAGED gradient (drop the per-micro-step drain)

**Mutation applied:**

```diff
@@ -476,9 +476,6 @@ class DPSGD:
             buf.add_(contribution)
         self._records += 1
 
-        for p in self._params:
-            p.grad = None  # D-01's per-micro-step drain -- load-bearing, not tidiness.
-        self._drained = True
 
     def _draw_noise(self):
```

**pytest summary line:** `12 failed, 65 passed, 2 skipped in 20.21s` — **RED**, failed count read from that line: `12`.

**Failing node ids (12):**

```
tests/test_phase22_dpsgd.py::test_drain_invariant_fires
tests/test_phase22_dpsgd.py::test_sum_then_noise_then_divide[2]
tests/test_phase22_dpsgd.py::test_side_channel_negative_control
tests/test_phase22_dpsgd.py::test_sigma_zero_non_binding_clip_reproduces_the_default_path[1]
tests/test_phase22_dpsgd.py::test_sigma_zero_non_binding_clip_reproduces_the_default_path[4]
tests/test_phase22_dpsgd.py::test_sigma_zero_non_binding_clip_reproduces_the_default_path[3]
tests/test_phase22_dpsgd.py::test_noise_is_scaled_by_the_lot_size_because_the_divide_comes_LAST[4]
tests/test_phase22_dpsgd_ast.py::test_dpsgd_step_reaches_no_forbidden_call[absorb_record]
tests/test_phase22_fakes.py::test_fake_averaged_gradient
tests/test_phase22_fakes.py::test_fake_noise_after_averaging[0.0-4]
tests/test_phase22_fakes.py::test_fake_noise_after_averaging[1.0-4]
tests/test_phase22_wiring.py::test_end_to_end_writes_no_scored_artifact
```

**Verbatim assertion messages — the two ASSIGNED detectors (D-05 axis 4, structural; D-16 invariant 1, runtime):**

```
E       AssertionError: functions reachable from DPSGD.absorb_record reach {}, not exactly
        {'absorb_record': ['.grad=']}. Between the noise write and optimizer.step() there may be
        no .backward(), no clip/normalize and no re-seed, and the ONLY .grad writes in the whole
        mechanism are D-01's per-micro-step drain and D-01's single combining write
E       assert {} == {'absorb_record': ['.grad=']}
```

```
E       RuntimeError: [dp-invariant:drain] the previous absorb_record did not drain .grad, so this
        record's clip would see a RUNNING SUM rather than one record. backward() ACCUMULATES:
        without the per-micro-step drain, record i's clip sees records 1..i summed and the true
        per-record sensitivity silently becomes N*C while the accountant is told C. Nothing else
        in the system would notice -- the run converges fine.
```

**Restore:** `sha256 140f5108… equal: True` · `blob f0e267c2… equal: True` · `git diff --exit-code`: exit **0**.
**Re-GREEN:** `78 passed, 2 skipped in 21.38s`, failed count `0`.

---

### FAKE 2 — noise scaled to the WRONG SENSITIVITY (a second clip constant)

**Mutation applied:**

```diff
@@ -294,6 +294,7 @@ class DPSGD:
         self.C = float(clip_norm)  # SINGLE source of truth -- the clip AND the noise read this.
+        self._c2 = 2.0 * self.C
@@ -448,7 +449,7 @@ class DPSGD:
-            coef = self.C / norm
+            coef = self._c2 / norm
```

**pytest summary line:** `5 failed, 73 passed, 2 skipped in 20.18s` — **RED**, failed count `5`.

**Failing node ids (5):**

```
tests/test_phase22_dpsgd.py::test_sensitivity_invariant_fires
tests/test_phase22_dpsgd.py::test_side_channel_negative_control
tests/test_phase22_dpsgd_ast.py::test_dpsgd_has_exactly_one_clip_constant
tests/test_phase22_fakes.py::test_fake_averaged_gradient
tests/test_phase22_fakes.py::test_fake_wrong_sensitivity
```

**BOTH assigned detectors fired, as the plan predicted.** Verbatim:

```
E       AssertionError: DPSGD.absorb_record treats ['C', '_c2'] as clip constants, not exactly
        {'C'}. D-17 makes the wrong-sensitivity fake impossible by giving the mechanism ONE clip
        constant captured in __init__ and read everywhere; a second one is FAKE 2, and it is the
        insertion that lets the code clip to one bound while the accountant is told another
E       assert {'C', '_c2'} == {'C'}
```

```
E       RuntimeError: [dp-invariant:sensitivity] the CLIPPED global norm is 0.0020000000949949026,
        above C * (1 + 1e-06) = 0.001000001. The noise is scaled to a sensitivity of exactly C, so
        a record contributing more than C means the noise is scaled to the WRONG SENSITIVITY and
        the published epsilon is optimistic by the ratio. This reads the SAME self.C the clip and
        the noise line read.
```

`0.0020000000949949026` against `C = 0.001` is **exactly 2C** — the fake's own bound, quoted back by the guard.

**Restore:** `sha256 140f5108… equal: True` · `blob f0e267c2… equal: True` · `git diff --exit-code`: exit **0**.
**Re-GREEN:** `78 passed, 2 skipped in 21.21s`, failed count `0`.

---

### FAKE 3 — noise added AFTER averaging (`divide → noise`)

**Mutation applied** — the `/N` hoisted ahead of the draw inside `_noised_private`, which is where both the draw and the divide actually live (`finalize` delegates to it):

```diff
@@ -514,6 +514,7 @@ class DPSGD:
         """
+        averaged = [buf / accum for buf in self._accum]
         pre = self._g.get_state()
@@ -536,7 +537,7 @@ class DPSGD:
         self._prev_gen_state = post
-        return [(buf + drawn) / accum for buf, drawn in zip(self._accum, noise)]
+        return [avg + drawn for avg, drawn in zip(averaged, noise)]
```

**pytest summary line:** `6 failed, 71 passed, 2 skipped in 22.82s` — **RED**, failed count `6`.

**Failing node ids (6):**

```
tests/test_phase22_dpsgd.py::test_noise_is_scaled_by_the_lot_size_because_the_divide_comes_LAST[4]
tests/test_phase22_dpsgd_ast.py::test_dpsgd_draws_the_noise_before_it_divides
tests/test_phase22_fakes.py::test_fake_noise_after_averaging[0.0-1]
tests/test_phase22_fakes.py::test_fake_noise_after_averaging[0.0-4]
tests/test_phase22_fakes.py::test_fake_noise_after_averaging[1.0-1]
tests/test_phase22_fakes.py::test_fake_noise_after_averaging[1.0-4]
```

**THE FINDING, and it is the reason this plan exists.** `test_sum_then_noise_then_divide` and all three parametrizations of `test_sigma_zero_non_binding_clip_reproduces_the_default_path` — **D-06's sigma-of-zero identity, the detector D-17's table assigns to this fake — are NOT in that list. They stayed GREEN.** 22-06 measured this and 22-09 carried the correction forward; this is the third independent measurement and the first against the real committed module with the shipped guard set. The reason is structural: at `sigma = 0` the drawn values are exactly zero, so `(S + 0)/N` and `(S/N) + 0` are the same bytes.

**Verbatim, the two detectors that DO fire:**

```
E       AssertionError: the released noise has std 1.0006904602050781 at N = 4, a ratio of
        4.002762 to the expected sigma*C/N = 0.25. D-02 puts the /N LAST: the noise is added to
        the SUM (one record moves the sum by at most C — the textbook sensitivity argument) and
        only then divided. A ratio near 4 means the divide moved AHEAD of the draw, so the
        released noise is N times too large for the sensitivity the accountant was told
E       assert 3.0027618408203125 <= 0.01
```

```
E       AssertionError: DPSGD._noised_private draws the noise at statement 4 and divides by
        'accum' at statement 1. D-02 puts the /N LAST: the noise is added to the SUM, because one
        record moves the SUM by at most C and that is the sensitivity the accountant is told.
        Dividing first releases noise N times too large for that sensitivity — FAKE 3, and it is
        INVISIBLE at sigma = 0 (the draw is exact zeros) and at N = 1 (the divide is a no-op),
        which is why the order is pinned structurally as well as by magnitude
E       assert 4 < 1
```

**Restore:** `sha256 140f5108… equal: True` · `blob f0e267c2… equal: True` · `git diff --exit-code`: exit **0**.
**Re-GREEN:** `78 passed, 2 skipped in 21.36s`, failed count `0`.

---

### FAKE 4 — RNG REUSED across steps (an in-step `manual_seed`)

**Mutation applied:**

```diff
@@ -601,6 +601,7 @@ class DPSGD:
     def finalize(self, accum):
         """..."""
+        self._g.manual_seed(0)
         lot = int(accum)
```

**pytest summary line:** `10 failed, 68 passed, 2 skipped in 20.96s` — **RED**, failed count `10`.

**Failing node ids (10):**

```
tests/test_phase22_dpsgd.py::test_generator_advances_and_is_never_reseeded
tests/test_phase22_dpsgd.py::test_legacy_clip_is_unreachable_on_the_dp_path
tests/test_phase22_dpsgd.py::test_sigma_zero_non_binding_clip_reproduces_the_default_path[1]
tests/test_phase22_dpsgd.py::test_sigma_zero_non_binding_clip_reproduces_the_default_path[4]
tests/test_phase22_dpsgd.py::test_sigma_zero_non_binding_clip_reproduces_the_default_path[3]
tests/test_phase22_dpsgd_ast.py::test_dpsgd_step_reaches_no_forbidden_call[finalize]
tests/test_phase22_dpsgd_ast.py::test_dpsgd_never_reseeds_its_generator
tests/test_phase22_fakes.py::test_fake_noise_after_averaging[1.0-1]
tests/test_phase22_fakes.py::test_fake_rng_reuse
tests/test_phase22_wiring.py::test_end_to_end_writes_no_scored_artifact
```

**BOTH AST guards AND the runtime generator-state check fired.** Verbatim:

```
E       AssertionError: DPSGD's generator seed/state call sites are {'__init__': ['manual_seed'],
        'load_noise_rng_state': ['set_state'], 'finalize': ['manual_seed']}, not exactly
        {'__init__': ['manual_seed'], 'load_noise_rng_state': ['set_state']}. Anything else is
        FAKE 4's positive insertion — the runtime generator-continuity invariant catches it on
        today's inputs, and this catches the FUTURE edit that a runtime check cannot see
```

```
E       AssertionError: functions reachable from DPSGD.finalize reach {'finalize': ['manual_seed'],
        '_write_once': ['.grad=']}, not exactly {'_write_once': ['.grad=']}. Between the noise
        write and optimizer.step() there may be no .backward(), no clip/normalize and no re-seed,
        and the ONLY .grad writes in the whole mechanism are D-01's per-micro-step drain and
        D-01's single combining write
```

```
E       RuntimeError: [dp-invariant:generator] this step's PRE-draw generator state is not the
        previous step's POST-draw state, so something touched the generator between steps. That is
        FAKE 4 -- RNG REUSED ACROSS STEPS: an in-step manual_seed makes every step draw the SAME
        noise vector, the noise stops being independent across compositions, and the T-fold
        composition the accountant charges for is not the mechanism that ran. CONTINUITY is
        asserted rather than 'the pre-state differs from last step's pre-state', because the
        latter is silent on a re-seed to a DIFFERENT fixed value and on any foreign consumer
        draining the same stream.
```

**Restore:** `sha256 140f5108… equal: True` · `blob f0e267c2… equal: True` · `git diff --exit-code`: exit **0**.
**Re-GREEN:** `78 passed, 2 skipped in 21.30s`, failed count `0`.

---

## Distinct RED Signature Accounting

**Nine detectors, nine distinct assertion messages. No two fakes share a signature.**

| Fake | Detector | Kind | Distinct? |
|---|---|---|---|
| 1 | `test_dpsgd_step_reaches_no_forbidden_call[absorb_record]` | AST | ✅ `reach {}, not exactly {'absorb_record': ['.grad=']}` |
| 1 | `[dp-invariant:drain]` (`test_drain_invariant_fires`) | runtime | ✅ |
| 2 | `test_dpsgd_has_exactly_one_clip_constant` | AST | ✅ `treats ['C', '_c2'] as clip constants` |
| 2 | `[dp-invariant:sensitivity]` (`test_sensitivity_invariant_fires`) | runtime | ✅ |
| 3 | `test_dpsgd_draws_the_noise_before_it_divides` | AST (new) | ✅ `noise at statement 4 … divides at statement 1` |
| 3 | `…_divide_comes_LAST[4]` | runtime | ✅ `std 1.0006904602050781 … ratio 4.002762` |
| 4 | `test_dpsgd_never_reseeds_its_generator` | AST | ✅ `'finalize': ['manual_seed']` in the site dict |
| 4 | `test_dpsgd_step_reaches_no_forbidden_call[finalize]` | AST | ✅ `reach {'finalize': ['manual_seed'], …}` |
| 4 | `[dp-invariant:generator]` | runtime | ✅ |

**The one near-collision, named rather than counted twice.** `test_dpsgd_step_reaches_no_forbidden_call` is the assigned detector for BOTH FAKE 1 and FAKE 4. It is not a shared signature: the two hits are different **node ids** (`[absorb_record]` vs `[finalize]`) reporting different **offender dicts** (`{}` where the drain's `.grad=` write vanished, against `{'finalize': ['manual_seed'], …}` where the re-seed appeared). One guard function, two entries, two messages. `test_every_fake_has_at_least_two_independent_detectors` pins the 9-against-9 arithmetic so a future collapse to a shared signature reddens.

**Collateral REDs are NOT counted as detection.** `test_side_channel_negative_control` (FAKE 1, 2), `test_sigma_zero_non_binding_clip_reproduces_the_default_path` (FAKE 1, 4) and `test_end_to_end_writes_no_scored_artifact` (FAKE 1, 4) redden under more than one fake. They are downstream consequences, not assigned detectors, and none of them is the reason any fake is claimed caught. **The one that matters is the σ=0 identity's ABSENCE from FAKE 3's list while appearing in FAKE 1's and FAKE 4's** — the same guard is capable against two fakes and structurally incapable against the third, which is precisely D-17's false row.

**REDs in `tests/test_phase22_fakes.py` itself are the probe file's own controls firing correctly** over a mutated module: `_mutate`'s applied-assertion (`the mutation target appears 0 times, not once` under FAKE 2, because `coef = self.C / norm` no longer exists), and `_assert_noise_precedes_divide`'s GREEN control over the real bytes (under FAKE 3). Recorded so no reader mistakes them for detections.

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `_assert_noise_precedes_divide(..., method="finalize")` is unsatisfiable against the shipped module**

- **Found during:** Task 1
- **Issue:** The plan specifies *"asserting that in `finalize`'s body the statement index of the `torch.normal` call is strictly less than the statement index of the `BinOp(Div)` whose right operand is `accum`."* Measured against `dpsgd.py`: `finalize`'s body contains **neither**. It is four statements — `lot = int(accum)`, two refusals, and `self._write_once(self._noised_private(lot))`. The draw lives in `_draw_noise` and the divide in `_noised_private`. A guard scoped to `finalize` finds zero of each and passes over nothing.
- **Fix:** The guard takes no method name. It LOCATES the divide-bearing method — the one with a parameter named `accum` **and** a `BinOp(Div)` whose right operand is a `Name` load of it — asserts there is exactly ONE (`_noised_private`), and derives the noise-producer name set from the class rather than hard-coding it (`{"normal"}` plus every method whose body calls it, which resolves `self._draw_noise()` in one hop). Both halves carry meta-guards: the producer set must exceed `{"normal"}` alone, and the located method count must be exactly 1.
- **Verification:** GREEN on the real bytes at `noise_index = 3 < divide_index = 7`; RED on the swapped-order string at `4 < 1`; RED on the real work-tree module during FAKE 3's watched pass.
- **Committed in:** `be3f1a0`

**2. [Rule 1 - Bug] The plan's stated FAKE 1 consequence does not discriminate the fake from the honest mechanism**

- **Found during:** Task 1
- **Issue:** The plan says *"with the drain dropped, the accumulated norm after two records exceeds `C` — i.e. true per-record sensitivity became `N*C`"*. The honest accumulator holds the **SUM** of clipped per-record gradients (D-02), so after N records its norm legitimately reaches `N*C`. Measured on this fixture with a binding clip, the honest accumulator's norm after two records is above `C` too. The assertion as written is green on correct code, which makes it a consequence claim that proves nothing.
- **Fix:** The consequence is measured as the **add/remove-one sensitivity** — D-18's own quantity, the one the accountant is told: `‖sum({r1, r2}) − sum({r2})‖ / C`. Honest: `1.000000` (the difference is exactly `clip(g1)`, whose norm is `C`). Drain dropped: `1.734481`. The second figure has a closed form — with `g1`, `g2` independent, equal-norm and over `C`, the difference is `clip(g1) + clip(g1+g2) − clip(g2)` whose norm is `C·√3 = 1.7320508 C`; the measured `1.734481` is that value plus the fixture's departure from exact orthogonality, asserted in a `±0.02` band with the honest ratio as its control.
- **Committed in:** `be3f1a0`

**3. [Rule 2 - Missing critical functionality] FAKE 3 has a SECOND blind spot no prior plan had named**

- **Found during:** Task 1
- **Issue:** 22-06 and 22-09 recorded FAKE 3's `sigma = 0` blind spot. Neither examined the lot size. Measured over the full `(sigma, N) ∈ {0, 1} × {1, 4}` grid: `(1.0, 1)` is **also** blind — `x / 1` is exact, so the divide's position is unobservable at `N = 1` at every sigma. **Three of the four cells are blind; only `(sigma > 0, N > 1)` detects.** A downstream plan trusting "the magnitude guard covers FAKE 3" without the lot-size condition would be trusting a detector that is silent at `TrainConfig.grad_accum_steps`'s default of `1`.
- **Fix:** `_FAKE3_DIFFERENTIAL_SEES` ships as a committed four-cell table with an expected-to-see boolean per cell, and `test_fake_noise_after_averaging` is parametrized over it: the three blind cells assert `torch.equal` (with a message saying to re-measure rather than widen if a cell ever starts detecting), and the detecting cell asserts the `3.999986` std ratio. Every cell additionally runs the structural detector, which is blind in none of them.
- **Committed in:** `be3f1a0`

**4. [Rule 3 - Blocking] The plan's mutation-then-restore flow has no failure path**

- **Found during:** Task 2
- **Issue:** The plan directs *"Apply the minimal mutation with `Edit`"* and restore afterwards. A crash, a timeout or an early return between those two steps leaves a **deliberately broken privacy mechanism** applied to the work tree with nothing to notice. This plan's own `<restoration_discipline>` says a fake must never be left applied.
- **Fix:** The four real-source mutations were driven by a script whose restore is in a `finally` and whose proof is doubled — the work-tree `sha256` **and** `git rev-parse HEAD:<path>`'s blob hash, both re-compared, plus `git diff --exit-code`, with an `assert` on all three before the re-GREEN run. Verified after every one of the four: `140f5108…` / `f0e267c2…` / exit `0`.
- **Committed in:** n/a (driver is a scratch artifact; its outputs are this ledger)

**5. [Rule 1 - Bug] Four prior summaries record `make lint` as broken on this box. It is not.**

- **Found during:** Task 3 sign-off
- **Issue:** 22-04 deviation 5, 22-06 deviation 6, 22-09 and 22-10 deviation 7 all state *"`make test` / `make lint` still do not resolve the venv"* and that *"`make lint` cannot exit 0 on this box"*. This session's own prompt repeats it. **Measured: `make lint` exits `0`.** What is broken is `make test`, which exits `2`. The claim conflated the two targets and has been carried forward four times unmeasured — the exact defect class this phase exists to catch, arriving in the phase's own records.
- **Fix:** Published here rather than re-transcribed. The precise statement: **`make lint` exits 0 but runs a DIFFERENT instrument** — pyenv's `ruff 0.16.4` over **229 files** — than `.venv/bin/ruff 0.15.16` over **203 files**. Both pass. So "`make lint` is green" is true and "`make lint` is the same check as `.venv/bin/ruff`" is false; the venv form remains the one to quote, for the same reason the venv `pytest` is.
- **Verification:** `make lint; echo $?` → `0`. `make test; echo $?` → `2`. `which ruff` → `~/.pyenv/shims/ruff`, `ruff --version` → `0.16.4`; `.venv/bin/ruff --version` → `0.15.16`.
- **Committed in:** n/a

**6. [Rule 2 - Missing critical functionality] A ledger's cited node ids can go stale silently**

- **Found during:** Task 2
- **Issue:** The plan requires the SUMMARY's ledger to name the failing test id per fake. Nothing would notice a later rename — the ledger is prose in a markdown file, and this repository has measured seven stale anchors across 22-02/22-03 alone. 22-09 recorded the mirror image: the frozen pin's by-symbol citation resolves only because a test was deliberately named to match it.
- **Fix:** `_WATCHED_RED_NODE_IDS` records the nine detectors as data and `test_watched_red_node_ids_resolve` asserts each resolves to a callable in its module and that its parametrization matches the cited id. Plus `test_fakes_ledger_is_recorded` (a heading per fake, and the words "RED" and "restored") and `test_fakes_ledger_names_its_blind_spots` (the two blind spots and `rng["mps"]` by literal). All three skip gracefully only while the SUMMARY does not exist.
- **Committed in:** `a0f01f4`, `3008a48`

**7. [Rule 1 - Bug] `gsd-sdk` mutation-handler defects, hand-repaired before commit** — see *Tooling Corruption Encountered*.

### Deliberate departures from the plan text

- **The RED capture runs WITHOUT `-x`.** The plan's command carries `-x -q`, which stops at the first failure and would have recorded one node id per fake instead of the full set. Twelve, five, six and ten node ids were captured respectively; the sharing analysis above is only possible because none was truncated away.
- **`tests/test_phase22_wiring.py` was added to the probe target set.** The plan names three files. The wiring file carries V-23's end-to-end production run, and it is the only place a fake can be observed reaching `main()`; it reddened under FAKE 1 and FAKE 4.
- **`_assert_noise_precedes_divide` is defined in `tests/test_phase22_dpsgd_ast.py`, not in the probe file.** The plan sanctions either ("one definition either way"). The AST module is where every other text-taking guard lives, so the live green test and the RED probe run the same function through the same import, and `grep -rn "def _assert_noise_precedes_divide" tests/` returns **1**.
- **The AST halves run the LIVE TEST FUNCTIONS, not the helpers.** The plan says to feed mutated strings to `_assert_single_clip_constant` / `_assert_no_forbidden_between_noise_and_step`. Repointing `ast_guards._DPSGD_PATH` at a temp copy and calling `test_dpsgd_has_exactly_one_clip_constant()` itself is strictly stronger: it proves the assertion **CI runs** is the assertion that reddens, not merely that the helper underneath it does. 22-04 established the pattern.
- **`_assert_no_forbidden_between_noise_and_step` is NOT used at `entry="finalize"` for FAKE 4.** That wrapper asserts `offenders == {}`, and 22-04 measured `{'_write_once': ['.grad=']}` there on correct code — it is RED unmutated, so a probe using it would be unattributable. The hard-equality allowlist test (`test_dpsgd_step_reaches_no_forbidden_call[finalize]`) is used instead, which is the form that actually ships.
- **The probe file collects 11, against the plan's "at least 8 passed".** 9 pass and 2 skip while this SUMMARY is unwritten; all 11 pass once it is on disk. Recorded so the count is not mistaken for scope creep.
- **Line anchors inside new code are cited by SYMBOL**, continuing 22-02…22-10's habit.

---

**Total deviations:** 7 auto-fixed (1 unsatisfiable guard scoping, 1 non-discriminating consequence, 1 unnamed blind spot, 1 unsafe restore flow, 1 four-times-inherited false claim about the tooling, 1 missing ledger lock, 1 tooling corruption), 7 deliberate departures.
**Impact on plan:** every correction makes a detector bite where the specified version could not, or narrows a claim to what was measured. None weakens a guard. **No source file was left changed:** `git diff --exit-code -- src/ scripts/` exits 0 and both frozen pins plus `pyproject.toml` are byte-unchanged.

---

## Phase 22 Sign-Off

### 1. Full suite

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | **1278 passed, 3 skipped**, 83 warnings, 219.41 s |
| baseline entering this plan | 1268 passed, 1 skipped |
| delta | **+10 passed, +2 skipped**, zero regressions |
| the 3 skips | `test_fakes_ledger_is_recorded` and `test_fakes_ledger_names_its_blind_spots` (both lift to passes with this file on disk) + `tests/test_train_loop.py:81` fp16 AMP smoke, which needs CUDA |

### 2. Lint

| Check | Result |
|---|---|
| `.venv/bin/ruff check . && .venv/bin/ruff format --check .` | clean, **203 files** formatted (ruff 0.15.16) |
| `make lint` | exit **0** — clean, 229 files (pyenv ruff 0.16.4). See deviation 5: four prior summaries record this as impossible |
| `make test` | exit **2** — genuinely broken, tenth confirmation. Bare `pytest` resolves to a pyenv 3.12.13 with no torch |

### 3. Frozen pins and the dependency manifest (V-24, RPT-03)

`git diff --exit-code -- scripts/mitigation_gate.py scripts/mitigation_unit.py scripts/mitigation_accountant.py pyproject.toml` → exit **0**, byte-unchanged. Nothing was installed.

### 4. `results/` (D-08)

`git status --porcelain results/` → **empty**. Phase 22 wrote no scored artifact.

### 5. Every V-ID has a green automated command

All 25 rows of `22-VALIDATION.md` run inside the green full suite. Each named node resolves — verified by locating `def <name>` for all 18 explicitly-named test functions (V-01…V-09, V-12, V-14, V-15, V-18…V-21, V-22, V-25); V-10/V-11/V-13/V-16/V-17/V-23/V-24 are file- or runtime-scoped rows and their files are green.

**The four positive controls (V-18…V-21) are recorded as OBSERVED RED BEFORE GREEN with the RED output recorded** — the ledger above, four sections, four verbatim captures, four byte-identical restores. This is the explicit phase gate before `/gsd:verify-work`, and it is the row `22-VALIDATION.md`'s sign-off left open.

### 6. What is NOT covered — named, because a sign-off that lists only green is not a sign-off

1. **FAKE 3 is invisible at `sigma = 0`.** `torch.normal(std=0.0)` returns exact zeros, so `(S + 0)/N` and `(S/N) + 0` are the same bytes at every lot size. D-17's table assigns FAKE 3 to exactly this detector; **the row is false** and was re-measured false here against the real module. What covers the fake at `sigma = 0` is the statement-order structural check.
2. **FAKE 3 is invisible at `accum = 1`.** `x / 1` is exact, so the divide's position is unobservable at every sigma. Found in this plan; not named by any prior one. `TrainConfig.grad_accum_steps` defaults to `1`, and 22-10's `dp_n8` / `dp_n64` arms run at `8` / `64` — which is what keeps the detecting regime reachable in production. **A future one-fact arm re-opens this.**
3. **The runtime `C*(1+tol)` sensitivity check is ONE-SIDED.** It refuses a clipped norm ABOVE `C*(1+tol)` — the dangerous direction, clip to `2C` while telling the accountant `C`. It is structurally blind to a second constant SMALLER than `C`: clipping to `C/2` is wasteful rather than unsafe and `C/2 <= C*(1+tol)` holds. Measured, not argued — `_ClipsToAHalfConstant` completes with **no refusal at all**. The AST guard catches both directions because it never looks at a number.
4. **`rng["mps"]` is required-but-UNEXERCISED in CPU-only CI.** D-14 records this on purpose: DPSGD-05 names the slot literally, but the DP path fires the separately-named `dp_noise_rng` slot, because D-07 locked a dedicated generator whose draw does not move the global MPS state. `tests/test_phase22_checkpoint.py::test_mps_rng_slot_round_trips` is `skipif`-gated on `torch.backends.mps.is_available()`. **On this box it RAN** (it is not among the 3 skips); in CI it will skip. Both facts are reported.

---

## Tooling Corruption Encountered

Twentieth consecutive session. Every `gsd-sdk` mutation call used the `--flag` form and was followed by `git diff` on the three planning files, hand-repaired before the metadata commit. This file was written to disk **before** `roadmap.update-plan-progress` ran (the 22-06 workaround). **Two handlers DIVERGED from the ten prior Phase-22 records and the divergence is published rather than transcribed** — the ten prior records are what this session expected, and two of them did not reproduce.

| Handler | Observed | Repair |
|---|---|---|
| `state.advance-plan` | **CORRECT, diverging from 22-01…22-10.** It did NOT revert the Status line; it set `status: verifying`, `Status: Phase complete — ready for verification`, `completed_phases: 2 → 3`, `completed_plans: 38 → 39`, `percent: 22 → 33`. All four verified before acceptance: `ls .planning/phases/*/*-SUMMARY.md \| wc -l` = **39**, `grep -c "^- \[x\] \*\*Phase" ROADMAP.md` = **3**, 3/9 = 33% | none |
| `roadmap.update-plan-progress --phase 22` | **CORRECT, diverging from all ten prior records.** No `In Progress\|  \|` malformation; it wrote `\| 11/11 \| Complete   \| 2026-08-26 \|`, flipped `22-11-PLAN.md`'s checkbox **and** the phase-level `- [x] **Phase 22:** … (completed 2026-08-26)` | none |
| `state.add-decision --summary` | **DEFECT, as recorded.** Prefixed all four entries `- [Phase ?]:` — and with a trailing colon the sibling entries do not carry | prefix rewritten to `- [Phase 22] 22-11:`; `grep -c "Phase ?"` → **0** |
| `requirements.mark-complete --ids …` | **DEFECT, as recorded.** All three checkboxes flipped correctly, all three traceability cells left **empty** where every sibling row carries its evidence. Its own JSON also echoed `"--ids"` back inside an argument array, so the repeated-flag form is parsed loosely even though the result was right | DPSGD-01 / -03 / -04 cells written by hand |
| `state.update-progress` | **DEFECT, as recorded.** `{"updated": false, "reason": "Progress field not found in STATE.md"}` against a frontmatter that plainly has a `progress:` block | harmless; `advance-plan` had already set it |
| `state.record-metric --flag` / `state.record-session --stopped-at` | correct under the `--flag` form | — |

**One repair is mine, not a handler's.** `STATE.md:28` read `Phase: 22 (…) — EXECUTING` while `Status:` two lines below now reads *"Phase complete — ready for verification"*. No handler owns that line; it was corrected to `— COMPLETE (11/11, ready for verification)` so the file does not contradict itself.

Eighth consecutive confirmation that the corruption lives in the **positional** argument path — and the first session in which two of the six handlers behaved correctly under `--flag` where prior sessions recorded them defective. Whether that is a fixed handler or the SUMMARY-before-handler ordering is **not established here**; only the observation is.

## Issues Encountered

- **Three `ruff` `E501` wraps and one `I001` import re-sort** in the new probe file; no assertion text or semantics changed.
- **The `.gitignore` modification present at session start is pre-existing and untouched** — not staged in any commit here.
- **`loop.py`'s `sha256` is `ce6f5d41…`, not 22-06's recorded `ee063ee0…`.** That is 22-10's three-line refusal-message edit, not drift from this plan: `git diff --exit-code -- src/` exits 0 and this plan mutated `loop.py` at no point.

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest tests/test_phase22_fakes.py -q` | **9 passed, 2 skipped** pre-SUMMARY (11 passed after) in 2.44 s |
| `.venv/bin/python -m pytest tests/test_phase22_dpsgd_ast.py -q` | **20 passed** (was 19 at 22-09; this plan adds exactly 1) |
| Watched deliberate-RED, FAKE 1 | 12 failed / 65 passed / 2 skipped, restored `140f5108…`, re-green 78/2 |
| Watched deliberate-RED, FAKE 2 | 5 failed / 73 passed / 2 skipped, restored `140f5108…`, re-green 78/2 |
| Watched deliberate-RED, FAKE 3 | 6 failed / 71 passed / 2 skipped, restored `140f5108…`, re-green 78/2 |
| Watched deliberate-RED, FAKE 4 | 10 failed / 68 passed / 2 skipped, restored `140f5108…`, re-green 78/2 |
| σ=0 identity under FAKE 3 | **GREEN** — D-17's assigned detector re-measured incapable |
| distinct RED signatures | **9 detectors / 9 signatures**, one near-collision named |
| `grep -rn "def _assert_single_clip_constant\|def _assert_no_forbidden_between_noise_and_step\|def _assert_noise_precedes_divide" tests/` | **1 each**, all in `tests/test_phase22_dpsgd_ast.py` |
| `git diff --exit-code -- src/ scripts/` | exit **0** |
| `git diff --exit-code -- scripts/mitigation_{gate,unit,accountant}.py pyproject.toml` | exit **0** |
| `git status --porcelain results/` | **empty** |
| Full suite | **1278 passed, 3 skipped** in 219.41 s |
| `.venv/bin/ruff check . && .venv/bin/ruff format --check .` | clean, **203 files** |

## Known Stubs

None. Every probe applies its fake and observes its refusal on every run; every recorded number carries its measurement; every blind spot is asserted rather than described. What this plan does **not** deliver, stated so no reader infers it: **no real training run exists** and no epsilon has been published. DPSGD-06 ("the σ=0 point is the DP arm's first executed run") is Phase 23's, and the four fakes are proven caught at fixture scale on CPU — which is exactly D-08's boundary and why this phase cost no M3 time.

## Threat Flags

None. This plan adds no network endpoint, no auth path, no schema and no new file-access pattern — the only writes are to `pytest`'s `tmp_path` and the only reads are of two already-read committed source files. Nothing was installed.

Threat register dispositions, each mitigated as planned:

- **T-22-54** (a guard accepted as real without ever being watched fail) — four watched deliberate-RED passes over the REAL module, each with a verbatim capture naming the failing node id and its assertion message. **And one guard was measured NOT to fire**: the σ=0 identity under FAKE 3, published rather than smoothed.
- **T-22-55** (a mutation imperfectly restored) — pre-mutation `sha256` AND `git rev-parse HEAD:<path>` blob recorded, `git checkout --` in a `finally`, both hashes re-compared plus `git diff --exit-code`, asserted before the re-GREEN run. Verified 4/4.
- **T-22-56** (a verdict misread from `$?` after a pipe) — every verdict parsed out of pytest's own summary line in captured stdout; no pipe is involved in any RED/GREEN determination.
- **T-22-57** (a blind spot presented as coverage) — FAKE 3's σ=0 and accum=1 invisibility ship as a committed four-cell table with per-cell assertions, and the one-sided `C*(1+tol)` check has a measured GREEN demonstration (`_ClipsToAHalfConstant`) rather than a docstring claim. Both are named in the sign-off.
- **T-22-58** (a probe reddening because the harness broke) — every probe asserts its unmutated control in the same test, through the identical harness; `_mutate` additionally asserts the replacement APPLIED (`count == 1`).
- **T-22-59** (the ledger silently going missing) — `test_fakes_ledger_is_recorded`, `test_fakes_ledger_names_its_blind_spots` and `test_watched_red_node_ids_resolve`.
- **T-22-SC** (package installs) — accepted; nothing installed, `pyproject.toml` byte-unchanged.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **DPSGD-01, DPSGD-03 and DPSGD-04 are CLOSED here.** DPSGD-02, -05 and -07 were closed by 22-06 and 22-07. **DPSGD-06 is Phase 23's and is the only DPSGD row still open** — its text is *"the σ=0 point is the DP arm's first executed run"*, which no amount of CPU fixture work can satisfy.
- **Phase 23 must not run a DP arm at `n_facts = 1`.** Measured here: FAKE 3 is invisible at `accum = 1`, and 22-06 measured D-02's inherited-divide fake invisible there too. `dp_n8` and `dp_n64` are safe (`accum` 8 / 64); a one-fact arm re-opens two blind spots at once.
- **The interface is `python scripts/teach_persona.py {dp_n8|dp_n64} --sigma=<f> --clip-norm=<f>`**, both required with no default at the CLI *and* at `train_arm`. Phase 22 names no σ and no C anywhere.
- **`_assert_noise_precedes_divide` is available to any future plan that touches the noise/divide order** and takes TEXT, like every other guard in `tests/test_phase22_dpsgd_ast.py`. It locates its own method; do not add a `method=` argument back.
- **The four fake subclasses in `tests/test_phase22_fakes.py` are reusable positive controls.** `_DrainDropped`, `_ClipsToASecondConstant`, `_DivideBeforeNoise` and `_ReseedsInStep` each have an `…Unguarded` sibling or an equivalent, so any new guard can be pointed at a known-bad object before it is trusted.
- **Two claims about this box that four prior summaries got wrong:** `make lint` **works** (exit 0), `make test` **does not** (exit 2). And `.venv/bin/ruff` (0.15.16, 203 files) is not the same instrument as the `ruff` on `PATH` (0.16.4, 229 files) — quote the venv one.
- **`22-VALIDATION.md`'s sign-off checkbox** *"All four positive controls have their RED output recorded, not just their GREEN"* is satisfied by the ledger above and can be checked.

## Self-Check: PASSED

- `tests/test_phase22_fakes.py` — FOUND
- `tests/test_phase22_dpsgd_ast.py` — FOUND
- `.planning/phases/22-dp-sgd-core-accountant-and-the-correctness-battery/22-11-SUMMARY.md` — FOUND
- commit `be3f1a0` — FOUND
- commit `a0f01f4` — FOUND
- commit `3008a48` — FOUND

---
*Phase: 22-dp-sgd-core-accountant-and-the-correctness-battery*
*Completed: 2026-08-26*
