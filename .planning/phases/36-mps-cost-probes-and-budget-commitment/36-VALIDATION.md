---
phase: 36
slug: mps-cost-probes-and-budget-commitment
status: complete
nyquist_compliant: true
wave_0_complete: true
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
| **Quick run command** | `.venv/bin/python -m pytest -q tests/test_phase36_*.py tests/test_phase35_prereg.py -p no:cacheprovider` (383 passed, ~78 s) |
| **Full suite command** | `.venv/bin/python -m pytest -q -p no:cacheprovider` launched with `nohup` and a `grep '^EXIT='` waiter (Bash caps at 600 s); committed clean tree only |
| **Estimated runtime** | quick ~78 s; full ~2530 s (41:46–43:06 measured in this phase) |

---

## Sampling Rate

- **After every task commit:** the quick run command (or the touched test files), plus `ruff check . && ruff format --check .`
- **After every plan wave:** targeted re-run by the orchestrator; the full suite on a committed, clean tree at the zero-records state (before the run), on the probes-only state, and on the fill + budget state — never while the LaunchAgent probe run is live
- **Before `/gsd:verify-work`:** full suite green after the budget commit, so the real-repo ordering legs (a)/(b)/(c) and the slot census run live
- **Max feedback latency:** quick run ~78 s (above the 60 s target; the two CPU live fixtures dominate)

---

## Per-Requirement Verification Map

