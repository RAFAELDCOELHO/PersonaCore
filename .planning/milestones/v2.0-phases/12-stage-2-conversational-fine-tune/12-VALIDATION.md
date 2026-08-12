---
phase: 12
slug: stage-2-conversational-fine-tune
status: ready
nyquist_compliant: true
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
| 12-01-T1 | 12-01 | 1 | TUNE-01 | T-12-01 | mask seam additive, v1.0 identity | unit (tdd) | `.venv/bin/python -m pytest tests/test_masked_train_seam.py -x -q` | ✅ exists | ✅ green |
| 12-01-T2 | 12-01 | 1 | TUNE-02 | T-12-01/02 | extra columns per-run, CSV_FIELDNAMES never mutated | unit (tdd) | `.venv/bin/python -m pytest tests/test_extra_eval_fns.py -x -q` | ✅ exists | ✅ green |
| 12-01-T3 | 12-01 | 1 | DEBT-01, DEBT-02 | T-12-01 | golden trajectory bit-identical | unit (existing pins) | `.venv/bin/python -m pytest tests/ -q` | ✅ | ✅ green |
| 12-02-T1 | 12-02 | 1 | TUNE-01 | T-12-04 | gate metric exact denominator, loud raises | unit (tdd) | `.venv/bin/python -m pytest tests/test_masked_perplexity.py -x -q` | ✅ exists | ✅ green |
| 12-02-T2 | 12-02 | 1 | TUNE-01 | T-12-03 | stop_ids default ≡ v1.0 | unit (tdd) | `.venv/bin/python -m pytest tests/test_stop_ids.py -x -q` | ✅ exists | ✅ green |
| 12-03-T1 | 12-03 | 1 | TUNE-02 | T-12-05/07 | refuse-to-rerun, trusted-only load | script lint + greps | `ruff check scripts/build_retention_bin.py` + SystemExit count | n/a | ✅ green |
| 12-03-T2 | 12-03 | 1 | TUNE-02 | T-12-06 | anchors measured not asserted; fullval < 2.1066 | script run + JSON assert | inline python assert on retention_anchors.json | n/a | ✅ green |
| 12-04-T1 | 12-04 | 2 | EWC-03 | T-12-08 | pre-registration committed before numbers | script lint + greps | ruff + PRE-REGISTRATION/SystemExit greps | n/a | ✅ green |
| 12-04-T2 | 12-04 | 2 | EWC-03, TUNE-01, TUNE-02 | T-12-09/10/11 | gates mechanical; halt-on-violation; PENDING verdict | manual-artifact (training) + automated file checks | report/CSV greps + full pytest | n/a | ✅ green |
| 12-04-T3 | 12-04 | 2 | EWC-03 | T-12-08 | ONE blocking D-07 checkpoint | checkpoint:human-verify | — (blocking gate) | n/a | ✅ green |
| 12-05-T1 | 12-05 | 3 | TUNE-01, EWC-03 | T-12-13/14 | GO-verdict gate; fingerprint-pinned Fisher | script lint + greps | ruff + verdict/export_slim greps | n/a | ✅ green |
| 12-05-T2 | 12-05 | 3 | TUNE-01, TUNE-02 | T-12-12 | slim loads weights_only=True; step-0 curve | manual-artifact (training) + automated CSV/blob asserts | inline python asserts on finetune_prod.csv + checkpoints | n/a | ✅ green |
| 12-05-T3 | 12-05 | 3 | TUNE-01 | T-12-15 | serialize-path prompts; measurable proxies | script run + greps + full suite | transcripts.md greps + full pytest | n/a | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_masked_train_seam.py` — mask-bin batch_fn routing; defaults ⇒ v1.0 identity (golden trajectory) — created by 12-01-T1
- [ ] `tests/test_extra_eval_fns.py` — extra columns logged; model restored to train mode; None ⇒ identical CSV — created by 12-01-T2
- [ ] `tests/test_masked_perplexity.py` — hand-fixture oracle: CE summed over mask=1 targets only — created by 12-02-T1
- [ ] `tests/test_stop_ids.py` — default ≡ v1.0 EOS behavior; stops-without-yield on any stop id — created by 12-02-T2

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Smoke-report review at D-07 blocking checkpoint | EWC-03 | Pre-registered human gate on λ*/smoke evidence | Review results/finetune_smoke_report.md before production (12-04-T3) |
| Curated transcript quality | TUNE-01 | Dialogue-format adherence is a judgment on generated text | Review results/transcripts.md (proxies reported alongside) |
| Multi-hour training runs (smoke arms + production) | EWC-03/TUNE-01/02 | Training cannot execute in CI (v1.0 T-07-07 precedent) | Verified via committed report/CSVs + driver proof SystemExits |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 120s (unit paths; training runs are pre-registered manual artifacts)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** planner 2026-08-01
