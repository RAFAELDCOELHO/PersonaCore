---
phase: 22
slug: dp-sgd-core-accountant-and-the-correctness-battery
status: draft
nyquist_compliant: false
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

- [ ] All tasks have `<automated>` verify or a Wave 0 dependency
- [ ] Sampling continuity: no 3 consecutive tasks without an automated verify
- [ ] Wave 0 covers all ❌ MISSING references above
- [ ] No watch-mode flags
- [ ] Feedback latency < 30 s
- [ ] All four positive controls have their RED output recorded, not just their GREEN
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
