---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
verified: 2026-08-26T03:08:10Z
status: gaps_found
score: 4/5 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: n/a
gaps:
  - truth: "The (eps, delta) accountant is stdlib `math` only, exact under q=1 composition, and agrees with two oracles of DIFFERENT mathematics (SC3 / DPSGD-03)"
    status: partial
    reason: >-
      Two of three conjuncts hold. The third — the two-oracle agreement that IS this
      requirement's entire mechanism of proof — is FALSIFIED in a band the module's own
      docstring names as reachable on this project's frontier. `delta_closed` and
      `delta_quadrature` disagree by up to 12.74% relative in delta, and the second oracle
      itself returns `+inf` and values above 1.0 for a quantity that is a probability. The
      agreement test only sweeps the 12 committed DELTA_FRONTIER rows, none of which is in
      the failing band, so the cross-check is structurally incapable of firing there.
      Measured, not argued — every figure below is from `.venv/bin/python` in this tree.
    artifacts:
      - path: "src/personacore/privacy/accountant.py:186"
        issue: >-
          `second = 0.0 if eb == 0.0 else 0.5 * math.exp(eps + math.log(eb))` treats an
          `erfc` UNDERFLOW as a negligible term. At (eps=775.7866600701457, mu=35.35533905932738)
          — i.e. sigma=0.40 / T=200 / delta=1e-5, the EXACT input the comment three lines above
          cites as reachable — `math.erfc(b)` is 0.0 while `exp(eps)` is ~8.3e336, so the true
          second term is 1.1296969516700846e-06 against a first term of 9.99999999999972e-06.
          Shipped `delta_closed` returns 9.99999999999972e-06; the correct value is
          8.870303048329635e-06 (verified independently three ways: `delta_quadrature` returns
          8.870303048231617e-06, an asymptotic log-erfc expansion agrees to 1.1e-11, and the
          reviewer's 60-dps mpmath agrees). Shipped value is 12.74% HIGH. The function's own
          docstring promises "at least 12 significant digits ... everywhere this function does
          not refuse"; it delivers zero correct digits and does not refuse. 19 of 72 (sigma, T)
          cells on a delta=1e-5 grid show two-oracle disagreement above 1e-9; worst 11.36%.
          Direction is CONSERVATIVE (delta over-stated => epsilon over-stated), so no published
          number is optimistic. Induced epsilon error is 1.218e-03 relative at sigma=0.40/T=200
          (775.786660 shipped vs 774.842722 corrected) and EXACTLY ZERO at sigma >= 0.42.
      - path: "src/personacore/privacy/accountant.py:311-318, 373-391"
        issue: >-
          `delta_quadrature` — the INDEPENDENT ORACLE that DPSGD-03's whole argument rests on —
          returns non-probabilities without refusing. Reproduced: `delta_quadrature(0.000440884929509763,
          75.3129260813192)` returns `inf`; scanning mu in [74.0, 78.0] at eps=1e-4 gives 426
          cells that are `inf` or above 1.0, first `inf` at mu=74.952. Condition 1 bounds a
          SINGLE `math.exp` argument while the Simpson loop sums 20001 terms with weights up to
          4, so it fires ~0.19 too late in z — and its own message already names this case
          ("the separated integral overflows (z < 0)"). Separately, 60 of 4000 sampled cells
          return delta slightly above 1.0 (max 1.000000000000009); there is no upper-bound
          refusal, only `if delta <= 0.0`. `delta_closed` never exceeds 1.0. NOTE: the
          orchestrator's brief reported the `inf` band as unreproducible — it reproduces.
      - path: "src/personacore/privacy/accountant.py:479-611"
        issue: >-
          `epsilon_for(5e-308, 200, 1e-5)` returns `0.0` — PERFECT PRIVACY for essentially zero
          noise. `mu = math.sqrt(steps) / sigma` overflows to `inf` (no finiteness check on the
          QUOTIENT), `_delta_or_below_float64`'s bare `except ValueError` swallows `delta_closed`'s
          GARBAGE-INPUT refusal, and the caller reads `None` as "delta is below float64's range,
          therefore below the target". `_delta_or_below_float64`'s own docstring asserts this is
          impossible ("`mu` is a finite strictly-positive number the caller computed"); nothing
          establishes that premise. Band measured: 320 (T, sigma) cells, widest sigma at T=200 is
          4.450147717014403e-308. This is the PRIVACY-UNDERSTATING direction, and it creates a
          discontinuity at exactly D-12's boundary: sigma=0.0 returns `inf`, the next
          representable float returns `0.0`. Not reachable from `sigma_for` (which refuses first)
          nor from any plausible CLI input, which is why this is scoped below CR-03.
      - path: "tests/test_phase22_accountant.py:364-379"
        issue: >-
          `test_epsilon_for_survives_the_overflow_regime` parametrizes over sigma in {0.40, 0.30}
          — the two points where the dropped term bites — and asserts ONLY `math.isfinite(got)`
          and `got > 700.0`. The test that visits the defect never compares the number to
          anything. `test_two_oracles_agree` cannot see it either: every DELTA_FRONTIER row has
          a healthy `erfc(b)` (max b is 11.5, at the (8.0, 0.5) row).
      - path: ".planning/phases/22-dp-sgd-core-accountant-and-the-correctness-battery/22-03-PLAN.md"
        issue: >-
          The plan's own frontmatter must_have is defeated at the input it names: "RESEARCH F2:
          the closed form uses `exp(eps + log(erfc(b)))`, never `exp(eps) * erfc(b)` — the naive
          form raises OverflowError at eps > 709.78, reachable during a legitimate inverse solve
          at sigma=0.40/T=200". At sigma=0.40/T=200 the `else` branch never executes, because
          `eb == 0.0`. The overflow fix is present in FORM and inert in SUBSTANCE at exactly the
          cited point.
    missing:
      - "A `_log_erfc(x)` helper that stays in log space through the erfc underflow (asymptotic series for large positive x), so `second` is never silently dropped"
      - "A finiteness check on `mu` in `epsilon_for` after `mu = math.sqrt(steps) / sigma`, refusing rather than falling through to `_delta_or_below_float64`"
      - "An upper-bound refusal in `delta_quadrature`: `if not (0.0 < delta <= 1.0): raise ValueError(...)`, plus a condition-1 headroom budget for the Simpson SUM (log(4*n)) rather than for one `exp` term"
      - "At least one DELTA_FRONTIER row in the `b > 27.2` band with a healthy `a` (e.g. eps=775.786660, mu=35.3553) so `test_two_oracles_agree` covers it"
      - "A committed truth for `test_epsilon_for_survives_the_overflow_regime` to compare against, replacing the `> 700.0` liveness assertion"
deferred: []
---

# Phase 22: DP-SGD Core, Accountant, and the Correctness Battery — Verification Report

**Phase Goal:** A from-scratch DP-SGD that is provably not the cheap fake — built and proven
entirely on CPU before a single second of M3 time is spent.
**Verified:** 2026-08-26T03:08:10Z
**Status:** gaps_found
**Re-verification:** No — initial verification

**Verdict in one line:** the DP-SGD **mechanism** is genuinely proven not to be the cheap fake —
SC1, SC2, SC4 and SC5 all hold under adversarial reading. The **accountant** does not meet SC3:
its two-oracle agreement, which is the entire mechanism by which DPSGD-03 claims correctness,
is falsified by measurement in a band the module's own docstring names as reachable.

---

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP Success Criterion) | Status | Evidence |
|---|-----------------------------------|--------|----------|
| 1 | Per-example clipping + Gaussian noise on the **LoRA gradients only**, base frozen, entering `train()` through a NEW ADDITIVE gradient-side seam (DPSGD-01) | ✓ VERIFIED | `dpsgd.py::absorb_record` clips per RECORD over a GLOBAL L2 across all trainable LoRA tensors (`_global_norm` stacks per-tensor norms — the norm of the concatenation), adds into a SUM accumulator, and DRAINS `.grad`. `_noised_private` draws from the dedicated generator at `std=self.sigma*self.C`, adds to the SUM, `/accum` LAST. `_write_once` = one write per parameter with two aliasing refusals. `__init__` is a nine-refusal pre-pass including a `requires_grad` audit by `"lora_" in name` and a closed-form census `r*n_layer*18*n_embd` derived from the LIVE model. `loop.py::_optimizer_step(..., dp_fn=None)` is a new trailing parameter; `clip_grad_norm_` has exactly ONE call site, inside `if dp_fn is None:` (loop.py:220-221). Production caller exists: `scripts/teach_persona.py::train_arm` constructs `DPSGD` after `mark_only_lora_trainable` + `model.to(device)` and passes `dp_fn=` plus `fact_bin`/`n_facts`/`replay_*`. |
| 2 | With the seam off, the default path is **BIT-IDENTICAL** to the Phase-10 golden-trajectory fixture (DPSGD-02) | ✓ VERIFIED | `test_seam_off_bit_identical` **RAN, not skipped**, on this box (Darwin/arm64/torch 2.7.1 == `_CAPTURE_PLATFORM`) and passed on all three fingerprints: exact CSV text, `repr` of the final loss (`9.435891151428223`), sha256 of the parameter bytes (`647f5981…`). `tests/fixtures/golden_trajectory_v1.json` is the genuine Phase-10 artifact (file dated 31 Jul, `captured_at_sha 6a46441c…`, and **not** in Phase 22's changed-file set). `_run_recipe` is IMPORTED from `tests/test_loop_penalty_fn.py`, so no second recipe can drift. `test_golden_fixture_is_the_phase10_one` is a live meta-guard against a truncated fixture. `test_seam_omitted_equals_seam_none` carries the guarantee platform-independently. |
| 3 | The (ε, δ) accountant is stdlib `math` only, exact under q=1 composition, and **agrees with two oracles of DIFFERENT mathematics** (DPSGD-03) | ✗ **FAILED** | (a) stdlib-only: VERIFIED (`import math` is the only import; `test_accountant_imports_math_only` asserts it over the AST). (b) exact under q=1 composition: VERIFIED (`test_composition_identity`, 28 (σ,T) pairs, rel ≤ 1e-12, with `test_composition_identity_would_fail_under_exact_equality` as a live non-vacuity control). (c) **two-oracle agreement: FALSIFIED.** See the three measured defects below. |
| 4 | Each known silent-non-privacy failure is caught with its positive control **WATCHED FAILING FIRST** (DPSGD-04) | ✓ VERIFIED | All four probes in `tests/test_phase22_fakes.py` mutate the **REAL committed** `dpsgd.py` source (`_mutate` asserts the target appears exactly once and that the replacement applied), feed it to the **LIVE guard functions CI runs** by repointing `ast_guards._DPSGD_PATH`, and each carries an UNMUTATED CONTROL through the identical harness. Read directly: FAKE 1 (drain deleted) → `test_dpsgd_step_reaches_no_forbidden_call[absorb_record]` + `[dp-invariant:drain]`, and the probe MEASURES the consequence (sensitivity 1.734481×C vs 1.000000×C honest); FAKE 2 (second clip constant) → `test_dpsgd_has_exactly_one_clip_constant` + `[dp-invariant:sensitivity]`; FAKE 3 (`/N` hoisted) → `test_dpsgd_draws_the_noise_before_it_divides` + the σ>0/N>1 magnitude guard; FAKE 4 (`manual_seed` in `finalize`) → two AST guards + `[dp-invariant:generator]` on step 2, with the consequence measured (`torch.equal` over all 331,776 elements on two steps). Ledger locks (`test_every_fake_has_at_least_two_independent_detectors`, `test_watched_red_node_ids_resolve`, `test_fakes_ledger_names_its_blind_spots`) make the SUMMARY's claims auditable rather than trusted. See WARNING-1 for the residual on the RNG-reuse *class*. |
| 5 | `checkpoint.py` carries an MPS RNG slot with backward-compatible load; kill→resume reproduces a **BIT-IDENTICAL reported ε**; `LoRALinear` not restructured; `persona_adapter.pt` + every v3.0 checkpoint still load (DPSGD-05, DPSGD-07) | ✓ VERIFIED | `checkpoint.py:148` saves `rng["mps"]` `None`-when-unavailable beside `cuda`; `:199` loads via `rng.get("mps")` while `rng["cuda"]` keeps its subscript — the asymmetry is correct and load-bearing. `CKPT_SCHEMA_VERSION` unchanged. All 12 `test_phase22_checkpoint.py` cases **PASSED with zero skips on this box**, including the three real on-disk artifacts (`persona_adapter.pt`, `phase14_real_latest.pt`, `model_slim.pt`). `test_resume_epsilon_bit_identical[1.0]` and `[0.0]` both pass: the resume goes through `train(resume_from=…)`, T is read from the COUNT of composed `finalize` calls (not the checkpoint's `step` field), the ε equality is exact `==`, the σ>0 leg carries a non-degeneracy control, AND the RNG half is separately asserted (`torch.equal` on the next draw) with a negative control that strips `dp_noise_rng`. DPSGD-07: `git diff --exit-code -- src/personacore/lora/` exits 0 and the directory's last commit predates Phase 22 entirely. |

**Score:** 4/5 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/personacore/privacy/dpsgd.py` | The DP-SGD mechanism | ✓ VERIFIED | 619 lines, substantive, imported by `teach_persona.py` and by 3 test modules. Nine construction refusals, four runtime invariants, all reachable and all exercised. |
| `src/personacore/privacy/accountant.py` | Two δ oracles + `epsilon_for`/`sigma_for` | ⚠️ **DEFECTIVE** | 705 lines, exists, wired, math-only. Three independent numerical defects — see the gaps table. Correct in every regime the project operates in; wrong outside it, without refusing. |
| `src/personacore/training/loop.py` | The additive `dp_fn=` gradient-side seam + `fact_bin=` data seam | ✓ VERIFIED | `dp_fn` threaded `train()` → `_optimizer_step`; four take-over points; legacy clip structurally unreachable on the DP path; `_dp_extra()` splatted into **all three** `save_checkpoint` sites (`:877`, `:900`, `:927`). |
| `src/personacore/checkpoint.py` | `rng["mps"]` slot, back-compatible load | ✓ VERIFIED | Save at `:148`, load at `:199` via `.get()`. Real gitignored artifacts round-trip. |
| `scripts/teach_persona.py` | D-08's four production wirings on `dp_n8`/`dp_n64` | ✓ VERIFIED | One `is_dp` predicate gates all four; σ and C are required no-default CLI args (`--sigma=`, `--clip-norm=`) with a `SystemExit` when a DP arm lacks either; `grad_accum_steps=stats["n_facts"]` is a real `ast.keyword`. No numeric σ or C literal in the file. |
| `scripts/mitigation_accountant.py` | The FROZEN pin | ✓ VERIFIED | Zero imports; `GOLDEN_EPSILON`'s seven rows; `REQUIRED_FORM`/`REJECTED_FORM`; `NEIGHBOURING`/`SENSITIVITY_MULTIPLIER`. All seven pinned ε reproduce to ≤ 1.07e-14 relative against `epsilon_for`, and **all seven sit outside the CR-03 defect band** (b ∈ [3.19, 7.94], `erfc(b)` healthy). |
| `tests/test_phase22_*.py` (7 files) | The correctness battery | ✓ VERIFIED | 253 tests, all passing. Full suite: **1280 passed, 1 skipped** (222 s) — matches the pre-verification baseline exactly, no regression. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `teach_persona.py::train_arm` | `DPSGD` | `dp_fn=` kwarg into `train()` | ✓ WIRED | Constructed after freeze + device move; `runtime=` passed so the AMP refusal is armed. |
| `teach_persona.py::main` | `train_arm` | `dp_n8`/`dp_n64` + `--sigma=`/`--clip-norm=` | ✓ WIRED | `test_phase22_wiring.py::test_end_to_end_writes_no_scored_artifact` drives it end to end. |
| `train()` | `DPSGD.noise_rng_state` | `_dp_extra()` splat | ✓ WIRED | All three save sites. The end-of-call one is asserted specifically (`test_resume_epsilon_bit_identical:451`). |
| `train(resume_from=)` | `DPSGD.load_noise_rng_state` | `ckpt.get("dp_noise_rng")` | ⚠️ **PARTIAL** | Wired and proven on the happy path, but the guard is a **silent no-op fallback where a refusal belongs**. See WARNING-1. |
| `teach_persona.py` | `train(resume_from=)` on a DP arm | — | ⚠️ **NOT WIRED** | No production driver can resume a DP arm at all. See WARNING-2. |
| `accountant.py` | any production consumer | — | ℹ️ **NONE YET** | `epsilon_for`/`sigma_for` are imported only by `src/personacore/privacy/__init__.py` (lazy re-export) and by tests. No code reports an ε today — that is Phase 23's `mitigation_budget.py`. SC5's "reported ε" is therefore computed by the test, which is correct for this phase's scope but worth recording. |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `DPSGD._accum` | clipped per-record sum | `p.grad` after each real `backward()` | Yes — `test_sum_then_noise_then_divide`, `test_noise_is_scaled_by_the_lot_size…` measure magnitudes | ✓ FLOWING |
| `dp_noise_rng` (checkpoint) | `dp_fn.noise_rng_state()` | live generator at each save | Yes — `kill["dp_noise_rng"].numel() > 0` asserted; 5,056 B on CPU | ✓ FLOWING |
| `rng["mps"]` (checkpoint) | `torch.mps.get_rng_state()` | real MPS state on this box | Yes, but **required-but-UNEXERCISED by the DP path** (the dedicated generator's draw does not move the global MPS stream) — recorded honestly in the module docstring, not glossed | ⚠️ STATIC-BY-DESIGN |
| `GOLDEN_EPSILON` | seven pinned ε | bisected against `delta_quadrature` ALONE, asserted over the test's own AST | Yes — worst deviation 5.75e-15 vs a 1e-12 budget, and every row deviates (min 1.62e-15), so the pin is not a photograph | ✓ FLOWING |
| `delta_closed` / `delta_quadrature` | δ | closed form / Simpson quadrature | **Partly** — correct on the 12 committed rows and every operating regime; produces a 12.74%-wrong δ, `+inf`, and `>1.0` outside them without refusing | ⚠️ **HOLLOW AT THE EDGES** |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full regression suite | `.venv/bin/python -m pytest -q` | `1280 passed, 1 skipped` in 222.28 s | ✓ PASS |
| Phase-22 battery | `pytest tests/test_phase22_*.py -q` | `253 passed` in 23.87 s | ✓ PASS |
| Golden bit-identity actually runs | `pytest tests/test_phase22_dpsgd.py -v` | `test_seam_off_bit_identical PASSED` (not skipped) | ✓ PASS |
| Real v3.0 artifacts load | `pytest tests/test_phase22_checkpoint.py -v` | 12 passed, **0 skipped** — incl. `persona_adapter.pt` | ✓ PASS |
| LoRA untouched | `git diff --exit-code -- src/personacore/lora/` | exit 0; last commit predates Phase 22 | ✓ PASS |
| Lint | `ruff check` + `ruff format --check` on all Phase-22 files | `All checks passed!` / `10 files already formatted` | ✓ PASS |
| `epsilon_for` at a subnormal σ | `epsilon_for(5e-308, 200, 1e-5)` | `0.0` (expected `inf` or a refusal) | ✗ **FAIL** |
| δ is a probability (quadrature) | `delta_quadrature(0.000440884929509763, 75.3129260813192)` | `inf` | ✗ **FAIL** |
| δ ≤ 1 (quadrature) | 4000-cell sweep | 60 cells above 1.0, max `1.000000000000009` | ✗ **FAIL** |
| Two oracles agree at the module's own cited frontier point | `delta_closed(775.7866600701457, 35.35533905932738)` vs `delta_quadrature(…)` | `9.99999999999972e-06` vs `8.870303048231617e-06` — **11.30% apart** | ✗ **FAIL** |
| Independent third computation of the same δ | asymptotic `log(erfc(b))` series, in-process | `8.870303048329635e-06` — agrees with the QUADRATURE to 1.1e-11; shipped `delta_closed` is **12.74% high** | ✗ **FAIL** |

### Probe Execution

| Probe | Command | Result | Status |
|-------|---------|--------|--------|
| — | — | No `scripts/*/tests/probe-*.sh` exist in this project and no PLAN declares one; the project's runnable-check convention is pytest, executed above | SKIPPED (N/A) |

---

### Requirements Coverage

| Requirement | Source Plan(s) | Status | Evidence |
|-------------|----------------|--------|----------|
| DPSGD-01 | 22-04, 22-06, 22-10, 22-11 | ✓ SATISFIED | Truth 1. Per-record global clip, SUM accumulator, dedicated-generator noise on the sum, `/N` last, one combining write, LoRA-only enforced as a property of the MECHANISM. Production caller reachable from `main()`. |
| DPSGD-02 | 22-06, 22-08, 22-11 | ✓ SATISFIED | Truth 2. Three-fingerprint bit-identity against the genuine Phase-10 fixture, ran rather than skipped, with a vacuity meta-guard and a platform-independent companion. |
| DPSGD-03 | 22-01, 22-02, 22-03, 22-05, 22-09, 22-10 | ✗ **BLOCKED** | Truth 3. Math-only and q=1 exactness hold. The two-oracle agreement — this requirement's own stated mechanism of proof — is falsified by measurement. REQUIREMENTS.md marks this row `[x] SATISFIED`; that row is not supported by the code outside the 12 committed frontier points. |
| DPSGD-04 | 22-01, 22-02, 22-04, 22-06, 22-09, 22-11 | ✓ SATISFIED | Truth 4. Four fakes, nine detectors, each probe re-applies its mutation to the real module and re-observes the refusal on every run, each with an unmutated control. Blind spots (FAKE 3 at σ=0 and at accum=1; the one-sided `C*(1+tol)` check) are asserted as committed tables rather than described. |
| DPSGD-05 | 22-05, 22-06, 22-07 | ✓ SATISFIED | Truth 5. MPS slot + `.get()` back-compat + bit-identical resumed ε through the production `train()` API, with the RNG half carrying its own control. |
| DPSGD-07 | 22-07 | ✓ SATISFIED | Truth 5. `src/personacore/lora/` byte-unchanged; bare `nn.Parameter` asserted directly; key FORM pinned as a literal after M7 was measured to leave set-equality green. |
| DPSGD-06 | — (Phase 23) | ℹ️ DEFERRED, correctly | REQUIREMENTS.md maps it to Phase 23 and Phase 23's SC1 owns it verbatim. **Not orphaned.** |

**Orphaned requirements:** none. Every ID the roadmap assigns to Phase 22 (DPSGD-01, 02, 03, 04, 05, 07) is claimed by at least one plan's frontmatter, and DPSGD-06 is explicitly routed to Phase 23 in both REQUIREMENTS.md and ROADMAP.md.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| all 15 Phase-22 files | — | `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` | — | **ZERO markers.** Clean. |
| all 15 Phase-22 files | — | `ruff check` / `ruff format --check` | — | Clean. |
| `accountant.py` | 181-186 | Comment asserts a property the code does not have | 🛑 Blocker | *"Log space keeps the identical product below the line"* — cited against σ=0.40/T=200, which is exactly where `eb == 0.0` makes the `else` branch unreachable and the product is dropped, not kept. |
| `accountant.py` | 452-464 | Docstring asserts an unreachability proof whose premise never held | 🛑 Blocker | *"`mu` is a finite strictly-positive number the caller computed"* — `mu = sqrt(steps)/sigma` is never checked for finiteness. `test_delta_closed_still_ships_exactly_four_raises` protects the *raise count* the argument rests on and is structurally incapable of noticing the other premise is false. |
| `accountant.py` | 143-149, 261-267 | `Returns:` contracts measurably false outside the committed rows | 🛑 Blocker | "at least 12 significant digits ... everywhere this function does not refuse" (delivers 0 at eps=775.79); "delta in (0, 1]" (returns `inf` and >1.0). |
| `loop.py` | 735-736 | Silent no-op fallback where a refusal belongs | ⚠️ Warning | See WARNING-1. |

---

### WARNINGS (not blocking, but they must not be inherited as clean)

**WARNING-1 — `loop.py:735-736` is a silent fallback, and the review's scoping of it is wrong in
both directions.**

The code is `if dp_fn is not None and ckpt.get("dp_noise_rng") is not None:` with no `else`, and
the comment eleven lines above names the exact consequence and then permits it. That much of
CR-04 is correct and the fix (refuse) is right.

But I traced the reachability myself rather than accepting either the review's claim or the
orchestrator's, and **"reachable through PRODUCTION" is not supported by this tree**:

- All three `save_checkpoint` sites inside `train()` splat `_dp_extra()` (`loop.py:877`, `:900`,
  `:927`), so **every checkpoint a DP run writes carries `dp_noise_rng`** — the end-of-call one is
  asserted specifically at `test_phase22_checkpoint.py:451`. The branch is therefore silent only
  when the prior run was NOT a DP run, and in that case the freshly seeded generator has released
  nothing, so seeding fresh is the correct behaviour, not a replay.
- `scripts/teach_persona.py::train_arm` — the only production DP caller — **never passes
  `resume_from`**, and its `refuse_if_exists(... paths["checkpoint"] ...)` actively blocks
  re-running a killed DP arm. There is no production path into this branch at all.
- The review also states the test *"exercises only the happy path, where the key is present."*
  **That is false.** `test_phase22_checkpoint.py:519-539` deliberately strips `dp_noise_rng` and
  asserts the resumed stream diverges — it uses the CR-04 branch as its negative control.

What remains genuinely open, and why it still matters: a silent fallback where a refusal belongs,
plus the **symmetric hole nobody has named** — `dp_fn is None` with `ckpt["dp_noise_rng"]` PRESENT
is equally unguarded, and that one is worse: a DP run resumed without the seam continues with no
clipping and no noise, silently. Both become live the moment Phase 23 wires DP resume, which
`CLAUDE.md` says is routine on the primary M3 path. One guard covering both directions closes it.

**WARNING-2 — DP kill→resume has no production driver.**
SC5's wording ("a kill→resume reproduces a bit-identical reported ε") is satisfied through
`train(resume_from=…)`, which is the production API, and the test correctly refuses to restore by
hand. But `teach_persona.py` cannot resume a DP arm, so the workflow SC5 describes is exercised
only from tests today. This is the same unwired-seam shape as Phase 21's IN-04 and should be
carried forward rather than inherited as done.

**WARNING-3 — no production consumer of the accountant exists.**
`epsilon_for`/`sigma_for` are reachable only from `privacy/__init__.py`'s lazy re-export and from
tests. No code path publishes an ε. That is correct for this phase's scope (budget
pre-registration is Phase 23 / CAL-02), but it means the SC3 defects are latent rather than
currently mis-reporting anything — and it means Phase 23 will be the first consumer, so the
defects should close before it lands.

---

### Human Verification Required

None. Every truth was resolvable from the codebase: the golden replay and the real-artifact legs
both RAN rather than skipped on this box, so nothing was left to a platform-gated skip. No PLAN
carried a deferred `<verify><human-check>` block.

---

### Gaps Summary

**The mechanism half of this phase is the strongest work in the tree and it does what it says.**
The clip is genuinely per-record over a global L2 across all 72 LoRA tensors, the accumulator holds
the SUM so sensitivity is `C` independent of the lot size, the noise lands on the sum with the `/N`
last, the generator is dedicated and never re-seeded on the step path, the legacy averaged-gradient
clip really does have exactly one reachable call site inside `if dp_fn is None:`, and the four
silent-non-privacy fakes are caught by nine detectors whose RED is re-observed on every test run
against the real committed module rather than trusted from a SUMMARY. I tried to break the
per-record sensitivity argument and could not. SC1, SC2, SC4 and SC5 hold.

**The accountant does not meet SC3, and it fails on the specific axis the criterion names.**
DPSGD-03's whole design is that a second oracle of different mathematics cannot share the
implementation's failure modes. Measured, the two oracles disagree by up to **12.74% relative in
δ** — and the disagreement is not a numerical curiosity, it is `delta_closed` silently discarding a
term worth 11% of the answer whenever `math.erfc(b)` underflows. It happens at
(σ=0.40, T=200, δ=1e-5), the exact input the line's own comment cites as reachable on this
project's frontier and the exact input the plan's own `must_haves` names. I confirmed which oracle
is right with a third, independent computation (asymptotic `log(erfc(b))`): the quadrature is
correct to 1.1e-11 and the closed form has zero correct significant digits, against a docstring
promising at least twelve. The test that visits σ ∈ {0.40, 0.30} asserts only that a finite number
above 700 came back. The agreement test cannot see it because no committed `DELTA_FRONTIER` row
lives in that band. On top of that, the second oracle itself returns `+inf` and values above 1.0
for a quantity that is a probability, and `epsilon_for` reports ε = 0 — perfect privacy — for a
subnormal σ, in the privacy-understating direction, through a guard whose docstring proves its own
unreachability from a premise nothing establishes.

**Stated with the honesty this phase demands of itself: no published number is currently wrong.**
All seven `GOLDEN_EPSILON` rows and all twelve `DELTA_FRONTIER` rows sit outside every defect band.
CR-03's direction is conservative (δ over-stated ⇒ ε over-stated), its induced ε error is 1.218e-03
relative at σ=0.40/T=200 and **exactly zero at σ ≥ 0.42**, and CR-01's band needs a subnormal σ that
no CLI input and no `sigma_for` walk can produce. Nothing in this tree has yet reported an ε at all.

That is precisely why this is a gap and not a catastrophe — and precisely why it must close before
Phase 23, which is the accountant's first consumer. This phase's stated purpose is *provably* not
the cheap fake. A module whose two published tolerances are both 1e-12, whose two independent
oracles disagree by 12.7% where nobody looked, and whose own comments assert three properties the
code does not have, is not yet proven — it is untested outside its fixture set. The five `missing:`
items in the frontmatter are the whole closure, and none of them touches `dpsgd.py`, `loop.py`,
`checkpoint.py` or any of the four positive controls.

---

_Verified: 2026-08-26T03:08:10Z_
_Verifier: Claude (gsd-verifier)_
