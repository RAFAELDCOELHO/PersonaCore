---
phase: 19
slug: selective-memory-erasure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-17
---

# Phase 19 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `19-RESEARCH.md` § Validation Architecture, extended with the locked decisions in
> `19-CONTEXT.md` (D1–D8) and the plan-checker's seven blockers.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest 9.0.3` (verified in `19-RESEARCH.md` § Environment Availability) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` — sha256-pinned as bytes by `tests/test_package.py` (STAT-04) |
| **Quick run command** | `.venv/bin/python -m pytest -q tests/test_phase19_erasure.py tests/test_phase16_prereg.py tests/test_package.py` |
| **Full suite command** | `make test` — 727 passed / 1 skipped / 728 collected in ~154 s (`18-VERIFICATION.md:131-133`) |
| **The one skip** | `test_train_loop.py::test_amp_fp16_smoke` — needs CUDA; unrelated |
| **Constraint** | Every test CPU-only and GPU-free. No test may require MPS or a 278 MB checkpoint load. The measurement RUNS need MPS; their tests do not. |
| **New dependencies** | **Zero.** `pyproject.toml` is byte-identical at v3.0 close (STAT-04), sha256-enforced. |

---

## Sampling Rate

- **After every task commit:** `.venv/bin/python -m pytest -q tests/test_phase19_erasure.py tests/test_phase16_prereg.py tests/test_package.py` (~seconds)
- **After every wave:** `make test` (full suite) plus `.venv/bin/ruff check . && .venv/bin/ruff format --check .`
- **Phase gate:** full suite green before `/gsd:verify-work`, **plus** every guard watched RED by
  deliberate mutation and restored byte-identically — the standing practice (`STATE.md:157,203`) and
  the reason Phase 15 caught a guard nobody had seen fail.
- **Max feedback latency:** ~30 s for the quick run.

> The ancestry guards are the one gate that can only be satisfied by having committed in the right
> order. They cannot be repaired after the fact. They are phase gates, not task gates — which is why
> waves 1–6 commit zero `results/phase19_*` artifacts and 19-07 is a blocking human read.

---

## Requirements → Test Map

