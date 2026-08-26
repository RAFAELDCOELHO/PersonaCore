---
phase: 22
slug: dp-sgd-core-accountant-and-the-correctness-battery
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-08-25
---

# Phase 22 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `22-RESEARCH.md` § *Validation Architecture*; decisions from `22-CONTEXT.md` D-01 … D-18.

**Nothing in this phase requires a GPU.** Every row runs on CPU. The MPS-touching row is
`skipif`-gated and is recorded honestly as **required-but-unexercised** in CI, per D-14 — no future
reader should believe the DP path fires the `rng["mps"]` slot.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (already in `[dev]` — nothing to install) |
| **Config file** | `pyproject.toml` → `[tool.pytest.ini_options]`, `pythonpath = ["."]` at `:26` |
| **Quick run command** | `.venv/bin/python -m pytest tests/test_phase22_*.py -x -q` |
| **Full suite command** | `make test` (CPU-only, GPU-free) + `make lint` |
| **Estimated runtime** | ~30 s quick (accountant frontier ≈ 0.3 s; one `delta_quadrature` at n=20,001 ≈ 10 ms) |

**Python 3.11 venv is MANDATORY** (`CLAUDE.md`). The dev box runs 3.14, which is not a supported
target — never validate against it.

---

## Sampling Rate

- **After every task commit:** `.venv/bin/python -m pytest tests/test_phase22_*.py -x -q`
- **After every plan wave:** `make test` && `make lint`
- **Before `/gsd:verify-work`:** full suite green **and** all four positive controls observed
  **RED before GREEN with the RED output recorded** (DPSGD-04 requires the watched failure, not the
  final green)
- **Runtime, EVERY training step:** D-16's four invariants fire inside the seam. Justified by the
  measured cost asymmetry — a failure costs **~17 s** (training) against **4.77 h** (evaluation,
  which runs after; `REQUIREMENTS.md:159-161`). Cheap and early, not expensive and late.
- **Max feedback latency:** 30 s

---

## Per-Task Verification Map

Task IDs are assigned at planning; the requirement→validation mapping below is fixed and every plan
task must inherit a row from it. `Threat Ref` is `—` throughout: this phase's threat surface is the
DP guarantee itself, covered by the D-05/D-16/D-17 guard rows rather than by an ASVS entry.

