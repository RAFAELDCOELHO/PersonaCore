---
phase: 10
slug: ewc-core
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-06-12
updated: 2026-06-12
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (installed in .venv, Python 3.11.15) |
| **Config file** | none — house convention is bare `tests/` + existing `conftest.py` |
| **Quick run command** | `source .venv/bin/activate && pytest tests/test_fisher.py tests/test_ewc_penalty.py tests/test_loop_penalty_fn.py tests/test_fisher_checkpoint.py -q -x` |
| **Full suite command** | `source .venv/bin/activate && make test` (190+ existing tests must stay green) |
| **Estimated runtime** | quick ~30 s; full suite ~2-3 min; smoke script ~1-2 min |

All tests CPU-only/GPU-free (house discipline); the real-device (MPS) proof lives in
`scripts/estimate_fisher_tinystories.py`, not the suite.

---

## Sampling Rate

- **After every task commit:** Run the quick run command (only the new-phase test files that exist so far)
- **After every plan wave:** Run `make test` (full suite) + `make lint`
- **Before `/gsd:verify-work`:** Full suite green AND `python scripts/estimate_fisher_tinystories.py` has exited 0 (cache exists)
- **Max feedback latency:** ~180 s (full suite); ~30 s per-task

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | EWC-01 | T-10-01 | finiteness guard fails loudly on corrupt data | unit (tdd) | `pytest tests/test_fisher.py -q -x` | ❌ created in-task (tests-first) | ⬜ pending |
| 10-01-02 | 01 | 1 | EWC-02 | — | fail-loud ValueError at construction/call | unit (tdd) | `pytest tests/test_ewc_penalty.py -q -x && make test` | ❌ created in-task (tests-first) | ⬜ pending |
| 10-02-01 | 02 | 2 | EWC-02 | T-10-04 | golden provenance pinned (captured_at_sha) | fixture capture + structural check | inline `python -c` JSON structure assertion | ❌ created in-task | ⬜ pending |
| 10-02-02 | 02 | 2 | EWC-02 | T-10-03 | default-None ≡ v1.0 checkpoints | unit (tdd) + full suite | `pytest tests/test_loop_penalty_fn.py -q -x && make test` | ❌ created in-task (tests-first) | ⬜ pending |
| 10-03-01 | 03 | 2 | EWC-01 | T-10-06 | weights_only=True choke point + schema gate | unit (tdd) | `pytest tests/test_fisher_checkpoint.py -q -x && make test` | ❌ created in-task (tests-first) | ⬜ pending |
| 10-03-02 | 03 | 2 | EWC-01 | T-10-05/T-10-07 | trusted-own-file load; cache stays untracked | smoke (scripted SystemExit checks) | `python scripts/estimate_fisher_tinystories.py` + load_fisher check + rerun-refusal check | ❌ created in-task | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

No separate Wave 0: every code-producing task is `tdd="true"` and creates its test file FIRST
within the task (RED before GREEN), so the MISSING test references in 10-RESEARCH.md's
Validation Architecture are closed by plan design:

- [ ] `tests/test_fisher.py` — created tests-first in task 10-01-01 (EWC-01 unit pins)
- [ ] `tests/test_ewc_penalty.py` — created tests-first in task 10-01-02 (EWC-02 penalty pins)
- [ ] `tests/fixtures/golden_trajectory_v1.json` — captured in task 10-02-01 BEFORE the loop edit (Pitfall 6 ordering enforced by task sequence)
- [ ] `tests/test_loop_penalty_fn.py` — created tests-first in task 10-02-02 (bit-identity + accum pins)
- [ ] `tests/test_fisher_checkpoint.py` — created tests-first in task 10-03-01 (persistence + cache schema pins)
- [ ] `scripts/estimate_fisher_tinystories.py` — created + executed in task 10-03-02 (real-weights smoke)
- Framework install: none — pytest already present

---

## Manual-Only Verifications

All phase behaviors have automated verification. (The smoke script is automated — scripted
SystemExit proof checks with exit-code semantics — merely slow at ~1-2 min.)

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (every task has one)
- [x] Wave 0 covers all MISSING references (folded into tests-first tdd tasks)
- [x] No watch-mode flags
- [x] Feedback latency < 180 s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-06-12 (planner)
