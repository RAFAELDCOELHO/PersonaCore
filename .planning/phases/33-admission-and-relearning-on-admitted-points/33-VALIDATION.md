---
phase: 33
slug: admission-and-relearning-on-admitted-points
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-28
---

# Phase 33 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: 33-RESEARCH.md § Validation Architecture, plus the plan-time rulings D-13..D-16 in 33-CONTEXT.md.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x in `.venv` (Python 3.11), CPU-only |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase33_admission.py` |
| **Guard set** | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase33_admission.py tests/test_phase29_prereg.py tests/test_phase27_prereg.py tests/test_phase30_points.py tests/test_phase25_driver.py tests/test_phase21_sc5.py` (~21 s without the new file) |
| **Full suite command** | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` + an `until grep -q '^EXIT=' $LOG` waiter (runs on the committed tree only) |
| **Estimated runtime** | quick: under 30 s; full: about 25 min |

---

## Sampling Rate

- **After every task commit:** the quick run command + `ruff check . && ruff format --check .`
- **After every plan wave:** the guard set
- **Before `/gsd:verify-work`:** the full suite must be green on the **committed** tree, after the record commit. The `results/` clean-tree probes are red while the record is untracked; that is expected.
- **Max feedback latency:** 30 s (quick)

---

## Per-Task Verification Map

The planner fills in the Task IDs. Rows are keyed by behavior.

| Task ID | Behavior | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|----------|-------------|-----------|-------------------|-------------|--------|
| 33-01-T2 | Constants and functions imported by reference from `phase29_prereg`; record path derived from `V5_RESULT_PATHS`; admission reaches `recall_threshold` | ADMIT-01 | unit + AST | `pytest tests/test_phase33_admission.py -k "by_reference or reaches" -x` | ❌ W0 | ⬜ pending |
| 33-01-T2 | `phase27_prereg.py` byte-unchanged; its ancestry guard green | ADMIT-01 | git | `pytest tests/test_phase27_prereg.py -k frozen -x` + new assert | partial | ⬜ pending |
| 33-01-T1 | Refusal order overwrite → committed-at-HEAD-but-absent (D-13, `git rev-parse --verify -q HEAD:<rel>`) → dirty, all before any digest | ADMIT-02 | unit | `pytest tests/test_phase33_admission.py -k refuses -x` | ❌ W0 | ⬜ pending |
| 33-01-T1 | Pathspec exclusion on an untracked record; sibling untracked still dirty; uncommitted deletion refused as committed-at-HEAD, both plain unlink and staged `git rm` (scratch repo) | ADMIT-02 | git (scratch) | `pytest tests/test_phase33_admission.py -k "pathspec or tracked_but_absent" -x` | ❌ W0 | ⬜ pending |
| 33-01-T2, 33-02-T1/T3 | Exactly one commit, touching only the record; checks shallow first (fails loudly); handles the written-untracked state | ADMIT-02 | git | `pytest tests/test_phase33_admission.py -k exactly_once -x` | ❌ W0 | ⬜ pending |
| 33-01-T2, 33-02-T3 | Record pinned to the frontier both ways; admission and scope re-derived live | ADMIT-02 | git + unit | `pytest tests/test_phase33_admission.py -k pinned -x` | ❌ W0 | ⬜ pending |
| 33-01-T2, 33-02-T3 | `module_sha256` equals live bytes; traced reach set ⊆ pinned modules (`mitigation_budget` added by hand) | ADMIT-02 | unit | `pytest tests/test_phase33_admission.py -k provenance -x` | ❌ W0 | ⬜ pending |
| 33-01-T2 | Git surface read-only (no add/commit/push in the module) | ADMIT-02 | AST | `pytest tests/test_phase33_admission.py -k git_surface -x` | ❌ W0 | ⬜ pending |
| 33-01-T1 | Every leg refuses on MOOT/REFUSED/CANDIDATE-UNREPLICATED/INCONCLUSIVE/absent/untracked/forged-ADMITTED and writes nothing | RELRN-06..09 | unit (parametrized) | `pytest tests/test_phase33_admission.py -k refuses_unless -x` | ❌ W0 | ⬜ pending |
| 33-01-T1 | Limitation bound from reasons/tallies; no "never exercised" / "apparatus built"; n64 never "held" | RELRN-06..09 | unit | `pytest tests/test_phase33_admission.py -k limitation -x` | ❌ W0 | ⬜ pending |
| 33-01-T2 | No `phase32_points` import in any form (AST, natural RED from a temporary copy) | D-12 | AST + runtime | `pytest tests/test_phase33_admission.py -k phase32_points -x` | ❌ W0 | ⬜ pending |
| 33-01-T2 | New files pass the accountant, `_wr05`, os.replace and `== 10` / `!= 10` censuses | (census) | existing | guard set | ✅ | ⬜ pending |
| 33-01-T3 | Full suite green on the committed 33-01 tree with the record absent (every repo-wide census, before the module is pinned); SUITE_SHA recorded; precondition of 33-02-T1 | ADMIT-02 | full suite | Full suite command → `EXIT=0` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase33_admission.py`: every row marked ❌ W0
- [ ] Helper copies (`_git`, `_docstring_nodes`, `_git_argv_subcommands`), copied as patterns and never imported across test modules

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live stderr capture (33-02-T1/T3) of every leg on the real record, before and after its commit: byte-identical, exit 1 | RELRN-06..09 | Spans the developer review checkpoint and the commit (27-05 precedent) | For each leg: `.venv/bin/python scripts/phase33_admission.py <leg> 2> e_<leg>_<state>; echo $?`, then `shasum -a 256` for each pair; record in the SUMMARY |
| Developer review (33-02-T2) of the written record before commit | ADMIT-02 | D-05 human checkpoint | `admit` prints verdict, reasons and control readings; the developer says "approved"; Claude commits the record alone |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
