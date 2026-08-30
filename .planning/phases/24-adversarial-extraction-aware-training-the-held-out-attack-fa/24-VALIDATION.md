---
phase: 24
slug: adversarial-extraction-aware-training-the-held-out-attack-fa
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-30
---

# Phase 24 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `24-RESEARCH.md` § Validation Architecture. Every anchor below was
> confirmed to exist at HEAD before this file was written.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x — `testpaths = ["tests"]`, `pythonpath = ["."]` (`pyproject.toml:24-26`) |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `pytest -q tests/test_phase14_scoring.py tests/test_phase21_replay_volume.py tests/test_phase21_aligned_bins.py` |
| **Full suite command** | `make test` (→ `pytest -q`) |
| **Estimated runtime** | ~15 s quick (55 tests in 10.56 s measured over the first two files); full suite CPU-only, GPU-free |

**No new test infrastructure is required.** No framework install, no `conftest.py` change.
Every assertion anchors to a module that already exists and already runs in CI.

---

## Sampling Rate

- **After every task commit:** `pytest -q tests/test_phase14_scoring.py tests/test_phase21_replay_volume.py tests/test_phase21_aligned_bins.py`
- **After every plan wave:** add `pytest -q tests/test_phase18_corpus.py tests/test_phase16_prereg.py`
- **Before `/gsd:verify-work`:** `make test` must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

*Populated by the planner — one row per task, keyed to the plan IDs it emits.*

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| *pending* | — | — | — | — | — | — | — | — | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### Requirement → anchor map (the contract each task row must satisfy)

| Req | Behavior asserted | Anchor (verified at HEAD) | Command |
|---|---|---|---|
| **ADVT-01** SC1 | `build_bins(..., adversarial_ratio=0.0)` writes bins byte-identical to v2.0 | `tests/test_phase21_aligned_bins.py::test_build_bins_byte_identity_default_matches_the_v2_golden` :200, vs `tests/fixtures/golden_build_bins_v2.json` | `pytest -q tests/test_phase21_aligned_bins.py` |
| **ADVT-01** SC1 (load-bearing half) | `adversarial_ratio` is actually **read**, not a dead kwarg — a byte-identity guard over an unwired kwarg is vacuously green | sibling of `tests/test_phase21_aligned_bins.py::test_align_facts_is_wired` :229 | same |
| **ADVT-01** D-02 | No refusal template contains any published value | **new sibling** of `tests/test_phase14_scoring.py::test_no_fact_strings_at_import` :367, reusing helper `embedded_fact_values` :349. Leave the existing `assert len(forbidden) == 10` untouched | `pytest -q tests/test_phase14_scoring.py` |
| **ADVT-01** D-10 | A3's `persona=` call site is allowlisted | `tests/test_phase14_scoring.py` D-21 hard-equality guard :539-559 (`PERSONA_ALLOWLIST` 4th entry) | same |
| **ADVT-02** D-13a | trained {A1-mild, A1-aggressive, A3} ∩ held-out {A2} = ∅ on key **`family`** | new named assertion in the `tests/test_phase18_corpus.py` register (`test_schema_and_reserved_family` :538 is the shape), reading `results/phase18_corpus.json` | `pytest -q tests/test_phase18_corpus.py` |
| **ADVT-02** D-13b | taught {F1,F2,F6} vs held-out {F3,F7,F8,reserved} disjoint on key **`source_family`** | **second, separately named** assertion — must not be conflated with D-13a | same |
| **ADVT-02** D-13 correction | the original `(fact_id, seed_index)` key is unsatisfiable and superseded, not deleted | `.planning/ROADMAP.md:721-724` dated continuation; `tests/test_phase20_correction.py` is the precedent shape | `pytest -q tests/test_phase20_correction.py` |
| **ADVT-03** | scored-token counts reported **per arm**, in a committed record | `build_bins` already returns `stats["tokens"]` / `["teaching_tokens"]` / `["mask_fraction"]` (:730-741, printed :1063) — **nothing persists them today**; Phase 24 must add the record + a test asserting its keys | new Phase-24 test module |
| **ADVT-01/02** SC4 | `scripts/phase18_extraction.py` ancestry-guarded, never edited | `tests/test_phase16_prereg.py::test_phase18_prereg_is_frozen_before_every_phase18_result` :322 | `pytest -q tests/test_phase16_prereg.py` |
| **D-05** | mask fraction inside `(0.15, 0.95)` at **all four** grid corners | `_prove_floor_and_band` (`scripts/teach_persona.py:528`) already `SystemExit`s at BUILD time; add a build-only CPU test asserting `frac >= 0.15` with margin | `pytest -q tests/test_phase24_*.py` (~4 s/corner, no GPU) |
| **D-08** | bins rebuild byte-identically after a kill | `build_arm_bins` rebuild-and-compare :1019-1039 + `tests/test_phase23_resume.py` | `pytest -q tests/test_phase23_resume.py` |
| **D-06** | volume is not derived from `teaching_tokens` | `tests/test_phase21_replay_volume.py::test_replay_constant_is_not_derived_from_the_corpus` :260 — left untouched as a regression tripwire | `pytest -q tests/test_phase21_replay_volume.py` |

---

## Wave 0 Requirements

- [ ] `tests/test_phase24_*.py` — the D-05 **four-corner** band check, build-only, no training.
      **Highest-value new test in the phase:** it converts a post-compute `SystemExit` into a
      4-second red test. Corners are `{n=8, n=64} × {ratio 0.0, ratio 1.909}`; `n=8` is the
      binding one (needs `L ≥ 9` scored tokens per refusal vs `L ≥ 7` at n=64).
- [ ] D-02 sibling guard in `tests/test_phase14_scoring.py` — **watch RED before GREEN** (D-02).
- [ ] The two D-13 assertions (`family`, `source_family`), **separately named**.
- [ ] A committed ADVT-03 record carrying per-arm scored-token counts — nothing persists them today.
- No framework install needed; no `conftest.py` change needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Positive confirmation that an attack on a filler fact triggers refusal by frame generalization | — (declared residue 1) | D-11's clean-frame probe detects fact-keyed refusal but cannot confirm the positive direction | Out of scope for Phase 24 — declared under the D-16 discipline, as Phase 26 SC3 already invokes |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
