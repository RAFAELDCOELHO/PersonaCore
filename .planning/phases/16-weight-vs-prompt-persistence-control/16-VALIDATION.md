---
phase: 16
slug: weight-vs-prompt-persistence-control
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-12
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Infrastructure, sampling rate and Wave 0 are derived from `16-RESEARCH.md` §Validation
> Architecture. The Per-Task Verification Map is populated during execution, once plans
> assign task IDs.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 (already installed — no framework install needed) |
| **Config file** | `pyproject.toml` (PEP 621 installable); `tests/conftest.py` present |
| **Quick run command** | `.venv/bin/pytest tests/test_phase16_ladder.py tests/test_phase16_stats.py tests/test_phase16_driver.py tests/test_phase16_prereg.py tests/test_phase14_scoring.py -q` |
| **Full suite command** | `make test` (equivalently `.venv/bin/pytest -q`) |
| **Estimated runtime** | quick ~seconds; full suite ~2 min |

**All validation surfaces are CPU-only and GPU-free.** This phase ships no user-facing feature —
it ships a **measurement and a pre-registration**, so validation means exactly two things:
(1) CPU-only tests proving the instrument is correct *before* any long run, and (2) a structural
proof that the pre-registration preceded the run.

---

## Sampling Rate

- **After every task commit:** run the quick command above (CPU-only, seconds)
- **After every plan wave:** `make test`
- **Phase gate — stricter than the default:** the full suite must be green **before the ladder
  runs**, not merely before `/gsd:verify-work`. PERS-01 makes the ladder blocking, so a ladder run
  on an unvalidated instrument is unrecoverable: the numbers cannot be re-derived afterwards
  without breaking pre-registration.
- **Max feedback latency:** ~10 s (quick command)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| *(populated at execute time — plans not yet written)* | — | — | — | — | — | — | — | — | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Requirement → test surface** (from `16-RESEARCH.md` §Validation Architecture — the planner maps
these onto task IDs):

| Req | Surface | File |
|---|---|---|
| STAT-01 | cell statistic counts **questions**, not draws | `tests/test_phase16_ladder.py` ❌ W0 |
| STAT-02 | every proportion ships a denominator + bound; zero cells emit `rule_of_three`, never `0%` | `tests/test_phase16_ladder.py` ❌ W0 |
| STAT-04 | `pyproject.toml` byte-identical to its v2.0-close state | `tests/test_package.py` ⚠️ extend |
| STAT-05 | threshold literals equal their derivation; `licensed_headline()` imports constants, never retypes them | `tests/test_phase16_ladder.py` ❌ W0 |
| STAT-06 | exactly 6 comparisons enter Holm; sign-test enumeration reproduces 0.0078125 / 0.0703125 / 0.015625; ties count against | `tests/test_phase16_stats.py` ❌ W0 |
| PERS-01 | `licensed_headline()` is **total** over the rung lattice; all-fail branch returns the SC1 capability-deficit statement | `tests/test_phase16_ladder.py` ❌ W0 |
| PERS-02 | arms share `max_new_tokens` / `forbid_ids` / `stop_ids` / context length via one shared config object; `CONDITION_ORDER` locked | `tests/test_phase16_driver.py` ❌ W0 |
| PERS-03 | truncation cells derived from the dilution axis crossing `block_size`, not declared independently (D-27) | `tests/test_phase16_driver.py` ❌ W0 |
| PERS-04 | arm D pool is exactly the 20-value lexicon, chance floor literal **0.05**; scored by the same `contains_value` as A/B/C | `tests/test_phase16_driver.py` ❌ W0 |
| PERS-05 | `run_fairness_control` passes `item.seed_index` — behavioural **and** AST | `tests/test_phase14_scoring.py` ⚠️ extend |
| PERS-06 | `assert_value_in_prompt` named + parameterized; every `draw_all` call site asserts; `persona=` guard scans `scripts/*.py` and `src/` with hard-equality allowlist | `tests/test_phase14_scoring.py` ⚠️ widen |
| PREREG-02 | `erasure_gate.py`'s commit is a git **ancestor** of every v3.0 results artifact; fails loudly on shallow clone; fails if it checked nothing | `tests/test_phase16_prereg.py` ❌ W0 |
| — | no fact strings at import; fixture unchanged | `tests/test_phase14_factset.py`, `tests/test_phase16_fixture_regen.py` ✅ exist |

---

## Wave 0 Requirements

- [ ] `.github/workflows/ci.yml` — set `fetch-depth: 0` on the checkout step. **Must land before**
      `tests/test_phase16_prereg.py`, or the PREREG-02 guard is green-but-blind in CI:
      `actions/checkout@v4` defaults to a shallow clone, `23a830c` is absent from it, and
      `git merge-base --is-ancestor` errors rather than failing the assertion.
- [ ] `tests/test_phase16_prereg.py` — PREREG-02
- [ ] `tests/test_phase16_ladder.py` — threshold derivation, `licensed_headline()` totality,
      STAT-01/02 reporting shape, synthetic-value vetting, D-16 import proof
- [ ] `tests/test_phase16_stats.py` — sign-test enumeration, Holm family closure, tie policy
- [ ] `tests/test_phase16_driver.py` — arm parity, `CONDITION_ORDER`, arm-D pool and scorer,
      D-27 sweep structure
- [ ] Extend `tests/test_phase14_scoring.py` — PERS-05 behavioural + AST,
      `assert_value_in_prompt`, every-`draw_all`-asserts, widened D-21 guard. **Prove the widened
      guard RED before landing it** (15-03 precedent: a structural guard nobody has watched fail
      is a guard nobody has verified).
- [ ] Extend `tests/test_package.py` — `pyproject.toml` byte-identity literal (STAT-04)
- Framework install: **none** — pytest 9.0.3 already present.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| The ladder run and the four-arm run themselves | PERS-01, PERS-02 | Require the real 13.9M weights on MPS; ~2 h wall clock; not CPU-only and not CI-runnable | Run the committed drivers on the local M3 after the full CPU suite is green. Record raw per-question output as log evidence. |

Everything else has automated CPU-only verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10 s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
