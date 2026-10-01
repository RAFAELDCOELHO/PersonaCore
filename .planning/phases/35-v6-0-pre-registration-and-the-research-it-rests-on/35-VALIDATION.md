---
phase: 35
slug: v6-0-pre-registration-and-the-research-it-rests-on
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-10-01
---

# Phase 35 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `35-RESEARCH.md` §"Validation Architecture". It is amended by CONTEXT D-14..D-17: no
> `proposer`/`adopted_by` field exists, so the PREREG-07 row below replaces the research's.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 in the Python 3.11 `.venv` (never the system 3.14) |
| **Config file** | `pyproject.toml` (`testpaths = ["tests"]`, `pythonpath = ["."]`) |
| **Quick run command** | `.venv/bin/pytest -q tests/test_phase35_prereg.py tests/test_phase29_prereg.py -p no:cacheprovider` |
| **Full suite command** | `make test` (~40 min: launch with `nohup` and a `grep '^EXIT='` waiter, because Bash caps at 600 s) |
| **Estimated runtime** | quick ~30 s; full ~2400 s |

---

## Sampling Rate

- **After every task commit:** the quick run command, plus `ruff check . && ruff format --check .`
- **After every plan wave:** the quick run command, plus `.venv/bin/python scripts/phase28_report.py check` and `.venv/bin/python scripts/phase34_report.py check` (both exit 0)
- **Before `/gsd:verify-work`:** full `make test` green on a committed, clean tree, with the skip count equal to the attributed pin (`tests/test_phase25_venue.py`)
- **Max feedback latency:** 60 seconds (quick run)

---

## Per-Requirement Verification Map

Task IDs are assigned by the planner; each task must cite the `-k` selector it turns green.

| Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|----------|-----------|-------------------|-------------|--------|
| PREREG-05 | The prereg's first add precedes every `results/phase36_*`..`phase45_*` (honest-green with zero v6.0 records) | git/ancestry | `pytest tests/test_phase35_prereg.py -k frozen_before -q` | ❌ W0 | ⬜ pending |
| PREREG-05 | `ARTIFACT_PATHSPECS` is derived from `V6_RESULT_PATHS` and disjoint from the `v5.0` tag's results | unit | `-k pathspecs` | ❌ W0 | ⬜ pending |
| PREREG-05 | The six closed pins are imported (AST Import nodes) and none is copied (literal census) | AST | `-k pins_imported` | ❌ W0 | ⬜ pending |
| PREREG-05 | The module imports without torch, phase19_erasure, phase18_extraction, phase26_canary or phase23_run (subprocess probe) | smoke | `-k without_torch` | ❌ W0 | ⬜ pending |
| PREREG-05 | `seed_list() is phase23_run.SEED_LADDER`, and the AST tuple at the file's first add (`git log --diff-filter=A`, = `5303819`) equals the live one | git+AST | `-k seed_ladder` | ❌ W0 | ⬜ pending |
| PREREG-05 | `e1_targets()` yields the 13/13 rows of `TARGET_RANKING`; the four names appear in no module `Constant` | unit+AST | `-k e1_targets` | ❌ W0 | ⬜ pending |
| PREREG-05 | `audit02_cut()` is the min over `results/phase26_canary.json` (== 3.7965357228934966); `e4_runs` is strict `>` | unit | `-k audit02` | ❌ W0 | ⬜ pending |
| PREREG-05 | R1a: k = `len(ablated_components)` = 78; the 77.6370113463966% re-derives; the margin is read from `phase19_noise_floors.json::margin_at_gate` | unit | `-k r1a` | ❌ W0 | ⬜ pending |
| PREREG-05 | Slot registry: every slot has its fields, including the 6 from D-15. Census checks (undeclared slot / wrong owner phase / different rule / ordering minus declared input records) are green on the real tree and RED on planted owner files | AST/git | `-k slot` | ❌ W0 | ⬜ pending |
| PREREG-05 | The E2 `S` rule refuses S > `len(seed_list())` (D-06); the E3 grid rule encodes 4 recipes × σ ∈ {0, 0.5, 1} plus the v4.0-control reuse condition (D-17) | unit | `-k "e2_S or e3_grid"` | ❌ W0 | ⬜ pending |
| PREREG-06 | Every entry has exactly {value, derivation, kind, source}; `kind` ∈ {derived, preference}; F_Y/F_C are `preference`, bound by `Attribute` to `mitigation_gate` | unit+AST | `-k entries` | ❌ W0 | ⬜ pending |
| PREREG-07 | No entry carries a `proposer` or `adopted_by` key (D-14); "selected by THE USER, verbatim" is absent from entry values (AST over dict Constants, not docstrings) | unit+AST | `-k no_proposer` | ❌ W0 | ⬜ pending |
| PREREG-08 | The new test file has zero skip markers (AST); the attributed CI skip pin in `test_phase25_venue.py` is unchanged | AST + full suite | `-k no_skips`; full `make test` | ❌ W0 / ✅ | ⬜ pending |
| PREREG-09 | One-run bound: Appendix D pin `(1000, 100, 75, 1e-4, 0.05)` → 0.673 and the p. 28 pin → 2.675, both within 1e-3; refuses v > r, r > m and bool inputs | unit | `-k one_run` | ❌ W0 | ⬜ pending |
| PREREG-09 | Basic composition: `curve_total([1.5, 2.25, 0.25], delta=mitigation_unit.DELTA) == (4.0, 3 * 1e-5)`; `SELECTION_ACCOUNTED is False` (Papernot–Steinke hypotheses fail for E3) | unit | `-k composition` | ❌ W0 | ⬜ pending |
| PREREG-09 | The research note exists and cites `2305.08846v1` (Thm 5.2 / Cor 5.4 / App. D) and `2110.03620v2` (Thm 2 / Thm 6) with pages | doc | `-k research_note` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase35_prereg.py`: covers PREREG-05..09; reuses `_assert_frozen_before`, `_git` and the AST helpers from `tests/test_phase29_prereg.py`
- [ ] `.planning/research/` PREREG-09 note (D-10)

No framework install is needed.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