| Req | Behaviour | Type | Command | Exists | Plan |
|-----|-----------|------|---------|--------|------|
| ERASE-01 | The Phase 19 pin precedes every `results/phase19_*` first-add | integration (git) | `pytest tests/test_phase16_prereg.py -k phase19_prereg` | ⚠️ extend `:54` + new twin | 19-01 |
| ERASE-01 | Zeroing a rank-1 component leaves the artifact rank-8-writable; `load_adapter_weights` accepts it | unit, CPU | `pytest tests/test_phase19_erasure.py -k artifact` | ❌ W0 | 19-01 |
| ERASE-01 | Full-index ablation reproduces `adapter_disabled` at max abs diff exactly 0.0 | unit, CPU | `pytest tests/test_phase19_erasure.py -k bit_identity` | ❌ W0 | 19-01 |
| ERASE-01 / D7 | `select_target_fact` reproduces the pinned `TARGET_FACT_ID` from `results/phase18_arm_adapter-on.json`; both tie-breaks resolve deterministically | unit | `pytest tests/test_phase19_erasure.py -k target` | ❌ W0 | 19-02 |
| STAT-01 / D5 | `N_TARGET_QUESTIONS` is derived (13+14) from the fixture; a duplicated `(fact_id, seed_index)` raises; no literal 27 on the derivation path | unit | `pytest tests/test_phase19_erasure.py -k denominator` | ❌ W0 | 19-02 |
| ERASE-01 / D2 | `lock_erasure_floor(x) <= literal_phase14_floor(x)` across the swept domain — the mirror is never looser | unit | `pytest tests/test_phase19_erasure.py -k floor` | ❌ W0 | 19-03 |
| ERASE-01 / D2 | Scoped to `floor_branch(x) == "discount"`: `math.floor(x*0.60*10000) <= x*0.60*10000` — exact, integer-vs-float, no tolerance. The unscoped `lock(x) <= x*0.60` is NOT asserted (red at 161/1001 by design, the clamp binds below the crossover). The stored value may exceed the grid point by ≤1 ulp and a test pins that bound (W1) | unit | `pytest tests/test_phase19_erasure.py -k floor_rounding` | ❌ W0 | 19-03 |
| ERASE-01 | `assert_erasure_floor_reachable` runs at module scope; `ERASURE_FLOOR_MIN` is the unrounded `wilson_upper_bound(0, 27)`; a downward ulp mutation goes RED at import | unit | `pytest tests/test_phase19_erasure.py -k reachab` | ❌ W0 | 19-03 |
| ERASE-01 / D3 | `dialogue_cap(x)` equals `erasure_gate`'s own arithmetic across a swept range; no baseline is retyped | unit | `pytest tests/test_phase19_erasure.py -k dialogue` | ❌ W0 | 19-04 |
| ERASE-01 / D4 | `nontarget_deltas` returns exactly seven per-fact rows with denominators; no pooled path exists; empty raises | unit | `pytest tests/test_phase19_erasure.py -k nontarget` | ❌ W0 | 19-04 |
| ERASE-01 / D4 | `nontarget_noise_floor` is the ONE reduction to the gate's scalar, and swapping `max`→`mean` changes it on a synthetic spread (B3) | unit | `pytest tests/test_phase19_erasure.py -k reduction` | ❌ W0 | 19-04 |
| STAT-06 / B5 | `SOFT_TIER_DESCRIPTIVE_READ` names both soft facts; they are scored post-erasure, published DESCRIPTIVE, and reach no gate | unit + in-run | `pytest tests/test_phase19_erasure.py -k soft_tier`; `19-12` verify asserts `len(r['soft_descriptive'])==2` | ❌ W0 | 19-04 / 19-10 / 19-12 |
| ERASE-01 | `zero_results_have_nll` is False with a named `fact_id` on a missing/partial/non-finite record, True on a complete one; eight slots required | unit | `pytest tests/test_phase19_erasure.py -k zero_nll` | ❌ W0 | 19-04 |
| STAT-06 | ΔW cosine / Fisher overlap reach no gate — no `sign_test_exact`, no `holm`, no threshold `Compare` on that path; no dangling `DESCRIPTIVE_ONLY_FUNCTIONS` entry | static (AST) | `pytest tests/test_phase19_erasure.py -k descriptive` | ❌ W0 | 19-05, 19-14 |
| STAT-05 | `erasure_succeeded` is imported and called exactly once outside tests; no v2.0 baseline appears as a numeric literal in the driver | static (AST) | `pytest tests/test_phase19_erasure.py -k verdict` | ❌ W0 | 19-05 |
| ERASE-01 | Post-erasure corpus digest / mask digest / K / rungs / stop ids / temperature / top-p / stride match Phase 18's committed config; a missing key raises | unit | `pytest tests/test_phase19_erasure.py -k parity` | ❌ W0 | 19-05 |
| ERASE-01 | Both ship-decision marker halves name Phase 19; neither contains "Phase 18"; `render_report` emits exactly one `## Verdict` and one pending line | unit | `pytest tests/test_phase19_docs.py` | ✅ `f8441ec` (extend) | 19-05, 19-16 |
| ERASE-02 | The retrain arm's fact list is `LOCKED_FACTS + SOFT_TIER_FACTS` minus exactly one; no recipe constant is redeclared; an unknown `fact_id` raises | unit, CPU | `pytest tests/test_phase19_erasure.py -k retrain_arm` | ❌ W0 | 19-06 |
| ERASE-01 | `run_bit_identity_control` accepts `adapter_path=`; the default keeps every existing call site behaviourally identical (B2) | unit | `pytest tests/test_phase14_scoring.py tests/test_lora_inject.py -x` | ⚠️ widen `phase14_recall.py:1480` | 19-06 |
| ERASE-01 | Every `draw_all` call site asserts in-prompt, in place or via a named indirection that exists | static (AST) | `pytest tests/test_phase14_scoring.py -k draw_all` | ✅ `:579` (extend) | 19-06 |
| ATK-01 | No network import reachable from `scripts/phase19_erasure.py` (W3) | static (AST) | `pytest tests/test_phase18_corpus.py::test_no_network_imports` | ✅ (widen scan set) | 19-06 |
| ERASE-01 | A calibration corpus builds over `CALIBRATION_POOL` with derived per-tier denominators; exclusions carry family ids; `6 ≤ \|R\| ≤ 8` holds and raises outside | unit | `pytest tests/test_phase19_erasure.py -k calibration` | ❌ W0 | 19-06 |
| ERASE-01 | `CALIBRATION_TARGET_SELECTION_RULE` is blind: it reads no Phase 18 recall and no Phase 19 result (B4) | static + unit | `pytest tests/test_phase19_erasure.py -k calibration_rule` | ❌ W0 | 19-06 |
| ERASE-01 | The floor file precedes every TARGET artifact; the four excluded artifacts are enumerated by name (W4) | integration (git) | `pytest tests/test_phase16_prereg.py -k phase19_floor` | ❌ W0 | 19-11 |
| ERASE-01 | The MEASURED floor is clearable by 0 successes over `N_TARGET_QUESTIONS`; a downward ulp mutation goes RED | unit | `pytest tests/test_phase19_erasure.py -k measured_floor` | ❌ W0 | 19-11 |
| STAT-01 | Every published `n` is a question count, proved against a derived quantity; the scored denominator equals `N_TARGET_QUESTIONS` (W2) | unit + in-run assert | `pytest -k denominator`; 19-12 verify | ❌ W0 | 19-02, 19-12 |
| STAT-02 | Every proportion carries denominator + Wilson + `3/n` at zero; no bare `0%` in any artifact | unit + grep | `pytest -k reporting`; `grep -rn '0%' results/phase19_*` → 0 hits | ❌ W0 | 19-04, 19-15 |
| STAT-04 | `pyproject.toml` byte-identical | unit | `pytest tests/test_package.py -x` | ✅ exists | all |

