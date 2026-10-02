---
phase: 36
slug: mps-cost-probes-and-budget-commitment
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-10-02
---

# Phase 36 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `36-RESEARCH.md` §"Validation Architecture", amended by the 36-CONTEXT Addendum
> (D-18: two K = 48 runs, K = 16 = first-16-draw prefix, no draws/hits in any record or log;
> D-19: E3 times recall only, E4 canary stage priced from `phase26_canary_sources.json`).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest in the Python 3.11 `.venv` (never the system 3.14), CPU-only in CI |
| **Config file** | `pyproject.toml` (`testpaths = ["tests"]`, `pythonpath = ["."]`) + `tests/conftest.py` |
| **Quick run command** | `.venv/bin/pytest -q tests/test_phase36_*.py tests/test_phase35_prereg.py -p no:cacheprovider` |
| **Full suite command** | `make test` (~25 min: launch with `nohup` and a `grep '^EXIT='` waiter, because Bash caps at 600 s; committed clean tree only) |
| **Estimated runtime** | quick ~60 s; full ~1500 s |

---

## Sampling Rate

- **After every task commit:** the quick run command, plus `ruff check . && ruff format --check .`
- **After every plan wave:** the full suite on a committed, clean tree — never while the LaunchAgent probe run is live
- **Before `/gsd:verify-work`:** full suite green after the budget commit (or after the halt checkpoint), so the real-repo ordering legs (a)/(b)/(c) and the slot census run live
- **Max feedback latency:** 60 seconds (quick run)

---

## Per-Requirement Verification Map

| Req / Decision | Behavior | Test Type | Automated Command | File Exists | Status |
|----------------|----------|-----------|-------------------|-------------|--------|
| COST-01 / SC4 | Phase 36 prereg precedes every `results/phase36_*` (honest-green at zero, natural RED available) | unit (git) | `pytest tests/test_phase36_prereg.py -k frozen` | ❌ W0 | ⬜ pending |
| COST-01 / D-17 | Every D-17/D-19 entry has exactly four fields, a known kind, no proposer; preferences labelled; P22 holds at T = 800 via `p22_onset_sigma` | unit + AST | `pytest tests/test_phase36_prereg.py` | ❌ W0 | ⬜ pending |
| COST-01 / D-01 / D-18 | Probe records carry per-stage seconds, repetition counts, provenance, a gates-nothing marker, and NO reading key (no recall/rank/hit/draw text) — JSON-key gate | unit | `pytest tests/test_phase36_probe.py -k record` | ❌ W0 | ⬜ pending |
| D-18 | E1 record keeps the two fixed-cost samples separately; K = 16 cost = fixed + first 16 draws/question; no pin stdout reaching the log carries a reading | unit | `pytest tests/test_phase36_probe.py -k e1` | ❌ W0 | ⬜ pending |
| COST-01 | Probe isolation: prefix/arm/path guards; no collision with later-phase result paths or stray globs | unit | `pytest tests/test_phase36_probe.py -k isolation` | ❌ W0 | ⬜ pending |
| COST-01 | Live path through the REAL stages at CPU fixture scale (no dry-run-only coverage) | integration (CPU) | `pytest tests/test_phase36_probe.py -k live` | ❌ W0 | ⬜ pending |
| COST-01 | Write-once emit; dirty-tree refusal first; run-sha vs HEAD refusal | unit | `pytest tests/test_phase36_probe.py -k emit` | ❌ W0 | ⬜ pending |
| COST-01 / D-16 | plist mirrors the Phase 31 agent (`caffeinate -dims`, heartbeat, logs/, RunAtLoad/KeepAlive false) | unit | `pytest tests/test_phase36_probe.py -k plist` | ❌ W0 | ⬜ pending |
| D-02 / D-04 | 25% comparator table maps each probe stage to its historical key; divergence > 25% refuses the budget derivation | unit | `pytest tests/test_phase36_budget.py -k divergence` | ❌ W0 | ⬜ pending |
| COST-02 / D-10 / D-13 / D-14 / D-19 | High bound per front; stop line `min(1.5Σ, 90)`; S = 5; E4 = 3 × (T = 200 train + 5556.24 s); caps derived | unit | `pytest tests/test_phase36_budget.py -k derive` | ❌ W0 | ⬜ pending |
| COST-02 | Consumer fed a real producer record: derived values pass `phase35_prereg.fill("v6_budget_and_stop_line", ...)`; the budget then passes `fill("e2_S")` / `fill("e1_checkpoint_grid")` | integration | `pytest tests/test_phase36_budget.py -k consumer` | ❌ W0 | ⬜ pending |
| COST-02 / SC3 / D-15 | Σ > 90 → HALT; cut table in D-15 order (r1b, e1_core last) with hours saved + question lost; no row applied without Rafael; S < 3 never offered; nothing written under `results/phase36_*` | unit | `pytest tests/test_phase36_budget.py -k halt` | ❌ W0 | ⬜ pending |
| COST-02 | Ancestry: probes ≺ fill file ≺ budget | unit (git) | `pytest tests/test_phase36_budget.py -k ancestry` + `tests/test_phase35_prereg.py::test_slot_ordering_is_green_on_the_real_repo` | ❌ / ✅ | ⬜ pending |
| COST-02 | Committed budget recomputes from committed probe records | unit | `pytest tests/test_phase36_budget.py -k recompute` | ❌ W0 | ⬜ pending |
| D-11 / D-12 / D-13 | Ledger: per-run grouping, torn tail, crashed run counted to last beat and flagged "sem registro de resultado", record wall-clock preferred; projection / 1.5× / stop-line refusals | unit | `pytest tests/test_phase36_ledger.py` | ❌ W0 | ⬜ pending |
| D-09 | Caps: `check_unit_caps` refusals; owner-fill-file scan honest-green at zero, RED on a planted overrun | unit | `pytest tests/test_phase36_caps.py` | ❌ W0 | ⬜ pending |
| Census | Phase 35 slot census and `_TRAIN_ARM_CALL_SITES` register stay green with the new files | existing | `pytest tests/test_phase35_prereg.py -k census tests/test_phase23_resume.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase36_prereg.py` — ancestry, entries, P22, zero skips, CPU-test census
- [ ] `tests/test_phase36_probe.py` — isolation, record builders, live CPU fixtures, emit, plist
- [ ] `tests/test_phase36_budget.py` — derive, consumer feed, halt/cut table, ancestry, recompute
- [ ] `tests/test_phase36_ledger.py`, `tests/test_phase36_caps.py`
- [ ] Register line(s) in `tests/test_phase23_resume.py::_TRAIN_ARM_CALL_SITES` for any new `train_arm(` call site

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| The probe run itself (real MPS timings) | COST-01 | Needs the M3 under the LaunchAgent | Load the plist, wait for the done line, read the probe records |
| 25% divergence read before the budget | D-02 / D-04 | A > 25% divergence is an investigation, not an automatic pass | Read the comparator table printed by the budget dry computation |
| Rafael's approved on the budget (or the cut table) | COST-02 / D-16 | Human decision | Checkpoint: present the dry numbers; commit fill + budget only after "approved" |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
