---
phase: 14
slug: teach-then-recall-demo
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-08-01
updated: 2026-08-02
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
| **Estimated runtime** | quick: **3.74 s** (101 tests) · full: **~110 s** (386 tests) — measured 2026-08-02 at phase close; the research-time estimate of ~0.75 s predated the 100 Phase-14 tests |

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

Task ID / Plan / Wave name the task that **shipped** each check. The three script-proof rows were
shipped by earlier plans and **executed** by plan 14-11 (wave 9): the teaching canary by 14-11 T1,
the scored recall run and Control 3 by 14-11 T2 — both runs exited 0, which is what turns those
rows green.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| T2 | 14-03 | 3 | DEMO-05 | — | Locked fact values keep token census + byte-fallback round-trip (D-07) | unit | `.venv/bin/pytest tests/test_phase14_factset.py -x` | ✅ exists | ✅ green |
| T3 | 14-04 | 4 | DEMO-05 | — | Teaching episodes mask exactly the answer span + eos (golden fixture) | unit | `.venv/bin/pytest tests/test_phase14_teaching.py::test_answer_span_mask -x` | ✅ exists | ✅ green |
| T3 | 14-04 | 4 | DEMO-05 | — | Teaching bin length > `block_size + 1`; token/mask bins element-aligned | unit | `.venv/bin/pytest tests/test_phase14_teaching.py::test_bin_shape -x` | ✅ exists | ✅ green |
| T1 | 14-07 | 5 | DEMO-05 | T-14-25 | Base params bit-untouched while LoRA learns the facts | script proof (`SystemExit` canary, MPS) | `.venv/bin/python scripts/teach_persona.py` | ✅ exists | ✅ green |
| T2 | 14-06 | 5 | DEMO-05 | T-14-18 | Fresh-process empty-prompt recall meets pre-registered thresholds; context dump proves no fact in context | script proof + committed report | `.venv/bin/python scripts/phase14_recall.py` | ✅ exists | ✅ green |
| T3 | 14-05 | 4 | DEMO-05 | — | D-19 generation-budget derivation + fit guard (pure function) | unit (importlib) | `.venv/bin/pytest tests/test_phase14_scoring.py::test_generation_budget -x` | ✅ exists | ✅ green |
| T3 | 14-04 | 4 | DEMO-06 | — | Taught and held-out family id sets are disjoint | unit | `.venv/bin/pytest tests/test_phase14_teaching.py::test_families_disjoint -x` | ✅ exists | ✅ green |
| T3 | 14-04 | 4 | DEMO-06 | — | No held-out question's id sequence is a contiguous subsequence of the teaching bin | unit | `.venv/bin/pytest tests/test_phase14_teaching.py::test_no_token_leakage -x` | ✅ exists | ✅ green |
| T3 | 14-05 | 4 | DEMO-06 | — | Normalizer + substring gate + contradiction detector behave as specified | unit (importlib) | `.venv/bin/pytest tests/test_phase14_scoring.py -x` | ✅ exists | ✅ green |
| T3 | 14-05 | 4 | DEMO-06 | T-14-34 | Pre-registered thresholds are literal module constants in the committed driver | unit (importlib) | `.venv/bin/pytest tests/test_phase14_scoring.py::test_preregistration_constants -x` | ✅ exists | ✅ green |
| T3 | 14-11 | 9 | DEMO-06 | T-14-18 | Taught vs held-out reported separately; all transcripts committed incl. failures | manual review | inspect `results/phase14_recall_report.md`, `results/phase14_transcripts.md` | ✅ exists | ⬜ pending (blocking human checkpoint) |
| T3 | 14-08 | 6 | DEMO-07 | — | `personalize_demo.py` `forbid_ids` mask tensor equals `demo_app.py`'s (D-17) | unit (CPU, no launch) | `.venv/bin/pytest tests/test_phase14_demo.py::test_forbid_ids_parity -x` | ✅ exists | ✅ green |
| T3 | 14-08 | 6 | DEMO-07 | — | UI token-panel ids byte-identical to the harness's committed dump (D-18) | unit | `.venv/bin/pytest tests/test_phase14_demo.py::test_prompt_ids_identical -x` | ✅ exists | ✅ green |
| T3 | 14-08 | 6 | DEMO-07 | T-14-27 | Demo emits zero remote stylesheet URLs (`build_demo().stylesheets == []`, UI-SPEC offline lock) | unit (CPU, no launch) | `.venv/bin/pytest tests/test_phase14_demo.py::test_no_remote_stylesheets -x` | ✅ exists | ✅ green |
| T3 | 14-01 | 1 | DEMO-07 | T-14-18 | `build_recall_prompt` ends at the assistant tag and contains no fact substring; `generate_text_from_ids` streams cumulatively | unit (tiny GPT fixture) | `.venv/bin/pytest tests/test_recall_prompt.py -x` | ✅ exists | ✅ green |
| T1 | 14-10 | 8 | DEMO-07 | T-14-28 | Adapter-off logits bit-identical to un-adapted base on real weights (D-11.3) | script proof, CPU | `.venv/bin/python scripts/phase14_recall.py` (control 3) | ✅ exists | ✅ green |
| — | pre-existing (Phase 9) | — | DEMO-07 | T-14-28 | Toggle enable/disable round-trip; eject returns vanilla tree; merged-module refusals | unit | `.venv/bin/pytest tests/test_lora_toggle.py -x` | ✅ exists | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

The two adapter-gated demo tests (`test_forbid_ids_parity_real_artifacts`,
`test_build_demo_stylesheets_real`) skipped for the whole phase because
`checkpoints/persona_adapter.pt` did not exist. Plan 14-11 T1 produced it and they now **run and
pass**: the suite moved from 381 passed / 6 skipped to **386 passed / 1 skipped**.

---

## Wave 0 Requirements

- [x] `tests/test_phase14_factset.py` — DEMO-05 (D-07 tokenizer census) — shipped 14-03 T2
- [x] `tests/test_phase14_teaching.py` — DEMO-05/DEMO-06 (mask fixture, bin shape, family disjointness, token-level no-leakage) — shipped 14-04 T3, extended 14-07 T3
- [x] `tests/test_phase14_scoring.py` — DEMO-06 (importlib-loaded scoring rules, thresholds, contradiction detector, D-19 budget) — shipped 14-05 T3, extended 14-09/14-10
- [x] `tests/test_phase14_demo.py` — DEMO-07 (D-17 mask parity, D-18 prompt byte-identity, offline stylesheet lock) — shipped 14-08 T3, extended 14-09
- [x] `tests/test_recall_prompt.py` — the two new package functions — shipped 14-01 T3
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

- [x] All tasks have `<automated>` verify or Wave 0 dependencies — every task across 14-01…14-11 carries an `<automated>` block, including both blocking human checkpoints (14-02 T3, 14-11 T3)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify — longest gap is 0
- [x] Wave 0 covers all MISSING references — all five test files exist and are green
- [x] No watch-mode flags — every command is a single-shot `pytest -q` or script invocation
- [x] Feedback latency < 5s — quick run **measured at 3.74 s** (101 tests, 2026-08-02)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending — the DEMO-05/06 recall verdict and the DEMO-07 on-camera demo pass are the
blocking human checkpoint at 14-11 T3. Everything automatable is green.
