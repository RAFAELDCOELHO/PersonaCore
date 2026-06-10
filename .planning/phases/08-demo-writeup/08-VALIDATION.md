---
phase: 8
slug: demo-writeup
status: draft
nyquist_compliant: false
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
| *(filled by planner)* | | | | | | | | | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_slim_checkpoint.py` — offline load/generate test for the DEMO-02 slim artifact (`weights_only=True` path)

*Existing infrastructure (37 CPU-only test files, conftest fixtures) covers all other phase requirements; the slim-checkpoint test is the only new automated surface.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Gradio chat UI streams a story on CPU with temperature/top-k controls, fully offline | DEMO-01 | Live browser interaction; offline posture verified by observing no network egress | Launch demo script in `.venv`, open localhost URL, send a prompt, watch token streaming; verify with network monitor that no external calls occur |
| `demo.ipynb` renders curves/tables/samples end-to-end | DEMO-03 | Notebook execution + visual inspection of committed outputs | Execute notebook top-to-bottom in `.venv` kernel; confirm all cells run and outputs are committed |
| README GIF shows live CPU streaming | DOC-01 (D-04) | Screen capture is inherently interactive | Record the running demo, convert via ffmpeg, embed in README |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
