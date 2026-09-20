---
phase: 28
slug: report-the-published-null-and-milestone-close
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-20
---

# Phase 28 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `28-RESEARCH.md` §Validation Architecture; the planner fills the per-task map.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest `~=9.0` (`pyproject.toml [project.optional-dependencies].dev`) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests"]`, `pythonpath = ["."]`) |
| **Quick run command** | `.venv/bin/pytest tests/test_phase28_report.py tests/test_phase28_ledger.py tests/test_package.py tests/test_phase18_docs.py tests/test_phase15_docs.py -q` |
| **Full suite command** | `make test` (= `.venv/bin/pytest -q`) — committed tree only, `run_in_background`, never behind `timeout 300` |
| **Lint** | `make lint` |
| **Estimated runtime** | quick: seconds · full: ~21–24 min (2871 tests) |

---

## Sampling Rate

- **After every task commit:** Run the quick run command + `make lint` (< 1 min)
- **After every plan wave:** Run `make test` uncapped, in the background, on the committed tree (no untracked `results/`/`tests/`/`scripts/` files present)
- **Before `/gsd:verify-work`:** Full suite green locally AND the D-38 CI run on `origin/main` green
- **Max feedback latency:** 60 s per task; ~24 min per wave

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| — | — | — | RPT-01 / SC1 | T-28-lead | lead quotes `capacity_branch` + both `arm_existentials` + `cleared_counts`; expectation quoted verbatim | unit | `pytest tests/test_phase28_report.py -k "lead or expectation" -x` | ❌ W0 | ⬜ pending |
| — | — | — | RPT-01 / SC1 | T-28-prereg | quote present at `c673b4c`; `c673b4c` ≺ earliest `results/phase2[0-8]_*` add; shallow clone refuses | unit (git) | `pytest tests/test_phase28_prereg.py -k ancestry -x` | ❌ W0 | ⬜ pending |
| — | — | — | RPT-01 / SC2 | T-28-bytes | re-render == committed bytes (REPORT block, README block) | unit | `pytest tests/test_phase28_report.py -k byte_identical -x` | ❌ W0 | ⬜ pending |
| — | — | — | RPT-01 / SC2 | T-28-numeral | template source has no bare numeral outside D-19 grammar (+ planted RED probe) | unit | `pytest tests/test_phase28_report.py -k template_scan -x` | ❌ W0 | ⬜ pending |
| — | — | — | RPT-01 / SC2 | T-28-const | every ε/σ/C/q/δ/K binding equals its module constant and the record | unit | `pytest tests/test_phase28_report.py -k constants -x` | ❌ W0 | ⬜ pending |
| — | — | — | RPT-01 / SC2 | T-28-oblig | all `PUBLICATION_OBLIGATION` paths resolve (count by `len()`) | unit | `pytest tests/test_phase28_report.py -k obligation -x` | ❌ W0 | ⬜ pending |
| — | — | — | RPT-01 / SC2 | T-28-register | prose checks route through `normalized`; AST register includes Phase 28 files | unit | `pytest tests/test_phase25_correction.py::test_the_register_is_three_files_wide -x` | ✅ (edit) | ⬜ pending |
| — | — | — | RPT-01 | T-28-heading | appended section keeps every prior `## ` heading in order; README bullets add no heading | existing | `pytest tests/test_phase18_docs.py tests/test_phase15_docs.py -q` | ✅ | ⬜ pending |
| — | — | — | RPT-01 / SC2 | T-28-prov | source digests in block == `sha256(read_bytes())` at HEAD | unit | `pytest tests/test_phase28_report.py -k provenance -x` | ❌ W0 | ⬜ pending |
| — | — | — | RPT-03 / SC3 | T-28-deps | `[project].dependencies` equal at `v1.0`, `v2.0`, `v3.0`, HEAD | unit (git + tomllib) | `pytest tests/test_package.py -k dependencies -x` | ❌ (add) | ⬜ pending |
| — | — | — | RPT-03 / SC3 | T-28-sha | sha pin renamed (D-26), still bytes-equal | unit | `pytest tests/test_package.py -x` | ✅ (rename) | ⬜ pending |
| — | — | — | RPT-03 / SC3 | T-28-ledger | ledger schema: six required keys, closed disposition domain, `FIXED` rows name a collectable test node id, counts = `len()` | unit | `pytest tests/test_phase28_ledger.py -x` | ❌ W0 | ⬜ pending |
| — | — | — | RPT-03 / SC3 | T-28-docstr | D-32 docstring fixes hold | unit | `pytest tests/test_perplexity.py tests/test_phase16_driver.py -k docstring -x` | ❌ (add) | ⬜ pending |
| — | — | — | SC4 | T-28-confound | confound strings are the record's own (`adversarial_no_replay.*`, `amended_criterion`, §12.5c slice under `normalized`) | unit | `pytest tests/test_phase28_report.py -k confound -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase28_report.py` — byte-identity, template scan (+ planted RED), obligation resolution, constants, provenance, confound, lead/expectation
- [ ] `tests/test_phase28_prereg.py` — D-05 ancestry (copy `_assert_frozen_before` shape from `tests/test_phase27_prereg.py:74-111`) — or fold into the file above
- [ ] `tests/test_phase28_ledger.py` — schema / domain / `FIXED`-has-test / `len()` counts
- [ ] `tests/test_package.py` — D-25 dependencies test added, D-26 pin rename
- [ ] D-32 docstring tests (`tests/test_perplexity.py`, `tests/test_phase16_driver.py`, or a new small file)
- [ ] Framework install: none — pytest present

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `gsd-sdk query audit-open` count drops from 9 to the intended residue; `verify.artifacts` on the five Phase-19 plans passes | D-31 / D-39 | GSD CLI state, not pytest-reachable | `gsd-sdk query audit-open`; `for p in .planning/phases/19-*/19-{08,09,12,13,16}-PLAN.md; do gsd-sdk query verify.artifacts "$p"; done` — record outputs in the ledger evidence |
| Green CI on `origin/main` after push | D-38 | Requires network + push; human checkpoint | `gh run list --branch main --limit 1` → run id into ledger |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s per task
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
