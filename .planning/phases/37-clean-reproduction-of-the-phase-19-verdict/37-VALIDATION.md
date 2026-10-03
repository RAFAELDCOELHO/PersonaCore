---
phase: 37
slug: clean-reproduction-of-the-phase-19-verdict
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-10-03
---

# Phase 37 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `37-RESEARCH.md` §"Validation Architecture" (every number measured 2026-10-03 in `.venv`).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x in the Python 3.11 `.venv` (never the system 3.14), CPU-only |
| **Config file** | `pyproject.toml` + `tests/conftest.py` |
| **Quick run command** | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase37_prereg.py tests/test_phase37_routes.py tests/test_phase37_r1a.py tests/test_phase37_r1b.py tests/test_phase35_prereg.py` |
| **Targeted regression** | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase35_prereg.py tests/test_phase36_prereg.py tests/test_phase36_ledger.py tests/test_phase36_budget.py tests/test_phase19_erasure.py tests/test_phase19_correction.py tests/test_phase16_prereg.py tests/test_erasure_kstar_run.py tests/test_lora_inject.py tests/test_phase25_driver.py tests/test_phase21_sc5.py` (~100 s) |
| **Full suite command** | `.venv/bin/pytest -q -p no:cacheprovider` under `nohup` with a `grep '^EXIT='` waiter (Bash caps at 600 s); committed clean tree only |
| **Estimated runtime** | quick < 60 s (target); targeted ~100 s; full ~42–44 min |

---

## Sampling Rate

- **After every task commit:** quick run (or the touched test files) + `ruff check . && ruff format --check .`
- **After every plan wave:** quick + targeted regression
- **After each record commit and at the phase gate:** full suite, background, clean tree — never while the R1b LaunchAgent is live
- **Before `/gsd:verify-work`:** full suite green, zero new skips (`test_phase25_venue.py` pins skip counts)
- **Max feedback latency:** ~100 s (targeted)

---

## Per-Requirement Verification Map

| Req / Decision | Behavior | Test Type | Automated Command | File Exists | Status |
|---|---|---|---|---|---|
| REPRO-01 | R1a asserts k 78, 0/27, 7/7 beyond `e1_condition_b_margin()`, 77.6370113463966, verdict FAILURE + recorded reasons; exit 0 | unit (CPU, committed records) | `pytest tests/test_phase37_r1a.py -x` | ❌ W0 | ⬜ pending |
| REPRO-01 | divergence halts (perturbed record → SystemExit naming the key, nothing written) | unit | same | ❌ W0 | ⬜ pending |
| REPRO-01 / D-10 | write-once record: refuses overwrite/dirty tree, four numbers, input SHA-256 from bytes, git sha; refuses unless prereg tracked | unit | same | ❌ W0 | ⬜ pending |
| REPRO-01 | AST: imports pin + gate; `render_verdict` sole verdict route; no `report()` call; no `results/phase19_` write | AST | same | ❌ W0 | ⬜ pending |
| REPRO-02 / D-09 A–D | natural reds on committed inputs: False / 0.2 / {14} / TypeError (no message match) | unit | `pytest tests/test_phase37_routes.py -x` | ❌ W0 | ⬜ pending |
| REPRO-02 / D-09 A–D | swapping one route for the unrouted pin path makes `rederive` diverge (parametrized) | unit | same | ❌ W0 | ⬜ pending |
| REPRO-02 / D-08 E | wrapper passes \|R\| = 8 = curve `reference_set_size`; twin = 6; re-sweep k(8)=78, k(6)=120 | unit (no model) | same | ❌ W0 | ⬜ pending |
| D-08 / ERASE-08 | `scripts/phase19_erasure.py` and `scripts/erasure_gate.py` byte-unchanged vs committed anchors | unit | same | ❌ W0 | ⬜ pending |
| REPRO-03 / D-01 | slot filled once in `scripts/phase37_prereg.py`; census green | unit | `pytest tests/test_phase37_prereg.py -x` | ❌ W0 | ⬜ pending |
| REPRO-03 / D-02 | tolerance keys == `R1A_ASSERTIONS` keys; three zeros `preference`; destroyed_pct `derived` = `MARGIN_K*floor/g0*100` from records (repr `0.8396203493271365`); no float literal (AST) | unit + AST | same | ❌ W0 | ⬜ pending |
| REPRO-03 / D-03, D-04, D-07 | four-field entries `{value, derivation, kind, source}`, no proposer; prereg torch-free | unit | same | ❌ W0 | ⬜ pending |
| SC4 | prereg + its test frozen before every `results/phase37_*` (ancestry, natural-RED non-vacuity) | git ancestry | same + `tests/test_phase35_prereg.py` | ❌ W0 | ⬜ pending |
| D-05 / D-07 | decision: same set → run (positions moved counted); k ≠ 78 or set differs → NOT_REPLICATED, arm not called | unit (CPU) | `pytest tests/test_phase37_r1b.py -x` | ❌ W0 | ⬜ pending |
| D-03 / D-04 | committed arm fed as replica → REPLICATED, 0 differing draws; perturbed → NOT_REPLICATED with per-fact context vs 0.14814814814814814 | unit (real producer record) | same | ❌ W0 | ⬜ pending |
| D-11..D-13 | `main()` end to end (pin monkeypatched): `require_launch` before `append("start")`; end names `results/phase37_r1b.json`; `provenance.run`; explicit `record_path` | unit (tmp ledger) | same | ❌ W0 | ⬜ pending |
| real tree | `test_phase36_ledger.py::test_every_tracked_v6_mps_record_has_a_launch_line` green after record commits | existing | `pytest tests/test_phase36_ledger.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase37_prereg.py` — ancestry, entries, fill, census, torch-free
- [ ] `tests/test_phase37_routes.py` — A–E natural reds + swaps, pin/gate byte-unchanged, AST gates
- [ ] `tests/test_phase37_r1a.py` — REPRO-01 assertions + write-once
- [ ] `tests/test_phase37_r1b.py` — D-07/D-03/D-04 logic, consumer fed the committed record, ledger wiring, plist

No framework install needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| R1b MPS replica run (~1.26 h) | REPRO-03 | MPS-only, long, needs Rafael's "approved" and the Phase 36 ledger | After approved: `require_launch("R1b")`, `launchctl kickstart` the agent, then `python scripts/phase36_ledger.py report` |
| Record commits | REPRO-01/03, SC4 | Committed only after Rafael writes "approved" | Orchestrator checkpoint |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 100s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