| V-ID | Requirement | Behaviour validated | Test type / granularity | Automated command | File Exists | Status |
|------|-------------|---------------------|-------------------------|-------------------|-------------|--------|
| V-01 | DPSGD-03 | `delta_closed` matches Balle–Wang Thm 8 on the 12-point frontier | unit, once per run | `…::test_closed_form_frontier -x` | ❌ W0 | ⬜ pending |
| V-02 | DPSGD-03 | `delta_quadrature` agrees with `delta_closed` — **relative** tol 1e-9, with `a != 0.0 and b != 0.0` asserted FIRST (F1) | unit, once per run | `…::test_two_oracles_agree -x` | ❌ W0 | ⬜ pending |
| V-03 | DPSGD-03 | `ε(σ,T,δ)` vs `ε(σ/√T,1,δ)` composition oracle — rel gap ≤ 1e-12, **never `==`** (F3) | unit, ≥20 swept (σ,T) | `…::test_composition_identity -x` | ❌ W0 | ⬜ pending |
| V-04 | DPSGD-03 | derived range beats the fixed range at ε=8, μ=0.5 (where `[-14,14]` gives 1.0 rel err) | unit, once per run | `…::test_low_privacy_corner -x` | ❌ W0 | ⬜ pending |
| V-05 | DPSGD-03 | **non-vacuity refusal fires** — all 3 conditions, each separately | unit, `pytest.raises(ValueError)` ×3 | `…::test_oracle_refuses -x` | ❌ W0 | ⬜ pending |
| V-06 | DPSGD-03 | `GOLDEN_EPSILON` re-derives from the **oracle**, never snapshotted from `accountant.py` | unit, once per run | `…::test_golden_epsilon_from_oracle -x` | ❌ W0 | ⬜ pending |
| V-07 | DPSGD-03 | round-trip `sigma_for(epsilon_for(σ,T,δ),T,δ) ≈ σ` (rel ≤ 1e-12) | unit, once per run | `…::test_round_trip -x` | ❌ W0 | ⬜ pending |
| V-08 | DPSGD-03/05 | `σ = 0 → ε = inf`, never `ZeroDivisionError` | unit, once per run | `…::test_sigma_zero -x` | ❌ W0 | ⬜ pending |
| V-09 | DPSGD-03 | `accountant.py` imports **`math` only** | **build time (AST)** | `…::test_accountant_imports_math_only -x` | ❌ W0 | ⬜ pending |
| V-10 | DPSGD-03 | frozen pin has **zero imports** and no executable formula | **build time (AST)** | `pytest tests/test_phase20_prereg.py -k accountant -x` | ❌ W0 | ⬜ pending |
| V-11 | DPSGD-01/04 | D-05 axis 1 — no `.backward()`, `.grad` write, clip/normalize, **second clip constant**, or **in-step re-seed** between noise and `step()` | **build time (AST)** | `pytest tests/test_phase22_dpsgd_ast.py -x` | ❌ W0 | ⬜ pending |
| V-12 | DPSGD-01/04 | D-05 axis 2 — one-kwarg-apart differential; private noised term byte-identical with/without the public term | unit, once per run | `…::test_side_channel_negative_control -x` | ❌ W0 | ⬜ pending |
| V-13 | DPSGD-01/04 | D-16's four runtime invariants: `.grad` drain, sensitivity ≤ `C*(1+tol)`, single-write count, generator-state advance | **runtime, EVERY step** | exercised by every DP test + the D-08 end-to-end run | ❌ W0 | ⬜ pending |
| V-14 | DPSGD-02 | seam off ⇒ bit-identical to `tests/fixtures/golden_trajectory_v1.json` | platform-gated replay + platform-independent in-process identity | `…::test_seam_off_bit_identical -x` | ❌ W0 | ⬜ pending |
| V-15 | DPSGD-05 | kill→resume reproduces a **bit-identical reported ε** — exact `==` is correct here (same call shape, F3) | integration, once per run | `…::test_resume_epsilon_bit_identical -x` | ❌ W0 | ⬜ pending |
| V-16 | DPSGD-05 | `rng["mps"]` slot round-trips; **old checkpoints without it still load** | unit + `skipif` MPS | `pytest tests/test_phase22_checkpoint.py -x` | ❌ W0 | ⬜ pending |
| V-17 | DPSGD-07 | `persona_adapter.pt` + every v3.0 checkpoint still load; `LoRALinear` state-dict keys unchanged | unit, key-set equality | existing `tests/test_lora_*.py` + one new assertion | ⚠️ partial | ⬜ pending |
| V-18 | DPSGD-04 | **FAKE 1** clip the averaged gradient — drop the drain; D-05 axis 4 reddens | **one-shot positive control, RED→GREEN** | `…::test_fake_averaged_gradient -x` | ❌ W0 | ⬜ pending |
| V-19 | DPSGD-04 | **FAKE 2** wrong sensitivity — add a second clip constant; AST **and** runtime `C*(1+tol)` both redden | **one-shot positive control, RED→GREEN** | `…::test_fake_wrong_sensitivity -x` | ❌ W0 | ⬜ pending |
| V-20 | DPSGD-04 | **FAKE 3** noise after averaging — build `divide → noise`; D-06's CPU σ=0 identity breaks | **one-shot positive control, RED→GREEN** | `…::test_fake_noise_after_averaging -x` | ❌ W0 | ⬜ pending |
| V-21 | DPSGD-04 | **FAKE 4** RNG reuse — add an in-step `manual_seed`; AST **and** generator-state check redden | **one-shot positive control, RED→GREEN** | `…::test_fake_rng_reuse -x` | ❌ W0 | ⬜ pending |
| V-22 | DPSGD-01 | D-04's three property refusals at the seam: non-`lora_` `requires_grad`, scaler enabled, trainable count == 331,776. Positive control = `inject_lora` **without** `mark_only_lora_trainable` (172 tensors / 14,223,360 params) | unit + runtime at seam construction | `…::test_seam_refuses -x` | ❌ W0 | ⬜ pending |
| V-23 | DPSGD-01 | D-08's four wirings execute end-to-end on a CPU fixture and write **NO scored artifact** | integration, once per run | `pytest tests/test_phase22_wiring.py -x` | ❌ W0 | ⬜ pending |
| V-24 | — | `pyproject.toml` untouched (RPT-03); `mitigation_gate.py` / `mitigation_unit.py` unmodified | regression, once per run | `pytest tests/test_phase20_prereg.py -x` | ✅ exists | ⬜ pending |
| V-25 | DPSGD-03/04 | **D-18** — `NEIGHBOURING` / `SENSITIVITY_MULTIPLIER` exist in the frozen pin, and the **cross-site consistency check** proves `accountant.py`'s documented relation and `dpsgd.py`'s noise line name the SAME relation | **build time (multi-site read)** | `…::test_adjacency_relation_consistent -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Gap-Closure Addendum — V-26 … V-34 (added 2026-08-26, plan 22-16)

`22-VERIFICATION.md` returned `gaps_found` at 4/5 and listed five `missing:` items. Plans `22-12`,
`22-13`, `22-14` and `22-15` closed them and added nine guards that this contract did not cover.
Numbering continues from V-25; the column shape is the table above's.

**Every `Automated command` below was RUN by plan 22-16 and observed exiting 0** — the pass counts
in the last column are that run's own output, not a prediction. The V-01 … V-25 rows above keep
their pre-execution `⬜ pending` status: re-scoring them is the re-verification's job, not this
addendum's.

| V-ID | Requirement | Behaviour validated | Test type / granularity | Automated command | File Exists | Status |
|------|-------------|---------------------|-------------------------|-------------------|-------------|--------|
| V-26 | DPSGD-03 | `_log_erfc` is **inert where `erfc` is healthy** — exact `==` over the 18 pinned points (11 frontier + 7 golden), so the repair cannot move the frozen pin; plus a hard-count companion pinning the count and the single exclusion, because the sweep's own filter would make an in-test meta-guard a tautology | unit, 18 pinned points + 1 count guard | `.venv/bin/python -m pytest tests/test_phase22_accountant.py::test_log_erfc_is_inert_where_erfc_is_healthy tests/test_phase22_accountant.py::test_log_erfc_inert_points_are_not_empty -q` | ✅ exists | ✅ green (19 passed) |
| V-27 | DPSGD-03 | `_log_erfc` matches the committed 60-dps `log(erfc(b))` at `b = 28.01573320140291` — the underflow band where `delta_closed`'s shipped `else` branch was unreachable and its second term was silently dropped | unit, once per run | `.venv/bin/python -m pytest tests/test_phase22_accountant.py::test_log_erfc_matches_the_committed_underflow_truth -q` | ✅ exists | ✅ green (1 passed) |
| V-28 | DPSGD-03 | The **thirteenth `DELTA_FRONTIER` row** carries V-01 and V-02 into the `b > 27.2` band the twelve committed rows could not reach — measured two-oracle gap **1.1050e-11** against the **UNWIDENED** 1e-9 budget | unit, 2 legs (V-01 + V-02 at the new row) | `.venv/bin/python -m pytest tests/test_phase22_accountant.py -q -k 775.7866600701457` | ✅ exists | ✅ green (2 passed, 188 deselected) |
| V-29 | DPSGD-03 | `epsilon_for` in the overflow regime is compared against **committed 60-dps epsilons** (`EPSILON_OVERFLOW_REGIME`), replacing the `math.isfinite(got) and got > 700.0` liveness assertion that visited the defect without comparing anything | unit, σ ∈ {0.40, 0.30} | `.venv/bin/python -m pytest tests/test_phase22_accountant.py::test_epsilon_for_survives_the_overflow_regime -q` | ✅ exists | ✅ green (2 passed) |
| V-30 | DPSGD-03 | Condition 1 budgets for the Simpson **SUM** via `log(4*n)`, not for one `exp` term — the former **404-of-4001-cell `inf` band** now refuses, and the cited defect point refuses with `DOMAIN LIMIT` rather than a later condition's wrong diagnosis | unit, cited defect point + a 14-point band sweep with a length meta-guard | `.venv/bin/python -m pytest tests/test_phase22_accountant.py::test_quadrature_budgets_the_simpson_sum_not_one_term -q` | ✅ exists | ✅ green (1 passed) |
| V-31 | DPSGD-03 | `delta_quadrature` returns a value in `(0, 1]` **or raises — never between**. The slack is `_DELTA_ACCUMULATION_SLACK = 1e-11`, MEASURED over 5,351 answered cells; the verification's literal `0.0 < delta <= 1.0` would have refused 267 of them (4.99%), all correct | unit, 240 cells | `.venv/bin/python -m pytest tests/test_phase22_accountant.py::test_quadrature_returns_a_probability_or_refuses -q` | ✅ exists | ✅ green (1 passed) |
| V-32 | DPSGD-03 | `epsilon_for` answers **`+inf`, never `0.0`**, for every σ whose `sqrt(steps)/sigma` overflows — the privacy-UNDERSTATING direction closed, and closed **CONTINUOUSLY with V-08's σ=0 branch** rather than relocating the discontinuity to a raise. Boundary DERIVED per step count from `sys.float_info.max` inside the test, never hardcoded (the module's `math`-only ceiling is V-09's and stays intact) | unit, T ∈ {1, 64, 200, 1000} × 3 in-band σ | `.venv/bin/python -m pytest tests/test_phase22_accountant.py::test_epsilon_for_answers_inf_in_the_subnormal_sigma_band -q` | ✅ exists | ✅ green (4 passed) |
| V-33 | DPSGD-03 | `_delta_or_below_float64` **refuses a non-finite or non-positive `mu` before its `try`**, so the docstring premise its bare `except ValueError` rested on is a postcondition of its own prologue instead of an unestablished assertion about the caller | unit, μ ∈ {`inf`, `-inf`, `nan`, `0.0`, `-1.0`} | `.venv/bin/python -m pytest tests/test_phase22_accountant.py::test_delta_or_below_float64_refuses_the_inputs_it_may_not_read_as_ordering -q` | ✅ exists | ✅ green (5 passed) |
| V-34 | DPSGD-04/05 | Resuming with `dp_fn=None` from a checkpoint carrying `dp_noise_rng` **REFUSES** — the direction that turns a private run non-private in silence — and the refusal fires **before any save**. Two narrowness legs in the same test: the sibling direction (seam live, slot absent) stays TOLERATED, and an ordinary non-DP resume is not caught | integration, 3 legs | `.venv/bin/python -m pytest tests/test_phase22_dpsgd.py::test_resume_without_the_seam_refuses_a_dp_checkpoint -q` | ✅ exists | ✅ green (1 passed) |

**Full suite at the time these were recorded:** `.venv/bin/python -m pytest -q` →
**`1314 passed, 1 skipped`** in 220.25 s; `.venv/bin/ruff check . && .venv/bin/ruff format --check .`
→ `All checks passed! / 203 files already formatted`.

**`make test` is BROKEN and must not be used** — bare `pytest` resolves to the pyenv 3.12.13 first
on `PATH` and produces ~83 `ModuleNotFoundError: torch`. The *Full suite command* cell in the Test
Infrastructure table above says `make test`; it was written at planning time and is wrong in this
tree. Use `.venv/bin/python -m pytest -q` (~220 s) and `.venv/bin/ruff check . && .venv/bin/ruff
format --check .`. Recorded here rather than by editing the row above, per this phase's
retract-in-place discipline.

**Each of these guards was WATCHED RED under a mutation of the real committed module**, which is
this phase's standard of evidence — the observed RED, not the final green. Distinct-RED counts,
verbatim messages and sha256-identical restores are in the SUMMARYs: `22-12` M-A/M-B/M-G (3/6/4),
`22-13` M-H (1, measured over the FULL suite), `22-14` M-C/M-D/M-D-sat/compound (1 each) with
M-D-partial and M-E proven behaviourally **inert** rather than reported as unwatched, and `22-15`
M-E/M-E-both/M-F (1/2/1). Two of those registers found that the mutation the plan specified was one
hunk where the fix ships as two independent layers, and reported the single-hunk result separately.

---

## Gap-Closure Addendum, Round 2 — V-35 … V-39 (added 2026-08-26, plan 22-19)

The 2026-08-26 re-verification confirmed all five `missing:` items above genuinely closed and
returned `gaps_found` 4/5 **anyway** — SC3 falsified on the same conjunct, by the same mechanism,
one band over: `_log_erfc` routed on `erfc(x) > 0.0`, so the range where `math.erfc` returns a
SUBNORMAL took `math.log` of a float that had already discarded up to 52 of its 53 mantissa bits.
Plans `22-17` and `22-18` closed it and added five guards this contract did not cover. Numbering
continues from V-34; the column shape is the table above's.

**Every `Automated command` below was RUN by plan 22-19 before its row was written**, and the pass
count in each Status cell is that run's own output, not a prediction. The V-01 … V-25 rows keep
their pre-execution `⬜ pending` status for the reason the round-1 addendum gives.

**The structural difference from round 1, stated because it is the point rather than a detail.**
Round 1's guards were a POINT LIST, and a point list is worth exactly the band it sweeps — which is
how a defect survived one band away from the one that was fixed. V-35 is parametrized on the
ROUTING BOUNDARY'S OWN NEIGHBOURHOOD and asserts a property of the RESULT ("whatever route was
chosen at `x`, that route is accurate at `x`"), so it never names the boundary and reddens when the
boundary moves. V-36 exists because V-35 can be satisfied vacuously by a table that has drifted off
the boundary.

| V-ID | Requirement | Behaviour validated | Test type / granularity | Automated command | File Exists | Status |
|------|-------------|---------------------|-------------------------|-------------------|-------------|--------|
| V-35 | DPSGD-03 | `_log_erfc` agrees with a committed 60-dps `log(erfc(x))` across its ROUTING BOUNDARY, over a band spanning all three `math.erfc` regimes (NORMAL / SUBNORMAL / exactly 0.0). Asserts a property of the **result**, never of the predicate — no route detector, no AST detector — so it reddens on a boundary move **without naming the boundary**. 26.8 is load-bearing and must not be pruned: without it a boundary hidden anywhere in (26.7, 26.9] stays green | unit, 17 band rows | `.venv/bin/python -m pytest tests/test_phase22_accountant.py::test_log_erfc_band_routes_accurately -q` | ✅ exists | ✅ green (17 passed) |
| V-36 | DPSGD-03 | V-35's NON-VACUITY companion: every band row is classified by calling `math.erfc` **at run time** and all three regimes must be non-empty (measured on this box: 4 normal / 9 subnormal / 4 zero), plus a HARD-EQUALITY pin that the lowest subnormal row is the boundary float `26.54325845425098`. It never calls `_log_erfc`, so **the module under test cannot satisfy its own meta-guard** | unit, once per run over 17 rows | `.venv/bin/python -m pytest tests/test_phase22_accountant.py::test_log_erfc_band_spans_all_three_erfc_regimes -q` | ✅ exists | ✅ green (1 passed) |
| V-37 | DPSGD-03 | The **FOURTEENTH `DELTA_FRONTIER` row** carries V-01 and V-02 into the erfc-SUBNORMAL band that **0 of the previous 22 pinned points entered** — `(728.2043182233367, 34.159747883408095)`, `erfc(b) = 1.43e-322` asserted strictly between 0.0 and the smallest normal at run time. Measured V-01 3.6662e-14 against 1.5e-12 (40.9× inside) and V-02 1.0137e-11 against an **UNWIDENED** 1e-9 (98.6× inside) | unit, 2 legs (V-01 + V-02 at the new row) | `.venv/bin/python -m pytest tests/test_phase22_accountant.py -q -k 728.2043182233367` | ✅ exists | ✅ green (2 passed, 212 deselected) |
| V-38 | DPSGD-03 | `_inert_points()` is filtered on `sys.float_info.min`, **not** on `erfc(b) > 0.0` — the old filter defined "healthy" as the property the defect satisfies, so it CERTIFIED THE DEFECTIVE BAND AS HEALTHY and the filter encoded the defect. Plus the hard-count companion, held deliberately at 18 with a two-entry exclusion list pinned by equality rather than by count | unit, 18 pinned points + 1 count guard | `.venv/bin/python -m pytest tests/test_phase22_accountant.py::test_log_erfc_is_inert_where_erfc_is_healthy tests/test_phase22_accountant.py::test_log_erfc_inert_points_are_not_empty -q` | ✅ exists | ✅ green (19 passed) |
| V-39 | DPSGD-03 | `ROUND_TRIP_REL_TOL` is a bound over a sweep that **includes its own worst case**: σ=0.414 is in `_round_trip_pairs()`, whose T=200 leg was measured **2.07e+07× over** the 1e-12 tolerance before 22-17. Exactly one of its four T legs is in the band (T=200; T=1 and 64 are NORMAL, T=1000 is past the cliff), and no assertion requires otherwise. The presence of 0.414 is pinned by HARD EQUALITY because both count guards pass a swap that keeps the count at 52 | unit, 4 round-trip legs + 1 hard-equality pin | `.venv/bin/python -m pytest tests/test_phase22_accountant.py -q -k "test_round_trip_pairs_is_not_empty or (test_round_trip and 0.414)"` | ✅ exists | ✅ green (5 passed, 209 deselected) |

**Full suite at the time these were recorded:** `.venv/bin/python -m pytest -q` →
**`1338 passed, 1 skipped`**; `.venv/bin/ruff check . && .venv/bin/ruff format --check .` →
`All checks passed! / 203 files already formatted`. Plan 22-19 changed **no source code**, so this
count is 22-18's closing count unmoved — any movement would have been a defect rather than a
tolerance question.

**`make test` is still BROKEN in this tree and was not used.** The *Full suite command* cell in the
Test Infrastructure table says `make test`; it was written at planning time and is wrong here.
**Every command in this addendum was run as `.venv/bin/python -m pytest`** under the Python 3.11
venv. Recorded here rather than by editing the planning-time row, per this phase's retract-in-place
discipline — the same reason the round-1 addendum gives.

**Each of these guards was WATCHED RED under a mutation of the real committed source**, which is
this phase's standard of evidence. `22-17` M-H (revert `_log_erfc`'s predicate to `if e > 0.0:`) —
**1 distinct test, 5 node ids**, worst 1.5906e-04 relative at x=27.19; M-H-both (additionally
delete `_SMALLEST_NORMAL`) — same 5 node ids, the second hunk inert to pytest but caught by `ruff`
as `F821`. `22-18` M-J (a **TEST-SIDE** mutation reverting `_inert_points()`'s filter) — **2
distinct tests**, one of them a node the old filter GENERATES that demands `_log_erfc` return
`math.log` of a float whose mantissa is already gone; and M-H re-applied contributes **+3 node ids**
at 1.28e+09×, 1.92e+06× and 2.07e+07× over their budgets. Both hunk counts VERIFIED at 1 rather than
inherited from the plan; all restores sha256-identical with `git diff --exit-code` at 0.

---

## Wave 0 Requirements

- [ ] `tests/test_phase22_accountant.py` — V-01 … V-09
- [ ] `tests/test_phase22_dpsgd_ast.py` — V-11
- [ ] `tests/test_phase22_dpsgd.py` — V-12, V-14, V-22
- [ ] `tests/test_phase22_checkpoint.py` — V-15, V-16
- [ ] `tests/test_phase22_fakes.py` — V-18 … V-21 (each RED-then-GREEN, RED output recorded)
- [ ] `tests/test_phase22_wiring.py` — V-23
- [ ] V-25's cross-site adjacency check (own file or a section of the AST file)
- [ ] additions to `tests/test_phase20_prereg.py` — V-10, plus D-11's **both halves**:
      `V4_ARTIFACT_GLOBS` gains `results/phase23_*` **and** a matching
      `_assert_ordering_holds(artifact_glob="results/phase23_*")` call (Phase 21 D-20 — the glob
      addition alone enforces nothing)
- [ ] a committed high-precision reference table as **literal data**, so V-01 never imports
      `mpmath` — **`mpmath` must not become a test dependency** (RPT-03). `22-RESEARCH.md`'s tables
      are that data.

**No framework install needed** — pytest 8.x is already in `[dev]`; `pyproject.toml` stays untouched.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `rng["mps"]` slot actually exercised on Apple Silicon | DPSGD-05 | CI is CPU-only; the slot is `skipif`-gated. D-14 records it as **required-but-unexercised** on purpose — the DP path uses the separately-named `dp_noise_rng` slot, not this one | On an M3 host in the 3.11 venv: `pytest tests/test_phase22_checkpoint.py -x` with MPS available; confirm V-16 runs rather than skips |
| The four positive controls were **watched** failing | DPSGD-04 | The requirement is the *observed* RED, not the final green. A suite that is green today cannot prove a guard ever fired | For each of V-18 … V-21: apply the fake, capture the RED output into the plan's summary, restore, confirm GREEN |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or a Wave 0 dependency — **measured 29/29 across
      `22-01-PLAN.md` … `22-11-PLAN.md`**
- [x] Sampling continuity: no 3 consecutive tasks without an automated verify — trivially held,
      every task carries one
- [x] Wave 0 covers all ❌ MISSING references above — **0 `MISSING` references in any plan**
- [x] No watch-mode flags — **0 occurrences of `--watch` / `--watchAll`**
- [x] Feedback latency < 30 s — plan `22-10` Task 3's budget was tightened from 60 s to 30 s so the
      plan and this row agree
- [x] All four positive controls have their RED output recorded, not just their GREEN —
      **CLOSED 2026-08-26 (ticked by plan 22-16 on plan `22-11`'s record, not on this closure's).**
      `22-11-SUMMARY.md` carries FAKE 1 … FAKE 4 (V-18 … V-21) each applied to the REAL committed
      `src/personacore/privacy/dpsgd.py`, each watched reddening a named test with its assertion
      message captured **verbatim**, each restored to a byte-identical blob (pre/post `sha256`
      equal, `git diff --exit-code` exit 0, all four times) — `12 / 5 / 6 / 10` failed against a
      `78 passed, 2 skipped` baseline, nine detectors producing nine DISTINCT messages. The gap
      closure's own mutations (M-A … M-H, above) are **additional** evidence for V-26 … V-34 and
      are not what ticks this line.
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-08-25
