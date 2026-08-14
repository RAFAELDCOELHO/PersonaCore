---
phase: 17
slug: multi-persona-isolation-matrix
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-14
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `17-RESEARCH.md` §Validation Architecture. Where RESEARCH.md and the working tree
> disagreed, the **measurement taken on 2026-08-14 wins** and the discrepancy is recorded below.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest 9.0.3` (pinned `pytest~=9.0`, `pyproject.toml:19`) |
| **Config file** | `pyproject.toml` → `[tool.pytest.ini_options]`, `testpaths = ["tests"]`, `pythonpath = ["."]` |
| **Quick run command** | `.venv/bin/pytest -q tests/test_phase17_*.py` |
| **Full suite command** | `make test` (i.e. `pytest -q`) |
| **Estimated runtime** | full suite **~122 s**; quick run seconds (CPU) |
| **Constraint** | **CPU-only, GPU-free, no checkpoint I/O, no model load, no generation** — the register every Phase 14/15/16 test file follows. Drivers are loaded with `importlib.util.spec_from_file_location` so `main()` never runs. |

> **Baseline correction (2026-08-14):** `17-RESEARCH.md` §Sampling rate cites "407 passed / 1 skipped
> in ~117 s". Measured on the current tree: **579 passed, 1 skipped, 122.42 s**. Use 579/1 as the
> pre-phase baseline — a Wave-0 run reporting 407 means tests were *lost*, not that the baseline
> was met.

---

## Sampling Rate

- **After every task commit:** `.venv/bin/pytest -q tests/test_phase17_*.py`
- **After every plan wave:** `make test` (full suite)
- **Before `/gsd:verify-work`:** full suite green **plus `make lint`**
- **Max feedback latency:** ~122 s (full suite); seconds for the phase-17 quick run

---

## Per-Task Verification Map

Task IDs are assigned by `/gsd:plan-phase` and backfilled into the `Task ID` / `Plan` / `Wave`
columns as plans land. The requirement → behavior → command mapping is fixed **now, before
planning**, so no plan can invent its own success criterion.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | ISO-01 | — | N/A | unit | `pytest tests/test_phase17_personas.py -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | ISO-01 | — | Every minted value ≤ 8 tokens, round-trips exactly | unit | `pytest tests/test_phase17_personas.py::test_census -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | ISO-01 | Repudiation | Training refuses without a recorded GO/ADAPT verdict | unit | `pytest tests/test_phase17_personas.py::test_verdict_blocks -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | ISO-02 | — | N/A | unit | `pytest tests/test_phase17_stats.py::test_sweeps_are_pairable -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | ISO-02 | — | N/A | unit | `pytest tests/test_phase17_scoring.py::test_slot_regrouping -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | ISO-03 | — | N/A | unit | `pytest tests/test_phase17_stats.py::test_base_column_is_a_control -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | ISO-04 | Spoofing | Silent adapter substitution cannot pass undetected | unit (tiny GPT, CPU) | `pytest tests/test_phase17_scoring.py::test_swap_canary_bites -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | ISO-04 | Spoofing | `--report` refuses when two sweep digests match | unit | `pytest tests/test_phase17_stats.py::test_report_refuses_identical_digests -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | ISO-05 | — | N/A | static AST | `pytest tests/test_phase17_stats.py::test_replication_is_not_gated -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | ISO-06 | Tampering | Consumers inject at the artifact's own `lora_config` | static AST | `pytest tests/test_lora_inject.py -x` (extend) | ✅ partial — `test_load_adapter_weights_refuses_wrong_alpha` | ⬜ pending |
| TBD | TBD | TBD | ISO-07 | — | N/A | static source scan | `pytest tests/test_phase17_stats.py::test_no_phase14_thresholds -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | STAT-01 | — | Signs computed on the question rate, not the draw rate | unit | `pytest tests/test_phase17_stats.py::test_signs_use_the_question_unit -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | STAT-02 | — | No bare `0%`; every zero cell carries denominator + bound | unit (writer) | `pytest tests/test_phase17_stats.py::test_no_bare_zero_percent -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | STAT-03 | — | Family is exactly 6; nothing else reaches `holm` | unit + static AST | `pytest tests/test_phase17_stats.py -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | STAT-04 | — | `pyproject.toml` byte-identical; stdlib + repo imports only | static AST + file hash | `pytest tests/test_phase17_stats.py::test_no_new_dependencies -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | STAT-05 | Repudiation | Pre-registration commit precedes every results artifact | static + git | `pytest tests/test_phase17_stats.py::test_prereg_precedes_results -x` | ✅ pattern — `tests/test_phase16_prereg.py` | ⬜ pending |
| TBD | TBD | TBD | STAT-06 | — | No aggregate 9-cell rate computed or printed | static AST | `pytest tests/test_phase17_stats.py::test_no_nine_cell_aggregate -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | SC3 (ISO-02) | — | `inspect.signature(score_completion)` carries no `(i, j)` | unit + static AST | `pytest tests/test_phase17_scoring.py::test_scorer_is_cell_blind -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | D-10 | — | All-fail branch text committed; writer emits it below six | unit (writer) | `pytest tests/test_phase17_stats.py::test_all_fail_branch -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | D-18 | — | Gate clears only on **all six** Holm rejections | unit | `pytest tests/test_phase17_stats.py::test_gate_requires_all_six -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | D-19 | — | `worst_pair` tie-break deterministic at the all-zero tie | unit | `pytest tests/test_phase17_stats.py::test_worst_pair_tiebreak -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | D-21 | — | Phase-17 twin of the six-pairs gate scan | static AST | `pytest tests/test_phase17_stats.py::test_nothing_outside_the_six_pairs -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase17_personas.py` — minting filters, token census (≤ 8 tokens/value), GO/ADAPT verdict gate (ISO-01)
- [ ] `tests/test_phase17_scoring.py` — cell-blindness, slot regrouping, swap canary (ISO-02, ISO-04, SC3)
- [ ] `tests/test_phase17_stats.py` — family closure, question unit, thresholds, dependencies, aggregate ban (STAT-01…06, ISO-03/05/07, D-10/18/19/21)
- [ ] No framework install needed — `pytest 9.0.3` is already in `[dev]` and `.venv` is live

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Human GO / ADAPT verdict on the minted persona values | ISO-01 | The judgment is semantic proximity on quoted base completions — precisely what exact-match cannot see (Phase 14's own reasoning). Only the **judgment** is manual; its **enforcement** is automated. | Run the `scripts/phase14_factset_gate.py` guessability + census instrument (imported, not copied), read the quoted base completions, record GO or ADAPT in the Phase 17 report. `_require_go_verdict` refuses to train on STOP/PENDING. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 130 s
- [ ] Full-suite baseline is **579 passed / 1 skipped** before Wave 0 adds tests
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
