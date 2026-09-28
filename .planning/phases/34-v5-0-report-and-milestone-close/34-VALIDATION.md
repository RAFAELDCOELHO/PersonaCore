---
phase: 34
slug: v5-0-report-and-milestone-close
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-28
---

# Phase 34 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Source: 34-RESEARCH.md § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (`.venv`, Python 3.11) |
| **Config file** | `pyproject.toml [tool.pytest.ini_options]` + `tests/conftest.py` |
| **Quick run command** | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase34_report.py tests/test_phase34_ledger.py tests/test_package.py tests/test_phase28_report.py tests/test_phase28_ledger.py tests/test_phase28_prereg.py tests/test_phase25_correction.py tests/test_phase15_docs.py tests/test_phase18_docs.py` |
| **Census run** | `.venv/bin/pytest -q tests/test_phase29_prereg.py::test_no_v5_module_uses_the_accountant tests/test_phase30_points.py::test_ast_guard_no_v5_module_reaches_a_dp_control tests/test_phase21_sc5.py tests/test_phase25_driver.py::test_os_replace_appears_only_in_the_two_phase25_writers tests/test_phase23_resume.py::test_resume_from_none_is_inert` |
| **Frozen checks** | `.venv/bin/python scripts/phase28_report.py check` and `.venv/bin/python scripts/phase34_report.py check` (both exit 0) |
| **Full suite command** | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` + grep waiter (committed tree only) |
| **Estimated runtime** | quick ~30 s; census ~6 s; full ~25 min |

---

## Sampling Rate

- **After every task commit:** quick run + census run + both `check`s
- **After every plan wave:** full suite on a committed tree
- **Before `/gsd:verify-work`:** full suite green locally AND push-2 CI run green
- **Max feedback latency:** 40 seconds (quick + census)

---

## Per-Task Verification Map

| Req | Behavior | Test Type | Automated Command | File Exists | Status |
|-----|----------|-----------|-------------------|-------------|--------|
| RPT-04 | templates carry no bare numeral (+ planted RED) | unit | `pytest tests/test_phase34_report.py -k numeral` | ❌ W0 | ⬜ pending |
| RPT-04 | every CONTRACT path resolves and is bound | unit | `pytest tests/test_phase34_report.py -k contract` | ❌ W0 | ⬜ pending |
| RPT-04 | lead: per-leg lines precede `admission.reasons`; n64 "not measured" | unit | `pytest tests/test_phase34_report.py -k lead` | ❌ W0 | ⬜ pending |
| RPT-04 | installed spans == fresh render | unit | `pytest tests/test_phase34_report.py -k byte_identical` | ❌ W0 | ⬜ pending |
| RPT-04 | placement after PHASE28-REPORT-END / above PHASE28-GLANCE-BEGIN, zero deletions | unit | `pytest tests/test_phase34_report.py -k placement` | ❌ W0 | ⬜ pending |
| RPT-04 | v4.0 frozen block byte-identical | unit | `pytest tests/test_phase28_report.py` (3 guards amended per R-1) | ✅ edit | ⬜ pending |
| RPT-04 | renderer torch-free, clock-free | unit | `pytest tests/test_phase34_report.py -k "torch or clock"` | ❌ W0 | ⬜ pending |
| RPT-04 | provenance digests recompute | unit | `pytest tests/test_phase34_report.py -k provenance` | ❌ W0 | ⬜ pending |
| RPT-04 | ledger schema/domain/FIXED-needs-test/redump-stable | unit | `pytest tests/test_phase34_ledger.py` | ❌ W0 | ⬜ pending |
| RPT-05 | deps equal across MILESTONES-derived tags + HEAD; missing tag RED; non-vacuous | unit | `pytest tests/test_package.py` | ✅ edit | ⬜ pending |
| RPT-06 | plist tests host-independent (push-1 prerequisite, R-2) | unit | `pytest tests/test_phase31_probe.py tests/test_phase32_points.py -k plist` | ✅ edit | ⬜ pending |
| RPT-06 | `close.ci_run` success; head contains the publishing commit | unit + manual | `pytest tests/test_phase34_ledger.py -k close` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase34_report.py`, `tests/test_phase34_ledger.py` — new
- [ ] `tests/test_package.py` — derived-tag test (edit)
- [ ] `tests/test_phase31_probe.py`, `tests/test_phase32_points.py` — plist host-path fix (R-2)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Developer pushes to origin/main | RPT-06 | D-38: Claude never pushes | Developer runs `git push origin main`; Claude reads the run with `gh run view <id>` |
| Developer reads and approves the rendered blocks before publish | RPT-04 | human judgement on the published text | read-checkpoint in the publishing plan |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 40s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
