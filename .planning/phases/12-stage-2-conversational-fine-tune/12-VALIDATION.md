---
phase: 12
slug: stage-2-conversational-fine-tune
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-31
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (existing — 250 tests green) |
| **Config file** | pyproject.toml |
| **Quick run command** | `.venv/bin/python -m pytest tests/ -x -q` |
| **Full suite command** | `.venv/bin/python -m pytest tests/ -q` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/python -m pytest tests/ -x -q`
- **After every plan wave:** Run `.venv/bin/python -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| (filled by planner) | | | | | | | | | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_masked_train_seam.py` — mask-bin batch_fn routing; defaults ⇒ v1.0 identity (golden trajectory)
- [ ] `tests/test_extra_eval_fns.py` — extra columns logged; model restored to train mode; None ⇒ identical CSV
- [ ] `tests/test_masked_perplexity.py` — hand-fixture oracle: CE summed over mask=1 targets only
- [ ] `tests/test_stop_ids.py` — default ≡ v1.0 EOS behavior; stops-without-yield on any stop id

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Smoke-report review at D-07 blocking checkpoint | EWC-03 | Pre-registered human gate on λ*/smoke evidence | Review results/finetune_smoke_report.md before production run |
| Curated transcript quality | TUNE-01 | Dialogue-format adherence is a judgment on generated text | Review results/transcripts.md |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