| Req / Decision | Behavior | Test Type | Automated Command | File Exists | Status |
|----------------|----------|-----------|-------------------|-------------|--------|
| COST-01 / SC4 | Phase 36 prereg precedes every `results/phase36_*` (honest-green at zero, natural RED available) | unit (git) | `pytest tests/test_phase36_prereg.py -k frozen` (1: `test_phase36_prereg_is_frozen_before_every_phase36_record`) | ✅ | ✅ green |
| COST-01 / D-17 | Every D-17/D-19 entry has exactly four fields, a known kind, no proposer; preferences labelled; P22 holds at T = 800 via `p22_onset_sigma` | unit + AST | `pytest tests/test_phase36_prereg.py` (17) | ✅ | ✅ green |
| COST-01 / D-01 / D-18 | Probe records carry per-stage seconds, repetition counts, provenance, a gates-nothing marker, and NO reading key — JSON-key gate | unit | `pytest tests/test_phase36_probe.py -k record` (23, incl. `test_record_gate_refuses_readings_and_free_text[0-6]`) | ✅ | ✅ green |
| D-18 | E1 record keeps the two fixed-cost samples separately; K = 16 cost = fixed + first 16 draws/question; no pin stdout reaching the log carries a reading | unit | `pytest tests/test_phase36_probe.py -k e1` (19, incl. `test_e1_run_separates_fixed_and_prefix_cost`, `test_live_e1_stdout_holds_no_reading`) | ✅ | ✅ green |
| COST-01 | Probe isolation: prefix/arm/path guards; no collision with later-phase result paths or stray globs | unit | `pytest tests/test_phase36_probe.py -k isolation` (3) | ✅ | ✅ green |
| COST-01 | Live path through the REAL stages at CPU fixture scale (no dry-run-only coverage) | integration (CPU) | `pytest tests/test_phase36_probe.py -k live` (23; `main(['run'])` reaches all five fronts) | ✅ | ✅ green |
| COST-01 | Write-once emit; dirty-tree refusal first; run-sha vs HEAD refusal (WR-02) | unit | `pytest tests/test_phase36_probe.py -k emit` (9) | ✅ | ✅ green |
| COST-01 / D-16 | plist mirrors the Phase 31 agent (`caffeinate -dims`, heartbeat, logs/, RunAtLoad/KeepAlive false) | unit | `pytest tests/test_phase36_probe.py -k plist` (1) | ✅ | ✅ green |
| D-02 / D-04 | 25% comparator table maps each probe stage to its historical key; divergence > 25% refuses the budget derivation | unit | `pytest tests/test_phase36_budget.py -k divergence` (4) | ✅ | ✅ green |
| COST-02 / D-10 / D-13 / D-14 / D-19 | High bound per front; stop line `min(1.5Σ, 90)`; S = 5; E4 = 3 × (T = 200 train + 5556.24 s); caps derived | unit | `pytest tests/test_phase36_budget.py -k derive` (23) | ✅ | ✅ green |
| COST-02 | Consumer fed a real producer record: derived values pass `phase35_prereg.fill("v6_budget_and_stop_line", ...)`; the budget then passes `fill("e2_S")` / `fill("e1_checkpoint_grid")` | integration | `pytest tests/test_phase36_budget.py -k consumer` (1) | ✅ | ✅ green |
| COST-02 / SC3 / D-15 | Σ > 90 → HALT; cut table in D-15 order (r1b, e1_core last) with hours saved + question lost; no row applied without Rafael; S < 3 never offered; nothing written under `results/phase36_*` | unit | `pytest tests/test_phase36_budget.py -k halt` (3) | ✅ | ✅ green |
| COST-02 | Ancestry: probes ≺ fill file ≺ budget | unit (git) | `pytest tests/test_phase36_budget.py -k ancestry` + `tests/test_phase35_prereg.py::test_slot_ordering_is_green_on_the_real_repo` | ✅ | ✅ green |
| COST-02 | Committed budget recomputes from committed probe records | unit | `pytest tests/test_phase36_budget.py -k recompute` (1) | ✅ | ✅ green |
| D-11 / D-12 / D-13 | Ledger: per-run grouping, torn tail, crashed run counted to last beat and flagged "sem registro de resultado", record wall-clock preferred; projection / 1.5× / stop-line refusals | unit | `pytest tests/test_phase36_ledger.py` (45) | ✅ | ✅ green |
| D-09 | Caps: `check_unit_caps` refusals; owner-fill-file scan honest-green at zero, RED on a planted overrun | unit | `pytest tests/test_phase36_caps.py` (35) | ✅ | ✅ green |
| Census | Phase 35 slot census and `_TRAIN_ARM_CALL_SITES` register stay green with the new files | existing | `pytest tests/test_phase35_prereg.py -k census` (4) + `tests/test_phase23_resume.py::test_resume_from_none_is_inert` (holds the register-count assertion) | ✅ | ✅ green |
| Review CR-01 | A re-probe's superseded end line is priced by its own span; a re-probe is refused once its record exists | unit | `pytest tests/test_phase36_ledger.py -k superseded` (1) + `tests/test_phase36_probe.py -k reprobe` (1) | ✅ | ✅ green |
| Review WR-01 | A2-context priced from the E1 record; a stale E6 copy is surfaced, not a permanent refusal | unit | `pytest tests/test_phase36_budget.py -k surfaces_an_e6_record` (1) | ✅ | ✅ green |
| Review WR-02 | A crashed attempt's session never poisons a clean rerun | unit | `pytest tests/test_phase36_probe.py -k poisons` (1) | ✅ | ✅ green |
| Review WR-03 | `emit-all` never closes a live attempt | unit | `pytest tests/test_phase36_probe.py -k live_attempt` (1) | ✅ | ✅ green |
| Review WR-04 / T-36-05 | Every reader of the real ledger proves it append-only; rewritten or absent ledger refused | unit | `pytest tests/test_phase36_ledger.py -k append_only` (3) + `tests/test_phase36_probe.py -k "rewritten or absent_ledger"` (2) | ✅ | ✅ green |
| Review WR-05 | `dry` applies ruled cuts once in the E3-recipes loop | unit | `pytest tests/test_phase36_budget.py -k cuts_once` (1) | ✅ | ✅ green |
| COST-02 / Rafael's ruling item 2 | `E6.a2_regenerated_entries`: refused below `entries` without the cap ruling, accepted with it, refused above `entries`; scoring and anchor terms kept | unit | `pytest tests/test_phase36_budget.py -k a2_regenerated` (1) | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_phase36_prereg.py` — ancestry, entries, P22, zero skips, CPU-test census (9f75933)
- [x] `tests/test_phase36_probe.py` — isolation, record builders, live CPU fixtures, emit, plist (36-03..05)
- [x] `tests/test_phase36_budget.py` — derive, consumer feed, halt/cut table, ancestry, recompute (36-06)
- [x] `tests/test_phase36_ledger.py`, `tests/test_phase36_caps.py` (36-02)
- [x] Register line in `tests/test_phase23_resume.py::_TRAIN_ARM_CALL_SITES` for `train_e2_rep` (104bbc8)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions | Done |
|----------|-------------|------------|-------------------|------|
| The probe run itself (real MPS timings) | COST-01 | Needs the M3 under the LaunchAgent | Load the plist, wait for the done line, read the probe records | ✅ 2026-10-02, 18:48–22:28 UTC; records f7b9962..0d59b6d (36-07-SUMMARY) |
| 25% divergence read before the budget | D-02 / D-04 | A > 25% divergence is an investigation, not an automatic pass | Read the comparator table printed by the budget dry computation | ✅ no gated row exceeds; max 6.45% (E3 T = 800) |
| Rafael's approved on the budget (or the cut table) | COST-02 / D-16 | Human decision | Checkpoint: present the dry numbers; commit fill + budget only after "approved" | ✅ ruling + approved verbatim in 36-08-SUMMARY; fill 9a5718a, budget 6b57231 |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [ ] Feedback latency < 60s — quick run measured ~78 s (two CPU live fixtures); accepted, every targeted `-k` run above stays under 15 s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** signed off 2026-10-03 on HEAD `400e4f6` (full suite 3782 passed / 4 skipped / EXIT=0 at
`e72c17a`, the last code commit; verification passed 4/4 SC `ecdce31`). Every command above was run at
`400e4f6` and selected ≥ 1 test, all green.

## Validation Audit 2026-10-03

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Rows added at audit: the six review findings (CR-01, WR-01..WR-05, fixed 0d1b51a..be3aaa6) and Rafael's
E6 cap ruling (84af553), each with its own test. Known limitations carried (not gaps): IN-01/IN-02
from 36-REVIEW.md; `phase25_run.beat` has no torn-tail check (pinned module, ≤ 1 beat under-count).
