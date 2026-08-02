---
phase: 14
slug: teach-then-recall-demo
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-01
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `14-RESEARCH.md` § *Validation Architecture*. That file is frozen at research
> time; **this** file is the living status tracker — the Status column moves as tasks land.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 (already installed; no Wave 0 framework install needed) |
| **Config file** | `pyproject.toml` → `[tool.pytest.ini_options]`, `testpaths=["tests"]`, `pythonpath=["."]` |
| **Quick run command** | `.venv/bin/pytest -q tests/test_phase14_*.py tests/test_recall_prompt.py` |
| **Full suite command** | `make test` (`.venv/bin/pytest -q`) |
| **Estimated runtime** | quick: <1 s · full: ~0.75 s (286 tests collected at research time) |

The suite is **CPU-only and GPU-free by contract**. No test in this phase may require MPS, a
checkpoint file, or a Gradio launch.

---

## Sampling Rate

- **After every task commit:** `.venv/bin/pytest -q tests/test_phase14_*.py tests/test_recall_prompt.py`
- **After every plan wave:** `make test` **and** `make lint`
- **Before `/gsd:verify-work`:** full suite green + all four `results/phase14_*.md` artifacts
  committed + the D-06 blocking user verdict recorded
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

Task IDs are assigned by the planner. Until plans exist, rows are keyed by requirement and
behavior; the planner (or `gsd-nyquist-auditor`) fills the Task ID / Plan / Wave columns.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| pending | — | — | DEMO-05 | — | Locked fact values keep token census + byte-fallback round-trip (D-07) | unit | `.venv/bin/pytest tests/test_phase14_factset.py -x` | ❌ W0 | ⬜ pending |
| pending | — | — | DEMO-05 | — | Teaching episodes mask exactly the answer span + eos (golden fixture) | unit | `.venv/bin/pytest tests/test_phase14_teaching.py::test_answer_span_mask -x` | ❌ W0 | ⬜ pending |
| pending | — | — | DEMO-05 | — | Teaching bin length > `block_size + 1`; token/mask bins element-aligned | unit | `.venv/bin/pytest tests/test_phase14_teaching.py::test_bin_shape -x` | ❌ W0 | ⬜ pending |
| pending | — | — | DEMO-05 | — | Base params bit-untouched while LoRA learns the facts | script proof (`SystemExit` canary, MPS) | `.venv/bin/python scripts/teach_persona.py` | ❌ W0 | ⬜ pending |
| pending | — | — | DEMO-05 | — | Fresh-process empty-prompt recall meets pre-registered thresholds; context dump proves no fact in context | script proof + committed report | `.venv/bin/python scripts/phase14_recall.py` | ❌ W0 | ⬜ pending |
| pending | — | — | DEMO-05 | — | D-19 generation-budget derivation + fit guard (pure function) | unit (importlib) | `.venv/bin/pytest tests/test_phase14_scoring.py::test_generation_budget -x` | ❌ W0 | ⬜ pending |
| pending | — | — | DEMO-06 | — | Taught and held-out family id sets are disjoint | unit | `.venv/bin/pytest tests/test_phase14_teaching.py::test_families_disjoint -x` | ❌ W0 | ⬜ pending |
| pending | — | — | DEMO-06 | — | No held-out question's id sequence is a contiguous subsequence of the teaching bin | unit | `.venv/bin/pytest tests/test_phase14_teaching.py::test_no_token_leakage -x` | ❌ W0 | ⬜ pending |
| pending | — | — | DEMO-06 | — | Normalizer + substring gate + contradiction detector behave as specified | unit (importlib) | `.venv/bin/pytest tests/test_phase14_scoring.py -x` | ❌ W0 | ⬜ pending |
| pending | — | — | DEMO-06 | — | Pre-registered thresholds are literal module constants in the committed driver | unit (importlib) | `.venv/bin/pytest tests/test_phase14_scoring.py::test_preregistration_constants -x` | ❌ W0 | ⬜ pending |
| pending | — | — | DEMO-06 | — | Taught vs held-out reported separately; all transcripts committed incl. failures | manual review | inspect `results/phase14_recall_report.md`, `results/phase14_transcripts.md` | ❌ W0 | ⬜ pending |
| pending | — | — | DEMO-07 | — | `personalize_demo.py` `forbid_ids` mask tensor equals `demo_app.py`'s (D-17) | unit (CPU, no launch) | `.venv/bin/pytest tests/test_phase14_demo.py::test_forbid_ids_parity -x` | ❌ W0 | ⬜ pending |
| pending | — | — | DEMO-07 | — | UI token-panel ids byte-identical to the harness's committed dump (D-18) | unit | `.venv/bin/pytest tests/test_phase14_demo.py::test_prompt_ids_identical -x` | ❌ W0 | ⬜ pending |
| pending | — | — | DEMO-07 | — | Demo emits zero remote stylesheet URLs (`build_demo().stylesheets == []`, UI-SPEC offline lock) | unit (CPU, no launch) | `.venv/bin/pytest tests/test_phase14_demo.py::test_no_remote_stylesheets -x` | ❌ W0 | ⬜ pending |
| pending | — | — | DEMO-07 | — | `build_recall_prompt` ends at the assistant tag and contains no fact substring; `generate_text_from_ids` streams cumulatively | unit (tiny GPT fixture) | `.venv/bin/pytest tests/test_recall_prompt.py -x` | ❌ W0 | ⬜ pending |
| pending | — | — | DEMO-07 | — | Adapter-off logits bit-identical to un-adapted base on real weights (D-11.3) | script proof, CPU | `.venv/bin/python scripts/phase14_recall.py` (control 3) | ❌ W0 | ⬜ pending |
| — | — | — | DEMO-07 | — | Toggle enable/disable round-trip; eject returns vanilla tree; merged-module refusals | unit | `.venv/bin/pytest tests/test_lora_toggle.py -x` | ✅ exists | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase14_factset.py` — stubs for DEMO-05 (D-07 tokenizer census)
- [ ] `tests/test_phase14_teaching.py` — stubs for DEMO-05/DEMO-06 (mask fixture, bin shape, family disjointness, token-level no-leakage)
- [ ] `tests/test_phase14_scoring.py` — stubs for DEMO-06 (importlib-loaded scoring rules, thresholds, contradiction detector, D-19 budget)
- [ ] `tests/test_phase14_demo.py` — stubs for DEMO-07 (D-17 mask parity, D-18 prompt byte-identity, offline stylesheet lock)
- [ ] `tests/test_recall_prompt.py` — stubs for the two new package functions
- [x] Framework install — **not needed**; pytest 9.0.3 present and the suite is green

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Guessability gate on the locked fact set | DEMO-05 | D-06 is a **blocking human verdict** by design — no automated proxy is legitimate | Run the gate script, read the candidate facts, record the verdict in the phase artifacts before teaching |
| Teaching run on real weights | DEMO-05 | Needs the 278 MB base checkpoint + MPS; forbidden in the CPU suite | `.venv/bin/python scripts/teach_persona.py`; canary raises `SystemExit` on base-weight drift |
| Calibration / scored recall run | DEMO-05, DEMO-06 | Needs checkpoints + MPS; produces the committed `results/phase14_*.md` artifacts | `.venv/bin/python scripts/phase14_recall.py`; review all four artifacts incl. failures |
| Demo surface on camera (toggle, Reset, token panel, streaming) | DEMO-07 | Gradio launch + human-visible behavior; the phase deliverable is a recorded frame | Launch `scripts/personalize_demo.py` locally, exercise ON → OFF → Reset, confirm the token panel and per-bubble stamps match the UI-SPEC contracts |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
