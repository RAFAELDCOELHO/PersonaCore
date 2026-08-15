---
phase: 18
slug: black-box-adversarial-extraction-audit
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-15
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `18-RESEARCH.md` § Validation Architecture, extended with D-28 … D-31.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest 9.0.3` (verified this session: `python -c "import pytest"`) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]`, `testpaths = ["tests"]` |
| **Quick run command** | `.venv/bin/pytest -q tests/test_phase18_*.py` |
| **Full suite command** | `.venv/bin/pytest -q` — **652 tests collect today** (verified: `pytest -q --collect-only` → `652 tests collected in 2.52s`) |
| **Estimated runtime** | ~3 s collection; full suite seconds-scale (CPU-only) |
| **Constraint** | CPU-only and GPU-free. No test may require MPS/CUDA or a checkpoint load. |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/pytest -q tests/test_phase18_*.py`
- **After every plan wave:** Run `.venv/bin/pytest -q` (full 652+ suite) plus
  `.venv/bin/ruff check . && .venv/bin/ruff format --check .`
- **Before `/gsd:verify-work`:** Full suite green **and** the ancestry guard green
- **Max feedback latency:** ~30 seconds

> The ancestry guard is the one gate that can only be satisfied by having committed in the right
> order — it cannot be repaired after the fact. It is a phase gate, not a task gate.

---

## Per-Task Verification Map

| Req | Behaviour | Test Type | Automated Command | File Exists |
|-----|-----------|-----------|-------------------|-------------|
| ATK-01 | Corpus re-derives byte-identical from pinned templates alone (D-07) | unit | `pytest tests/test_phase18_corpus.py::test_corpus_rederives_byte_identical -x` | ❌ W0 |
| ATK-01 | No external network/API reachable from the driver (AST scan `requests`/`urllib`/`http`) | unit | `pytest tests/test_phase18_corpus.py::test_no_network_imports -x` | ❌ W0 |
| ATK-01 / D-16 | `assert_no_value_in_prompt` covers the question portion of **every** family incl. A2 | unit | `pytest tests/test_phase18_corpus.py::test_strict_guard_covers_every_family -x` | ❌ W0 |
| ATK-01 / D-16 | A2 tail bounded: `1 ≤ realized ≤ ⌊ids/4⌋` on the final id list, per slot | unit | `pytest tests/test_phase18_corpus.py::test_a2_injection_within_budget -x` | ❌ W0 |
| ATK-01 / D-19 | Round-trip guard is **RED** on a mid-UTF-8 split — asserts `SystemExit`, not `UnicodeDecodeError` | unit | `pytest tests/test_phase18_corpus.py::test_roundtrip_guard_is_red_on_mid_utf8 -x` | ❌ W0 |
| ATK-01 / D-03 | Static scan: `scripts/phase18_*.py` holds no fact value in any string **or docstring** | unit | `pytest tests/test_phase18_prereg.py::test_no_fact_values_in_phase18_modules -x` | ❌ W0 |
| ATK-01 / D-08 | `PERSONA_ALLOWLIST` hard equality holds with the new third entry | unit | `pytest tests/test_phase14_scoring.py -k persona_argument -x` | ✅ `:422` |
| ATK-01 / D-11 | Corpus schema carries `family, dose, fact_id, slot, seed_index`; `family == "reserved"` for exactly the 32 flagged probes | unit | `pytest tests/test_phase18_corpus.py::test_schema_and_reserved_family -x` | ❌ W0 |
| ATK-03 / D-09 | `draw_all` prefix stability — draws 0..8 at `n_samples=63` byte-identical to `n_samples=8` | unit | `pytest tests/test_phase18_draws.py::test_prefix_is_budget_independent -x` | ❌ W0 |
| ATK-03 / D-06 | `question_seed(index*K) == SEED + index*K`; 216×64 strided seed set has zero collisions | unit | `pytest tests/test_phase18_draws.py::test_strided_seeds_are_disjoint -x` | ❌ W0 |
| ATK-03 / D-01 | Family-zero comparison is **exact hit-vector equality** against the parsed 112 taught rows | unit | `pytest tests/test_phase18_prereg.py::test_family_zero_compares_the_vector -x` | ❌ W0 |
| ATK-02 | One prompt object dispatched twice — structural check that no mode builds prompts per arm | unit | `pytest tests/test_phase18_prereg.py::test_one_corpus_two_arms -x` | ❌ W0 |
| ATK-04 | Span NLL is masked to the value tokens only — preamble changes, span NLL does not | unit | `pytest tests/test_phase18_draws.py::test_nll_is_span_masked -x` | ❌ W0 |
| **ATK-04 / D-29** | **NLL conditions on `SLOT_FORMS[slot].ans1`; all three frames computed; the held-out F3 bare frame is published but NOT read by the gate** | unit | `pytest tests/test_phase18_draws.py::test_nll_frame_is_taught_not_bare -x` | ❌ W0 |
| **ATK-04 / D-30** | **`null_result_is_admissible` reads the MEAN reduction; both published; at spread 0 (`birth_year`, `house_number`) sum and mean rank identically** | unit | `pytest tests/test_phase18_draws.py::test_mean_is_admissible_and_spread0_agrees -x` | ❌ W0 |
| ATK-04 / D-22 | Exposure rank formula `log2\|R\| − log2 rank`; ceiling equals `log2\|R\|` at rank 1 for all 8 slots | unit | `pytest tests/test_phase18_draws.py::test_exposure_ceilings_per_slot -x` | ❌ W0 |
| ATK-05 | `null_result_is_admissible` keyword-only, returns `(verdict, reasons)`, INCONCLUSIVE takes precedence — one case per condition | unit | `pytest tests/test_phase18_prereg.py::test_admissibility_precedence -x` | ❌ W0 |
| ATK-05 / STAT-05 | Every commit touching `scripts/phase18_extraction.py` precedes every `results/phase18_*` first-add | unit | `pytest tests/test_phase16_prereg.py -k phase18 -x` | ❌ W0 (glob `:54` covers artifacts) |
| ATK-05 | `scripts/erasure_gate.py` byte-untouched since `23a830c` (D-27) | unit | `pytest tests/test_phase18_prereg.py::test_erasure_gate_untouched -x` | ❌ W0 |
| **ATK-05 / D-28** | **Both new instruments (NLL/exposure, D-14 scoring) live INSIDE `scripts/phase18_extraction.py` — no admissibility logic in a helper module** | unit | `pytest tests/test_phase18_prereg.py::test_instruments_are_inside_the_pin -x` | ❌ W0 |
| **D-12 / D-28** | **Smoke additionally asserts finite NLL for every candidate in R across all 8 slots, and spread-0 control agreement — on the un-adapted base only** | unit | `pytest tests/test_phase18_prereg.py::test_smoke_covers_nll_path -x` | ❌ W0 |
| ATK-06 / D-23 | README + `docs/REPORT.md` continuations are **additive** (0 deletions); the sentence appears verbatim in all three surfaces | unit | `pytest tests/test_phase18_docs.py::test_continuation_is_additive -x` | ❌ W0 |
| ATK-06 / D-24 | Conclusion sentence produced by the committed function from committed literals; ATK-06 LoRA caveat is a required adjacent sentence | unit | `pytest tests/test_phase18_docs.py::test_conclusion_is_templated -x` | ❌ W0 |
| STAT-01 | Every published proportion declares `unit == "question"`; no prompt/draw-level denominator | unit | `pytest tests/test_phase18_prereg.py::test_every_rate_declares_its_unit -x` | ❌ W0 |
| STAT-02 | No bare `0%` in any committed report **or figure label**; every zero carries denominator + Wilson + `3/n` | unit | `pytest tests/test_phase18_docs.py::test_no_bare_zero_percent -x` | ❌ W0 |
| STAT-04 | `pyproject.toml` unchanged | unit | `pytest tests/test_phase16_prereg.py -k dependency_freeze -x` | ✅ 16-01 |
| **STAT-06 / D-31** | **Holm family size m=4 asserted at import; m≥7 must raise** | unit | `pytest tests/test_phase18_prereg.py::test_holm_family_is_reachable -x` | ❌ W0 |
| D-12 | Pre-flight smoke covers all four prompt shapes, floors against measured 56/936 and 47/936 attractors, never touches the adapter | unit | `pytest tests/test_phase18_prereg.py::test_smoke_scope_is_base_only -x` | ❌ W0 |
| — | **Manual, GPU-bound (not automatable):** the 8.17h two-arm run; the D-12 smoke's live throughput measurement; the human read of the recorded verdict | manual | — | run artifacts |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky — all Wave 0 rows start ⬜.*

> **Reachability assert, stated precisely** (D-31): the gate must be able to clear, i.e.
> `HOLM_ALPHA/m ≥ sign_test_exact((1,)*n_facts)`.
> At m=4: `0.0125 ≥ 0.0078125` ✅ (clears by 60%).
> At m=6: `0.0083333 ≥ 0.0078125` ✅ but by only `0.00052` — the Phase 16/17 razor margin, rejected.
> At m=7: `0.0071429 ≥ 0.0078125` ✗ → **must raise at import**.

---

## Wave 0 Requirements

- [ ] `tests/test_phase18_prereg.py` — ancestry (`PHASE18_PREREG_ARTIFACT`), `_GATE_MODULES` glob, static value scan, admissibility precedence, **Holm reachability (D-31)**, unit declaration, family-zero vector comparison, `erasure_gate` byte-identity, D-12 smoke scope, **instruments-inside-the-pin (D-28)**
- [ ] `tests/test_phase18_corpus.py` — byte-equality re-derivation, guard coverage per family, A2 budget bounds, D-19 RED proof, schema + reserved-family counts, no-network AST scan
- [ ] `tests/test_phase18_draws.py` — prefix stability against a deterministic fake model, strided-seed disjointness, span-masked NLL, exposure ceilings, **taught-frame conditioning (D-29)**, **mean-reduction + spread-0 control (D-30)**
- [ ] `tests/test_phase18_docs.py` — additive continuation, templated conclusion + required LoRA caveat, no bare `0%`
- [ ] Deterministic fake-model fixture in `tests/conftest.py` (currently holds only `simulate_pascal`) — needed by the D-09 prefix test, the NLL span test, and the D-29/D-30 frame tests
- [ ] Framework install: **none** — `pytest 9.0.3` present, 652 tests collect

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| The 8.17h two-arm run (adapter-on / adapter-off at the same budget) | ATK-02, ATK-03 | GPU-bound, hours-scale; cannot run in CI | Run the pinned driver; archive `results/phase18_*.json` |
| D-12 pre-flight smoke live throughput per prompt shape | D-12, OQ-4 | Requires the real model on MPS | Run smoke on `convbase_slim`, record `draws_per_min` into `results/phase18_preflight_report.md` **before** the pin |
| Human read of the recorded verdict | ATK-05, STAT-05 | The verdict template is committed; the *reading* is a human gate | Confirm the emitted verdict matches a committed template verbatim, INCONCLUSIVE included |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30 s
- [ ] D-28 … D-31 each carry at least one automated row above
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
