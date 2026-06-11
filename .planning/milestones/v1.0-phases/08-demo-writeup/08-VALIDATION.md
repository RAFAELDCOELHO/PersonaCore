---
phase: 8
slug: demo-writeup
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-06-10
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (CPU-only, GPU/MPS-free) |
| **Config file** | pyproject.toml |
| **Quick run command** | `.venv/bin/python -m pytest tests/ -x -q -k "<touched component>"` |
| **Full suite command** | `.venv/bin/python -m pytest tests/ -q` |
| **Estimated runtime** | ~70 seconds (122 passed, 1 skipped baseline) |

---

## Sampling Rate

- **After every task commit:** Run the quick run command scoped to the touched component
- **After every plan wave:** Run `.venv/bin/python -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 08-01.T1 | 01 | 1 | DEMO-02 | T-08-01 | Slim test asserts weights_only=True load succeeds | unit (Wave-0 RED) | `.venv/bin/python -m pytest tests/test_slim_checkpoint.py -q` (expect RED) | created in task | ⬜ pending |
| 08-01.T2 | 01 | 1 | DEMO-02, QA-02 | T-08-01, T-08-02 | load_slim = restricted unpickler choke point; best.pt read trusted-only | unit | `.venv/bin/python -m pytest tests/test_slim_checkpoint.py -q && make lint` | ✅ after T1 | ⬜ pending |
| 08-01.T3 | 01 | 1 | DEMO-02, QA-01 | T-08-03 | Artifact key set = tensors/config/SHA only; gitignore intact | integration + full suite | `scripts/export_slim.py` + size assert + `pytest -q` | ✅ | ⬜ pending |
| 08-02.T1 | 02 | 2 | DEMO-01 | T-08-04 | 4096-token DoS cap fires through the adapter | unit | `.venv/bin/python -m pytest tests/test_demo_callback.py tests/test_generation_text.py -q` | created in task | ⬜ pending |
| 08-02.T2 | 02 | 2 | DEMO-01 | T-08-01, T-08-02, T-08-03 | weights_only=False absent; share=False; analytics killed pre-import | smoke (construct) | importlib exec + `build_demo()` prints ChatInterface; `make lint` | ✅ | ⬜ pending |
| 08-02.T3 | 02 | 2 | DEMO-01 | T-08-02, T-08-03 | Wi-Fi-off streaming session | manual (checkpoint:human-verify) | — see Manual-Only table | — | ⬜ pending |
| 08-03.T1 | 03 | 2 | DEMO-03 | T-08-SC | [ASSUMED] installs gated (ipykernel/nbconvert) | manual (blocking-human) | — see Manual-Only table | — | ⬜ pending |
| 08-03.T2 | 03 | 2 | DEMO-03 | — | Committed curve byte-identical to source | CLI | `cmp logs/run.csv results/run.csv && wc -l && grep header` | ✅ | ⬜ pending |
| 08-03.T3 | 03 | 2 | DEMO-03, QA-02 | T-08-01, T-08-05 | Notebook loads slim only; no logs/best.pt refs in committed outputs | smoke | `jupyter nbconvert --execute` exit 0 + nbformat monotonic/size checks | notebook IS the deliverable | ⬜ pending |
| 08-04.T1 | 04 | 2 | DOC-01 | T-08-06 | Honest M1/M2 framing; no overclaim | source assertion | grep set (sections, Milestone 2, data_ptr, 8192) on docs/REPORT.md | ✅ | ⬜ pending |
| 08-04.T2 | 04 | 2 | DOC-01 | T-08-06 | PPL always with denominator; caveat verbatim | source assertion | grep set (2.1066, 12,636,922, NOT to the headline, weights_only=True) | ✅ | ⬜ pending |
| 08-05.T1 | 05 | 3 | DOC-01 | T-08-SC | [ASSUMED] install gated (imageio-ffmpeg) | manual (blocking-human) | — see Manual-Only table | — | ⬜ pending |
| 08-05.T2 | 05 | 3 | DOC-01 | T-08-05 | Window-scoped capture (demo UI only) | manual (human-action) | — see Manual-Only table | — | ⬜ pending |
| 08-05.T3 | 05 | 3 | DOC-01 | T-08-05 | No .mov/palette committed | CLI | GIF magic/720px/size python assert | ✅ | ⬜ pending |
| 08-06.T1 | 06 | 4 | DOC-01 | T-08-08 | Weights published only on explicit selection | manual (checkpoint:decision) | — see Manual-Only table | — | ⬜ pending |
| 08-06.T2 | 06 | 4 | DOC-01 | T-08-06, T-08-07 | No present-tense M2 claims; Release pins SHA | source assertion | README grep set (+ `gh release view` if release) | ✅ | ⬜ pending |
| 08-06.T3 | 06 | 4 | QA-01, QA-02 | T-08-05 | Hygiene: no pt/bin/mov/secrets tracked | full suite + CLI | `pytest -q && make lint` + consistency greps + `git ls-files` filters | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_slim_checkpoint.py` — offline load/generate test for the DEMO-02 slim artifact (`weights_only=True` path) — **planned as 08-01 Task 1 (the first executed task of the phase, written RED before the export exists)**

*Existing infrastructure (37 CPU-only test files, conftest fixtures) covers all other phase requirements; the slim-checkpoint test is the only required new automated surface. 08-02 Task 1 additionally adds `tests/test_demo_callback.py` covering the testable slice of DEMO-01 (the optional Wave-0 item from 08-RESEARCH).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Gradio chat UI streams a story on CPU with temperature/top-k controls, fully offline | DEMO-01 | Live browser interaction; offline posture verified by observing no network egress | 08-02 Task 3 checkpoint: launch demo in `.venv`, open localhost, turn Wi-Fi OFF, send prompt, watch cumulative streaming, exercise sliders |
| `demo.ipynb` renders curves/tables/samples end-to-end | DEMO-03 | Visual inspection of committed outputs (execution itself is automated via nbconvert) | 08-03 Task 3 automated nbconvert + nbformat checks; visual confirmation at `/gsd:verify-work` |
| README GIF shows live CPU streaming | DOC-01 (D-04) | Screen capture is inherently interactive | 08-05 Task 2 human-action records the .mov; Task 3 converts + structurally verifies |
| Package legitimacy gates (ipykernel, nbconvert, imageio-ffmpeg) | supply chain (T-08-SC) | slopcheck unavailable at research time → [ASSUMED] installs need human PyPI verification | 08-03 Task 1 and 08-05 Task 1 blocking-human checkpoints |
| Weights distribution decision (Release vs regenerate-only) | DOC-01 | Repo-publishing intent is the developer's call (T-08-08) | 08-06 Task 1 checkpoint:decision |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (checkpoint tasks are manual-only by design and listed above)
- [x] Sampling continuity: no 3 consecutive auto tasks without automated verify (every auto task carries `<automated>`)
- [x] Wave 0 covers all MISSING references (test_slim_checkpoint.py = 08-01.T1; test_demo_callback.py = 08-02.T1)
- [x] No watch-mode flags
- [x] Feedback latency < 90s (scoped pytest runs < 10 s; full suite ~70 s)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** planner sign-off 2026-06-10 (gsd-planner); `wave_0_complete` flips true when 08-01 Task 1 lands
