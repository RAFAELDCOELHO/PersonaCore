---
phase: 24
slug: adversarial-extraction-aware-training-the-held-out-attack-fa
status: planned
nyquist_compliant: true
wave_0_complete: true
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

*Populated by the planner 2026-08-30 — 17 tasks across 7 plans in 4 waves.*

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 24-01-T1 | 24-01 | 1 | ADVT-01 | T-24-01/03 | refusal table is per-slot, value-free, key-parity enforced at import | unit | `pytest -q tests/test_phase24_refusal.py` | `scripts/phase24_adversarial.py` | ⬜ pending |
| 24-01-T2 | 24-01 | 1 | ADVT-01 | T-24-03/05 | every refusal clears MIN_REFUSAL_SCORED_TOKENS through the frozen tokenizer | unit | `pytest -q tests/test_phase24_refusal.py` | `tests/test_phase24_refusal.py` | ⬜ pending |
| 24-01-T3 | 24-01 | 1 | ADVT-01 | T-24-01/02/04 | no published value in any refusal string, docstrings included — watched RED first | static/AST | `pytest -q tests/test_phase14_scoring.py` | `tests/test_phase14_scoring.py` | ⬜ pending |
| 24-02-T1 | 24-02 | 1 | ADVT-01, ADVT-03 | T-24-07/08 | grid is literal assignments only; zero imports, zero branches | static/AST | `pytest -q tests/test_phase23_budget.py` | `scripts/mitigation_budget.py` | ⬜ pending |
| 24-02-T2 | 24-02 | 1 | ADVT-03 | T-24-06/09 | both extremes re-derive from committed artifacts under exact == | re-derivation | `pytest -q tests/test_phase24_grid.py` | `tests/test_phase24_grid.py` | ⬜ pending |
| 24-03-T1 | 24-03 | 1 | ADVT-02 | T-24-12/13 | trained ∩ held-out = ∅ on `family`; taught vs held-out disjoint on `source_family`; old key measured unsatisfiable | artifact read | `pytest -q tests/test_phase24_split.py` | `tests/test_phase24_split.py` | ⬜ pending |
| 24-03-T2 | 24-03 | 1 | ADVT-02 | T-24-11/15/16 | original SC2 clause stands, superseded by a dated 24-03 continuation; node ids resolved by AST | doc guard | `pytest -q tests/test_phase24_correction.py` | `.planning/ROADMAP.md` | ⬜ pending |
| 24-04-T1 | 24-04 | 1 | ADVT-01 | T-24-17/21 | contains_refusal reuses the ONE scoring normalizer; frozen gate untouched | unit | `pytest -q tests/test_phase14_scoring.py` | `scripts/phase14_recall.py` | ⬜ pending |
| 24-04-T2 | 24-04 | 1 | ADVT-01 | T-24-18/19/20 | pointwise mirror agreement with contains_value; D-11 populations disjoint and pinned | unit | `pytest -q tests/test_phase24_refusal_rate.py` | `tests/test_phase24_refusal_rate.py` | ⬜ pending |
| 24-05-T1 | 24-05 | 2 | ADVT-01, ADVT-02 | T-24-23/24/26/27/28 | 336 deterministic episodes, core_taught only, A2 refused, every prompt byte-equal to its committed row | integration | `pytest -q tests/test_phase16_prereg.py tests/test_phase18_corpus.py` | `scripts/phase24_adversarial.py` | ⬜ pending |
| 24-05-T2 | 24-05 | 2 | ADVT-01, ADVT-02 | T-24-25/29 | fourth PERSONA_ALLOWLIST entry lands with its call site; D-21 hard equality green | static/AST | `pytest -q tests/test_phase24_adversarial.py tests/test_phase14_scoring.py` | `tests/test_phase24_adversarial.py` | ⬜ pending |
| 24-06-T1 | 24-06 | 3 | ADVT-01 | T-24-30 | the wiring sibling is WATCHED RED before the kwarg exists | watched-RED | `pytest -q tests/test_phase21_aligned_bins.py tests/test_phase21_replay_volume.py` | `tests/test_phase24_bins.py` | ⬜ pending |
| 24-06-T2 | 24-06 | 3 | ADVT-01 | T-24-31/32/33/37 | adversarial_ratio=0.0 byte-identical; permutation pure in seed; sizing from episode count | golden + property | `pytest -q tests/test_phase24_bins.py tests/test_phase21_aligned_bins.py` | `scripts/teach_persona.py` | ⬜ pending |
| 24-06-T3 | 24-06 | 3 | ADVT-01, ADVT-03 | T-24-34/36 | adv_n8/adv_n64 pack FLAT; ratio reaches build_bins from train_arm; sanity_check proof 6 passes | integration | `pytest -q tests/test_phase14_teaching.py tests/test_phase22_wiring.py tests/test_phase23_resume.py` | `scripts/teach_persona.py` | ⬜ pending |
| 24-07-T1 | 24-07 | 4 | ADVT-01 | T-24-39/40 | all four D-05 corners clear the floor with MASK_FRACTION_MARGIN; control corner = the flat operating point | build-only | `pytest -q tests/test_phase24_band.py` | `tests/test_phase24_band.py` | ⬜ pending |
| 24-07-T2 | 24-07 | 4 | ADVT-03 | T-24-38/42/43/44 | per-arm scored-token counts persisted with denominators, multiplicity, corpus sha256 and SC4 discharge | artifact write | `pytest -q tests/test_phase24_record.py` | `results/phase24_token_budget.json` | ⬜ pending |
| 24-07-T3 | 24-07 | 4 | ADVT-02, ADVT-03 | T-24-38/41 | record covers every grid point; counts re-derive from a rebuild under exact == | re-derivation | `pytest -q tests/test_phase24_record.py tests/test_phase24_band.py` | `tests/test_phase24_record.py` | ⬜ pending |

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
