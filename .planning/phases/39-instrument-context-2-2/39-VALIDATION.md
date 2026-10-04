---
phase: 39
slug: instrument-context-2-2
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-10-04
---

# Phase 39 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Source: 39-RESEARCH.md
> §Validation Architecture, amended by the plan-time rulings D-23..D-29 in 39-CONTEXT.md.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 in `.venv` (Python 3.11), CPU-only, zero skips in Phase 39 files |
| **Config file** | `pyproject.toml` (`make test` = `.venv/bin/pytest -q`) |
| **Quick run command** | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase39_prereg.py tests/test_phase39_ctx.py` |
| **Cross-phase guards** | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase35_prereg.py tests/test_phase36_caps.py tests/test_phase36_ledger.py tests/test_phase21_sc5.py tests/test_lora_inject.py tests/test_phase25_driver.py tests/test_phase38_prereg.py tests/test_phase38_rank.py` |
| **Full suite command** | `LOG=<scratchpad>/suite39.log; nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` plus a `run_in_background` waiter `until grep -q '^EXIT=' "$LOG"; do sleep 60; done` (Bash caps at 600 s) |
| **Estimated runtime** | quick ~60 s; guards ~2-3 min; full ~46-49 min (Phase 38: 4103 passed / 4 skipped) |

---

## Sampling Rate

- **After every task commit:** quick run + cross-phase guards
- **After every wave AND after each `results/phase39_*` / ledger commit:** full suite (records surface latent reds)
- **Before `/gsd:verify-work`:** full suite green on the committed state
- **Max feedback latency:** ~180 s (quick + guards)

---

## Per-Requirement Verification Map

