---
phase: 15
slug: figures-writeup
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-02
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `15-RESEARCH.md` → `## Validation Architecture`.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `pyproject.toml` → `[tool.pytest.ini_options]` (`testpaths = ["tests"]`, `pythonpath = ["."]`) |
| **Quick run command** | `.venv/bin/pytest -q tests/test_phase15_plots.py tests/test_phase15_stats.py tests/test_phase15_docs.py` |
| **Full suite command** | `.venv/bin/pytest -q` (or `make test`) |
| **Estimated runtime** | ~10 s quick · ~120 s full (baseline: 392 passed, 1 skipped, 119.6 s) |
| **Environment** | CPU-only, GPU-free, Python 3.11 venv; CI installs `.[cpu,dev,demo]` — matplotlib ships via `demo` |

---

## Sampling Rate

- **After every task commit:** Run the quick command above (< 10 s expected)
- **After every plan wave:** Run `.venv/bin/pytest -q` **and** `make lint`
- **Before `/gsd:verify-work`:** Full suite green (≥ 392 passed, allowing for new tests) + `make lint`
  clean + both PNGs and the D-05 JSON committed
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

Task IDs are assigned by the planner; the behavior→test contract below is fixed by research and
must be preserved when tasks are numbered.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | 0 | D-10 / D-12 | — | N/A | unit (known-answer) | `pytest tests/test_phase15_stats.py::test_spearman_known_answers -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | D-12 | — | N/A | unit (determinism) | `pytest tests/test_phase15_stats.py::test_seeded_results_are_reproducible -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | D-12 | — | N/A | unit (behavioral) | `pytest tests/test_phase15_stats.py::test_ci_behavior_on_null_and_signal -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 0 | D-11 | — | N/A | unit (gate logic) | `pytest tests/test_phase15_stats.py::test_gate_rule -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 1 | D-05 / D-06 | T-15-01 | Artifact schema complete; every block carries regime/param_count/training_budget | unit (schema) | `pytest tests/test_phase15_plots.py::test_artifact_schema -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 1 | D-08 | T-15-01 | Extraction reproduces the committed JSON exactly | integration (`skipif` on 6 checkpoints) | `pytest tests/test_phase15_plots.py::test_extraction_reproduces_the_committed_artifact -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 2 | VIZ-02 | — | N/A | unit (tmp_path smoke) | `pytest tests/test_phase15_plots.py::test_plot_functions_write_pngs -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 2 | VIZ-03 | — | N/A | unit (tmp_path smoke) | `pytest tests/test_phase15_plots.py::test_plot_functions_write_pngs -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 2 | D-01 | — | N/A | unit | `pytest tests/test_phase15_plots.py::test_ab_panels_share_one_norm -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 2 | D-02 | — | N/A | unit | `pytest tests/test_phase15_plots.py::test_shared_range_is_full_data_range -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 2 | D-02 / D-18 | — | N/A | unit | `pytest tests/test_phase15_plots.py::test_vmax_driver_matches_argmax -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 2 | D-07 | T-15-02 | Plotting module has no code path that opens a `.pt` file | structural (AST + subprocess) | `pytest tests/test_phase15_plots.py::test_plotting_module_never_opens_a_checkpoint -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 3 | D-15 | — | N/A | doc integrity | `pytest tests/test_phase15_docs.py::test_limitations_quotes_are_verbatim -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 3 | D-16 | — | N/A | doc integrity | `pytest tests/test_phase15_docs.py::test_headline_numbers_match_sources -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 3 | D-17 | — | N/A | doc integrity | `pytest tests/test_phase15_docs.py::test_verdict_section_is_dated_and_separated -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | 3 | DOC-02 | — | N/A | regression | `.venv/bin/pytest -q` | ✅ exists | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase15_stats.py` — covers D-10 / D-11 / D-12. **Must land in the same commit as
      `scripts/phase15_stats.py`, before any artifact exists** (D-09 pre-registration boundary).
- [ ] `tests/test_phase15_plots.py` — covers VIZ-02 / VIZ-03 / D-01 / D-02 / D-05 / D-06 / D-07 / D-08.
- [ ] `tests/test_phase15_docs.py` — covers D-15 / D-16 / D-17.
- [ ] No framework install needed. No `conftest.py` change needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Extraction correctness | D-08 / VIZ-02 / VIZ-03 | Needs six gitignored checkpoints (~914 MB); cannot run in CPU-only CI. Skips cleanly. | Locally, with all six checkpoints present: run the extraction script, then `pytest tests/test_phase15_plots.py::test_extraction_reproduces_the_committed_artifact` — must match the committed JSON byte-for-byte. Re-running against a **future** checkpoint requires a fresh manual run producing a fresh committed artifact, not a test that stays green while checking nothing. |
| Whether the committed numbers are the RIGHT numbers | VIZ-02 / VIZ-03 | The suite proves the artifact→figure path is faithful and the schema complete; it cannot prove the artifact describes the intended checkpoints. | Human review of the `git_sha` / `step` / `val_loss` fingerprints recorded in each artifact block. Specifically confirm the adapter block's W₀ is `convbase_best.pt` (fingerprint `04e724c6…`, step 4000), **not** `best.pt` — see RESEARCH.md Pitfall 1. |
| Figure legibility under the shared scale | D-01 / D-02 | "Flatness is a finding" is a judgment about whether the rendered PNG communicates; not machine-checkable. | Open both committed PNGs. Confirm the caption names the `vmax` driver and states which panels share a scale and why the Fisher panel does not. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
