---
phase: 23
slug: cost-calibration-the-0-diagnostic-and-budget-pre-registratio
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-26
derived_from: 23-RESEARCH.md § Validation Architecture (commit 1da1d3f)
---

# Phase 23 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `23-RESEARCH.md` § Validation Architecture. The reasoning behind each row lives there;
> this file is the execution contract.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest` 8.x (`[tool.pytest.ini_options]`, `pyproject.toml:24-26`) |
| **Config file** | `pyproject.toml` — `testpaths = ["tests"]`, `pythonpath = ["."]` |
| **Quick run command** | `.venv/bin/python -m pytest tests/test_phase23_*.py -q` |
| **Full suite command** | `make test` → `pytest -q` |
| **Current suite size** | 1,339 tests collected (measured 2026-08-26) |
| **Estimated runtime** | quick < 30 s; full suite dominated by the MPS legs |
| **Lint** | `make lint` → `ruff check . && ruff format --check .` |
| **CI** | `.github/workflows/ci.yml` — ubuntu-latest, Python 3.11, `pip install -e ".[cpu,dev,demo]"`. **CPU-only: every MPS leg MUST be `skipif`-gated or CI goes red.** |
| **MPS gating precedent** | module-level `pytestmark` in `tests/test_mps_smoke.py`; per-case register at `tests/test_phase22_checkpoint.py:671` |

---

## Sampling Rate

- **After every task commit:** `.venv/bin/python -m pytest tests/test_phase23_*.py -q` (target < 30 s).
  **Plus** `pytest tests/test_phase20_prereg.py -k import_graph -q` on any task touching
  `scripts/mitigation_*.py` — that guard *is* the SC3 gate.
- **After every plan wave:** `make test` (full 1,339+) **on the M3, where the MPS legs actually run** —
  a CPU-only pass skips exactly the tests D-02 exists to produce. Plus `make lint`.
- **Before `/gsd:verify-work` (phase gate):** full suite green on the M3 with **zero skips among the
  MPS-gated Phase-23 tests** — record the skip count explicitly, because a green run that skipped the
  venue tests is the precise failure mode D-02 names. Plus
  `git diff --exit-code -- scripts/mitigation_accountant.py scripts/mitigation_gate.py` returning 0
  (both are FROZEN; D-09 forbids editing the gate).
- **Max feedback latency:** 30 s per task; one full-suite M3 run per wave.

---

## Per-Requirement Verification Map

| Req / Decision | Behavior | Test Type | Automated Command | File Exists |
|---|---|---|---|---|
| **DPSGD-06** | D-16 generator invariant on MPS at σ=0: `torch.normal(std=0.0)` returns exact zeros **and** advances the 44-byte state | unit (MPS, skipif) | `pytest tests/test_phase23_mps_venue.py::test_sigma_zero_advances_the_mps_generator -x` | ❌ W0 |
| **DPSGD-06** | σ=0 is the DP arm's **first** executed run — no noised `results/phase23_*` record precedes it in git | structural (ancestry) | `pytest tests/test_phase23_prereg.py::test_sigma_zero_precedes_every_noised_point -x` | ❌ W0 |
| **DPSGD-06 / D-04** | Within floor ⇒ proceed; outside ⇒ HALT with zero noised points | unit (both branches, RED watched) | `pytest tests/test_phase23_prereg.py::test_floor_breach_halts_the_sweep -x` | ❌ W0 |
| **D-02** | V-15 kill→resume ε bit-identity, parametrized `["cpu","mps"]` | integration (MPS skipif) | `pytest tests/test_phase22_checkpoint.py::test_resume_epsilon_bit_identical -x` | ✅ **needs device parametrization** |
| **D-02** | Four DPSGD-04 fakes, runtime halves re-watched RED on MPS | unit ×4 (MPS skipif) | `pytest tests/test_phase22_fakes.py -k "fake_" -x` | ✅ **needs device parametrization** |
| **D-02** | AST halves recorded as device-invariant, not silently skipped | structural (ledger) | `pytest tests/test_phase22_fakes.py::test_fakes_ledger_is_recorded -x` | ✅ **ledger needs a device column** |
| **CAL-01** | Training leg measured on the DP path with the seam active; record carries device, torch version, git_sha, step count, denominators | structural (schema) | `pytest tests/test_phase23_cost.py::test_training_cost_record_is_complete -x` | ❌ W0 |
| **CAL-01** | A cost record missing any provenance key is REFUSED, not defaulted | unit (refusal) | `pytest tests/test_phase23_cost.py::test_incomplete_cost_record_is_refused -x` | ❌ W0 |
| **CAL-01 / D-10** | The "~1,010×" claim is corrected by dated additive continuation; original left standing; sentence re-scoped to the non-DP arm | structural (retract-in-place) | `pytest tests/test_phase23_cost.py::test_cost_claim_correction_is_additive -x` | ❌ W0 |
| **CAL-05** | Record carries `h_per_point_floor` **and** `h_per_point_ceiling` as distinct required keys — no bare mean field exists | structural | `pytest tests/test_phase23_cost.py::test_no_bare_mean_field_exists -x` | ❌ W0 |
| **CAL-05** | Sizing refuses a floor-only record; Z is sized against the **ceiling** | unit (refusal + positive) | `pytest tests/test_phase23_budget.py::test_sizing_refuses_a_floor_only_record -x` | ❌ W0 |
| **CAL-02 / SC3** | Gate structurally unable to import the budget — **static** | structural (AST) | `pytest tests/test_phase20_prereg.py -k import_graph -x` | ✅ **exists and bites** (watched RED, research §R2.2) |
| **CAL-02 / SC3 / D-09** | …and **transitively**, out of process — closes the `gate → erasure_gate → budget` route | structural (subprocess) | `pytest tests/test_phase23_budget.py::test_gate_does_not_transitively_load_the_budget -x` | ❌ W0 |
| **CAL-02** | `mitigation_budget.py` holds literal assignments only — no rule, no estimator, no import | structural (AST) | `pytest tests/test_phase23_budget.py::test_budget_holds_only_literal_constants -x` | ❌ W0 |
| **CAL-02** | Every pinned Z constant **re-derives** from its committed artifact on every suite run | unit (re-derivation) | `pytest tests/test_phase23_budget.py::test_budget_constants_re_derive -x` | ❌ W0 |
| **CAL-02** | Selected K is a member of the FROZEN `mitigation_gate.K_RUNGS` and satisfies the ratchet | unit | `pytest tests/test_phase23_budget.py::test_selected_k_is_a_ratcheted_rung -x` | ❌ W0 |
| **CAL-03 / D-05** | ε at n=8 vs n=64 at fixed σ is **bit-identical** under `==`, never a tolerance | unit | `pytest tests/test_phase23_cal03.py::test_epsilon_is_bit_identical_across_capacity -x` | ❌ W0 |
| **CAL-03 / D-05** | Composed step count T asserted equal **directly**, read from `_count_composed_steps`, not `ckpt["step"]` | unit | `pytest tests/test_phase23_cal03.py::test_composed_step_count_is_equal_across_capacity -x` | ❌ W0 |
| **CAL-03 / D-05** | A synthetic N-leak into T is **WATCHED** reddening both assertions | unit (positive control) | `pytest tests/test_phase23_cal03.py::test_an_n_leak_into_t_is_detected -x` | ❌ W0 |
| **CAL-03 / D-06** | Falsified ⇒ n=64 leg absent from the committed budget, withdrawing measurement recorded | structural | `pytest tests/test_phase23_budget.py::test_n64_leg_absent_when_cal03_falsified -x` | ❌ W0 |
| **CTRL-03 / D-08** | Never-taught provenance names `arm="never-taught"` with ≥ `EXTRACTION_FLOOR_MIN_SEEDS` distinct seeds (FROZEN gate's requirement) | structural | `pytest tests/test_phase23_ctrl.py::test_never_taught_provenance_satisfies_the_gate -x` | ❌ W0 |
| **CTRL-03** | Trained once (one scheduling), consumed twice — one record, two named consumers, no second training call | structural | `pytest tests/test_phase23_ctrl.py::test_never_taught_is_trained_once -x` | ❌ W0 |
| **D-03** | Control record's first git add **strictly precedes** the σ=0 record's | structural (ancestry) | `pytest tests/test_phase23_prereg.py::test_control_precedes_sigma_zero -x` | ❌ W0 |
| **D-03** | `scripts/mitigation_accountant.py` byte-unchanged across the phase | structural | `git diff --exit-code -- scripts/mitigation_accountant.py` + `pytest tests/test_phase20_prereg.py -k phase23_result -x` | ✅ guard exists (`:332`), currently vacuous |
| **D-07** | `train_arm(resume_from=None)` byte-identical to today at all 8 call sites | unit (inertness) | `pytest tests/test_phase23_resume.py::test_resume_from_none_is_inert -x` | ❌ W0 |
| **D-07** | A resume finds checkpoint/csv/bins present and does NOT refuse; the adapter still refuses | unit (4 targets) | `pytest tests/test_phase23_resume.py::test_refuse_if_exists_is_resume_aware -x` | ❌ W0 |
| **D-07** | `resume_from` naming another arm's checkpoint is REFUSED | unit (refusal) | `pytest tests/test_phase23_resume.py::test_cross_arm_resume_is_refused -x` | ❌ W0 |
| **D-07** | Production kill→resume through `train_arm` reproduces bit-identical ε **on MPS** | integration (MPS skipif) | `pytest tests/test_phase23_resume.py::test_production_resume_epsilon_bit_identical -x` | ❌ W0 |

*Status legend: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase23_mps_venue.py` — D-02 device-parametrization harness + the σ=0 generator-advance guard (DPSGD-06's keystone)
- [ ] Device-parametrize `tests/test_phase22_dpsgd.py::_model`, `tests/test_phase22_fakes.py::_record`, `tests/test_phase22_checkpoint.py::_next_draw` — exhaustive touchpoint list in research §R1.7
- [ ] `tests/test_phase23_prereg.py` — ordering/ancestry guards (D-03, D-04, DPSGD-06)
- [ ] `tests/test_phase23_cost.py` — cost-record schema + refusals + the D-10 correction (CAL-01, CAL-05)
- [ ] `tests/test_phase23_budget.py` — budget structure, re-derivation, transitive import guard, K ratchet (CAL-02, D-06, D-09)
- [ ] `tests/test_phase23_cal03.py` — ε/T bit-identity + the watched N-leak positive control (CAL-03)
- [ ] `tests/test_phase23_ctrl.py` — never-taught provenance and single-training (CTRL-03, D-08)
- [ ] `tests/test_phase23_resume.py` — the D-07 seam, its inertness, its refusals, its MPS production leg
- [ ] `results/phase23_*` naming convention — anything outside this prefix falls outside the ancestry guard at `tests/test_phase20_prereg.py:332`
- [ ] Framework install: **none needed** — pytest 8.x, ruff and the venv are present and green (1,339 collected)

---

## Two Failure Modes This Contract Exists To Catch

1. **A green CPU run that skipped every MPS leg.** D-02's entire purpose is venue transfer; a suite
   that passes because the venue tests were `skipif`-ed is the failure, not the pass. Hence the
   explicit skip-count recording at the phase gate.
2. **A guard nobody has watched fail.** Every new structural guard here needs a watched RED — the
   N-leak positive control, the floor-breach halt branch, the transitive import probe. Phase 20's SC3
   guard was watched RED against a scratch module during research; the new ones inherit that standard.