---

## Wave 0 Gaps

- [ ] `tests/test_phase19_erasure.py` — the whole table above except the four ✅ rows
- [ ] `tests/test_phase16_prereg.py` — `V3_ARTIFACT_GLOBS += "results/phase19_*"` (`:54`),
      `test_phase19_prereg_is_frozen_before_every_phase19_result`, and the floor-file guard
- [ ] `tests/test_phase14_scoring.py` — `DRAW_ALL_ASSERTED_BY` entry if a named indirection is used
- [ ] `tests/test_phase18_corpus.py` — widen `test_no_network_imports`' scanned file set
- [ ] `tests/test_phase19_docs.py` — extend for the Phase 19 marker pair (the additivity proof already
      exists at `f8441ec`)
- [ ] Framework install: **none** — pytest 9.0.3 is present

---

## Guards Watched RED (mandatory, per-plan)

Each is mutated deliberately, observed RED, then restored **byte-identically**. Recorded in the
owning plan's SUMMARY.

| Guard | Mutation | Plan |
|---|---|---|
| Ablation ΔW==0 | zero only `lora_B[:,j]`, leave `lora_A[j,:]` | 19-01 |
| Module-scope reachability | `ERASURE_FLOOR_MIN = 0.0` | 19-03 |
| Not-gated (AST) | insert `if cosine > 0.5:` on the representational path | 19-05, 19-14 |
| Single verdict path (AST) | add a second `erasure_succeeded(` call | 19-05 |
| Measured-floor reachability | `TARGET_FLOOR` down one ulp | 19-11 |

---

## Ordering Assertions (not repairable after the fact)

| Check | Command | When |
|---|---|---|
| No Phase 19 artifact before the pin closes | `test -z "$(git ls-files 'results/phase19_*')"` | every plan 19-01…19-07 |
| The ancestry guard stops being vacuous | `test_phase19_prereg_is_frozen_before_every_phase19_result` reports `checked > 0` | 19-08 onward |
| The floor guard stops being vacuous | `test_phase19_floor_precedes_every_target_artifact` reports `checked > 0` | 19-12 onward |
| The frozen Phase 18 driver is untouched | `git log --format=%H -- scripts/phase18_extraction.py \| wc -l` unchanged | every plan |
| `23a830c` is unamended | `git log --format=%H -- scripts/erasure_gate.py \| wc -l` == 1 | 19-15, 19-16 |
| No commit to the pin after the first artifact | `git log --format=%H -- scripts/phase19_erasure.py` all ancestors of every artifact's earliest add | 19-08 onward |
