---
phase: 13
slug: ewc-a-b-no-forgetting-experiment
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-08-01
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (275 tests collected, CPU-only, GPU-free by contract) |
| **Config file** | pyproject.toml / Makefile (`make test`) |
| **Quick run command** | `.venv/bin/python -m pytest tests/ -x -q` |
| **Full suite command** | `make test` (inside `.venv`) |
| **Estimated runtime** | quick ~15s; full ~60s (CPU-only) |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/python -m pytest tests/ -x -q`
- **After every plan wave:** Run `make test` (full 275+ suite — purity contract: `train()` untouched, all existing tests stay green)
- **Before `/gsd:verify-work`:** Full suite must be green + both arm CSVs, figures, samples, and report committed
- **Max feedback latency:** 120 seconds (test feedback; the two ~37-min training runs are evidence-committed, not test-run — see Manual-Only)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 13-01-01 driver | 01 | 1 | DEMO-04 | T-13-01/02/03 | refuse-to-rerun guard on all arm outputs; trusted-only torch.load | unit (inline) | `.venv/bin/python -c "import importlib.util,pathlib; s=importlib.util.spec_from_file_location('fab', 'scripts/finetune_ab.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); assert m.K==2 and m.LAMBDA_EWC==0.01 and not m.ewc_mitigates(5.0, 5.0-m.MARGIN)"` | ✅ inline | ⬜ pending |
| 13-01-02 tests | 01 | 1 | DEMO-04 | T-13-01 | guard + gate arithmetic + config identicality pinned by test | unit | `.venv/bin/python -m pytest tests/test_phase13_driver.py -x -q` | ❌ W0 (created by this task) | ⬜ pending |
| 13-01-03 preamble | 01 | 1 | DEMO-04 | T-13-03 | pre-registration committed before any arm runs (git SHA proof) | smoke | `grep -q "## Pre-Registration" results/phase13_ab_report.md && grep -q "666d096" results/phase13_ab_report.md && grep -q "0.068930" results/phase13_ab_report.md` | ✅ inline | ⬜ pending |
| 13-02-01 EWC arm | 02 | 2 | DEMO-04 | T-13-04/05/06 | Phase-12 evidence byte-untouched; D-11 margin cross-check | integration (inline) | `.venv/bin/python -c "import csv; rows=list(csv.DictReader(open('results/phase13_ewc/run.csv'))); assert rows[0]['step']=='0' and int(float(rows[-1]['step']))==4000; assert abs(float(rows[-1]['retention_ppl'])-3.891139975617828)<=0.13786, rows[-1]['retention_ppl']"` | ✅ inline | ⬜ pending |
| 13-02-02 naive arm | 02 | 2 | DEMO-04 | T-13-04/05 | schema identity across arms; finite retention values | integration (inline) | `.venv/bin/python -c "import csv; n=list(csv.DictReader(open('results/phase13_naive/run.csv'))); e=list(csv.DictReader(open('results/phase13_ewc/run.csv'))); assert n[0].keys()==e[0].keys(); assert int(float(n[-1]['step']))==4000; import math; assert all(math.isfinite(float(r['retention_ppl'])) for r in n if r['retention_ppl'])"` | ✅ inline | ⬜ pending |
| 13-03-01 plots | 03 | 3 | VIZ-01, VIZ-04 | T-13-08 | figures regenerable from committed CSVs; λ=0 point hardcoded-with-citation (Pitfall 1) | smoke | `.venv/bin/python -m pytest tests/test_phase13_plots.py -x -q && .venv/bin/python scripts/plot_phase13.py && test -s results/phase13_forgetting_curve.png && test -s results/phase13_frontier.png` | ❌ W0 (created by this task) | ⬜ pending |
| 13-03-02 samples | 03 | 3 | DEMO-04 (D-12) | T-13-07/09 | seeded one-run both-arms protocol; proxies over ALL generations | smoke (inline) | `.venv/bin/python -c "t=open('results/phase13_retention_samples.md').read(); assert 'REPRESENTATIVE' in t and 'naive' in t and 'ewc' in t and 'leakage' in t.lower()"` | ✅ inline | ⬜ pending |
| 13-04-01 results | 04 | 4 | DEMO-04 | T-13-10/11 | all cells from committed CSVs; pre-reg table byte-unchanged | smoke (inline) | `.venv/bin/python -c "t=open('results/phase13_ab_report.md').read(); assert '## 2×2 Result' in t and '## Gate Verdict' in t and '0.13786' in t and 'measured, not applied' in t and '3.891139975617828' in t"` | ✅ inline | ⬜ pending |
| 13-04-02 narrative | 04 | 4 | DEMO-04 | T-13-10 | D-09 reconciliation + threats-to-validity register present | smoke (inline) | `.venv/bin/python -c "t=open('results/phase13_ab_report.md').read(); assert '## Threats to Validity' in t and '## Reconciliation' in t and 'not demonstrable' in t and '2.107553' in t and 'phase13_frontier.png' in t and 'phase13_retention_samples.md' in t"` | ✅ inline | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase13_driver.py` — guard + gate-arithmetic + config-identicality units for DEMO-04 (created in Plan 13-01 Task 2, Wave 1, before any arm runs)
- [ ] `tests/test_phase13_plots.py` — smoke the plot functions into tmp_path for VIZ-01/04 (created in Plan 13-03 Task 1)

No framework install needed — pytest 8.x already in the venv; existing 275-test suite covers all shared infrastructure (`train()`, `EWCPenalty`, metrics).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| The two ~37-min training runs themselves | DEMO-04 | Long-running MPS training; same class as Phase 12's prod run — evidence-committed, not test-run | Execute `scripts/finetune_ab.py {ewc,naive}` per Plan 13-02; committed per-arm CSVs + SUMMARY-recorded gate inputs are the evidence. Step-250 twin check + D-11 endpoint cross-check bound the risk |
| Figure visual sanity (labels, dashed 2.1066 baseline, budget captions) | VIZ-01, VIZ-04 | Pixel content not assertable; smoke test covers "renders, non-empty" | Open both PNGs; check dashed baseline labeled as v1.0 headline 2.1066, VIZ-04 caption says "1250-step sweep endpoints", VIZ-01 says "4000-step arms" (Pitfalls 3/4) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (all 9 tasks carry one)
- [x] Wave 0 covers all MISSING references (`test_phase13_driver.py`, `test_phase13_plots.py`)
- [x] No watch-mode flags
- [x] Feedback latency < 120s (training runs excluded as evidence-committed manual items)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved (revision addressing checker WARNING 1, 2026-08-01)