| Req / Decision | Behavior | Test Type | Automated Command | File Exists | Status |
|---|---|---|---|---|---|
| CTX-01 / SC1 | `E6_ENTRY_SUBSET` = all 216 entries (tuple, derived not typed), filled once in `scripts/phase39_prereg.py`, consumes probe e1/e6; ordering legs, slot census, caps owner exec green | unit + census | `pytest tests/test_phase39_prereg.py -k "entry or fill"` ; `pytest tests/test_phase35_prereg.py -k "slot_census or slot_ordering"` ; `pytest tests/test_phase36_caps.py -k owner` (one invocation per file: pytest keeps only the last `-k`) | ❌ W0 | ⬜ pending |
| SC4 | prereg + test first-added before every `results/phase39_*`; records write-once | git ancestry | `pytest tests/test_phase39_prereg.py -k "frozen or first_added or records_at_commit"` | ❌ W0 | ⬜ pending |
| CTX-02 gate 2 (D-19) | 8 A2 records hash to pins (7 from cap_rulings + adapter-off); `_pooled_rows` reproduces committed counts; tamper → STOP | unit (real tracked JSON) | `pytest tests/test_phase39_prereg.py -k "gate2 or a2_sha"` | ❌ W0 | ⬜ pending |
| CTX-02 gate 1 (D-18) | 64 committed anchor ranks reproduced before new scoring; mismatch → GATE_FAILED | unit (fake model) | `pytest tests/test_phase39_ctx.py -k gate` | ❌ W0 | ⬜ pending |
| CTX-02 (a) gen (D-04..D-08, D-28) | anchor ids == value_span_nll context; seeds `i*K`, `K-1` samples, T/top-p from phase14_recall; forbid digest; 48 completions kept | unit (stubbed draw_all) | `pytest tests/test_phase39_ctx.py -k anchor` | ❌ W0 | ⬜ pending |
| CTX-02 (b) NLL (D-23, D-23a/b) | context = `_guarded_span(entry)` + whole value; per-token NLL kept; taught suffix sum after `realized_injection`; 216 × |R| per reading; (ii) `cleared[:7]` on all 8 adapters (D-26) | unit (call log) | `pytest tests/test_phase39_ctx.py -k "question or minted or suffix"` | ❌ W0 | ⬜ pending |
| CTX-03 (D-13..D-16, D-24, D-25) | truth table: 4 classes + NO_DISAGREEMENT, collapse and damage separately; R_q lost on n1 (collapse n1 = 0; damage drop > MARGIN, strict); ALREADY_AT_K0 / UNREACHABLE_AT_SIZE incl. n1(k0) < 9 and G_q reachability; person k8 tie; adapter-off and (ii) never in classes | unit (pure) | `pytest tests/test_phase39_prereg.py -k "classify or lost or reachab"` | ❌ W0 | ⬜ pending |
| D-33 (Phase 38 precedent) | committed formula pre/n - post/n stands; at n = 27 the four rounding-decided exact 8-drops (15,7) (17,9) (19,11) (21,13) are LOST and (26,18) INTACT; the record's drop-formula audit over R_q n1, G_a, G_q names every rounding tie and exact tie, criterion False | unit | `pytest tests/test_phase39_prereg.py -k lost` ; `pytest tests/test_phase39_ctx.py -k drop` | ❌ W0 | ⬜ pending |
| D-11 / D-26 / D-30 | quote verbatim (two-line join, from 62af2fe); projection computed = 0.7293568082878159 (D-26 + doubly scored gate, D-30) ≤ stop 0.7424221732238463; `front_hours.E6` reproduced; caps called without `adapters` | unit + AST | `pytest tests/test_phase39_prereg.py -k "d11 or arithmetic"` ; `pytest tests/test_phase39_ctx.py -k caps` | ❌ W0 | ⬜ pending |
| D-30 / D-30a | copy of span_nll_from_ids: nll_sum/nll_mean bitwise equal to the pinned function (CPU test; on MPS every gate cell scored by both, any difference → STOP before new scoring); per-token sums descriptive only, never read by ranks/n1/events (AST); suffix sum from a suffix mask in the same forward, bitwise equal to pinned `span_nll_from_ids(prompt_ids, suffix)` | unit + AST | `pytest tests/test_phase39_ctx.py -k "copy or equality or per_token or suffix"` | ❌ W0 | ⬜ pending |
| D-17 / D-23c / D-29 | predicted rate: (a) exp(-whole-value sum), (b) exp(-suffix sum); descriptive only | unit | `pytest tests/test_phase39_ctx.py -k predicted` | ❌ W0 | ⬜ pending |
| D-21 / D-27 run shape | refusals before ledger start (dirty tree, open attempt, require_launch, non-MPS real root, inputs, digests, gate 2, prereg sha drift since rehearsal); write-once sidecars; crash reconcile; one real CPU rehearsal record fed to the report | unit + rehearsal | `pytest tests/test_phase39_ctx.py -k "preflight or refus or crash or rehearsal or main"` | ❌ W0 | ⬜ pending |
| D-20 | CPU cross-check NLL/rank only; differing cells counted; criterion False | unit | `pytest tests/test_phase39_ctx.py -k crosscheck` | ❌ W0 | ⬜ pending |
| Report | rendered from committed record only, byte-equal to `render_report(record)`; denominators on every class table; not-measured list (|R| > 8, B1′, D-12/D-23d) | unit | `pytest tests/test_phase39_ctx.py -k report` | ❌ W0 | ⬜ pending |
| Hygiene | no `inject_lora`, no `os.replace`, no `== 10` in tests; instruments imported not redefined (AST, not grep); every function called by a test; zero skips | AST census | `pytest tests/test_phase39_prereg.py tests/test_phase39_ctx.py -k "census or ast or skips"` ; `pytest tests/test_lora_inject.py tests/test_phase21_sc5.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky. Task IDs are bound by the plans' `<automated>` blocks.*

---

## Wave 0 Requirements

- [ ] `tests/test_phase39_prereg.py` — ancestry, census, D-11 quote, arithmetic, A2 pins, gate 2 on real tracked JSON, classifier truth table
- [ ] `tests/test_phase39_ctx.py` — fake-model rig with tmp root, tmp ledger, stubbed `adapter_digests` / `tracked_files` (no checkpoint dependency; ubuntu CI)

No framework install needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Rafael's literal "approved" before each record/ledger commit and before the MPS launch | SC4 | human gate | checkpoint presents the artifact; commit only after the word |
| The MPS run | CTX-02 / D-21 | device + ledger | `nohup caffeinate -dims .venv/bin/python scripts/phase39_ctx.py run`; stop (a) checked by `require_launch` only |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 180 s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
