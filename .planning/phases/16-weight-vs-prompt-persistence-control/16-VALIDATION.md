---
phase: 16
slug: weight-vs-prompt-persistence-control
status: planned
nyquist_compliant: true
wave_0_complete: true
created: 2026-08-12
updated: 2026-08-12
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Infrastructure, sampling rate and Wave 0 are derived from `16-RESEARCH.md` §Validation
> Architecture. The Per-Task Verification Map below is populated against the 11 committed plans.

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

**Interpreter:** every automated command uses `.venv/bin/python` / `.venv/bin/pytest`, never bare
`python` or `python3`. This box runs Python 3.14, which CLAUDE.md declares an unsupported target —
torch is absent under it, so any `importlib … exec_module` check that loads a driver module fails
with `ModuleNotFoundError` rather than the assertion it was written to make.

---

## Sampling Rate

- **After every task commit:** run the quick command above (CPU-only, seconds)
- **After every plan wave:** `make test`
- **Phase gate — stricter than the default:** the full suite must be green **before the ladder
  runs** (16-07) and again **before the four-arm run** (16-11), not merely before
  `/gsd:verify-work`. PERS-01 makes the ladder blocking, so a ladder run on an unvalidated
  instrument is unrecoverable: the numbers cannot be re-derived afterwards without breaking
  pre-registration.
- **Max feedback latency:** ~10 s (quick command)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 16-01 T1 | 16-01 | 1 | PREREG-02 | T-16-02 | CI clones full history so the ancestry query resolves | static | `.venv/bin/python -c "…'fetch-depth: 0' in ci.yml"` | ✅ ci.yml | ⬜ pending |
| 16-01 T2 | 16-01 | 1 | PREREG-02 | T-16-01/03/04 | prereg commit is a git ancestor of every v3.0 artifact; loud on shallow clone; loud on empty match | unit | `.venv/bin/pytest tests/test_phase16_prereg.py -q` | ❌ W0 | ⬜ pending |
| 16-01 T3 | 16-01 | 1 | STAT-04 | T-16-SC | `pyproject.toml` byte-identical to v2.0 close | unit | `.venv/bin/pytest tests/test_package.py -q` | ⚠️ extend | ⬜ pending |
| 16-02 T1 | 16-02 | 1 | PERS-05 | T-16-05 | `run_fairness_control` pairs on `item.seed_index`, not `enumerate` | unit + AST | `.venv/bin/pytest tests/test_phase14_scoring.py -q` | ⚠️ extend | ⬜ pending |
| 16-02 T2 | 16-02 | 1 | PERS-06 | T-16-06 | `assert_value_in_prompt` named, `values` a parameter, two-level check | unit + AST | `.venv/bin/pytest tests/test_phase14_scoring.py -q` | ⚠️ extend | ⬜ pending |
| 16-03 T1 | 16-03 | 2 | PERS-06 | T-16-07 | every `draw_all` call site asserts; `persona=` guard scans `scripts/*.py` + `src/` with hard-equality allowlist | AST | `.venv/bin/pytest tests/test_phase14_scoring.py -q` | ⚠️ widen | ⬜ pending |
| 16-04 T1 | 16-04 | 3 | PERS-01 | T-16-08 | `probe_guessability` public; gate imported, never copied (D-16) | unit + AST | `.venv/bin/pytest tests/test_phase14_factset.py -q` | ✅ exists | ⬜ pending |
| 16-04 T2 | 16-04 | 3 | STAT-01/02/05, PERS-01 | T-16-09..17 | threshold literals equal their derivation; `licensed_headline()` total over the rung lattice; no bare `0%` | unit | `.venv/bin/pytest tests/test_phase16_ladder.py -q` | ❌ W0 | ⬜ pending |
| 16-05 T1 | 16-05 | 4 | PERS-01 | T-16-19/21 | measured distances (≤3 / [25,35]); no instructed-copy framing; near builder passes no `persona=` | unit + AST | `.venv/bin/pytest tests/test_phase16_ladder.py tests/test_phase14_scoring.py -q` | ❌ W0 | ⬜ pending |
| 16-05 T2 | 16-05 | 4 | PERS-01, STAT-05 | T-16-18/20 | every synthetic value token-length-matched and gate-CLEARED (`clean == True`) before becoming a literal; the rejected candidates on the record | unit | `.venv/bin/pytest tests/test_phase16_ladder.py -q` | ❌ W0 | ⬜ pending |
| 16-06 T1-T3 | 16-06 | 5 | PERS-01, STAT-02/05 | T-16-22..25 | clobber guard anchored on `VERDICT_SECTION`; D-14 clause verbatim; both floor units | unit + AST | `.venv/bin/pytest tests/test_phase16_ladder.py -q` | ❌ W0 | ⬜ pending |
| 16-07 T1-T2 | 16-07 | 6 | PERS-01 | T-16-26..31 | the ladder ran and was committed **before** anything was compared | artifact | `.venv/bin/pytest tests/test_phase16_ladder.py tests/test_phase16_prereg.py -q` | ❌ W0 | ⬜ pending |
| 16-08 T1 | 16-08 | 7 | PERS-02, STAT-05 | T-16-33/33b | `CONDITION_ORDER` locked; four scalar parity fields on one object read by identity; `forbid` runtime-injected + content-hashed; `PER_QUESTION_KEYS` names the record shape once | unit + AST | `.venv/bin/pytest tests/test_phase16_driver.py -q` | ❌ W0 | ⬜ pending |
| 16-08 T2 | 16-08 | 7 | PERS-02 | T-16-33b | arms A/B/C dispatched, not reimplemented; all four normalized onto `PER_QUESTION_KEYS` | unit + AST | `.venv/bin/pytest tests/test_phase16_driver.py tests/test_phase14_scoring.py -q` | ❌ W0 | ⬜ pending |
| 16-08 T3 | 16-08 | 7 | PERS-04 | T-16-32/34..37 | arm D: 20-value pool, floor 0.05, adapter off, one text draw, scored by `contains_value` | unit + AST | `.venv/bin/pytest tests/test_phase16_driver.py -q` | ❌ W0 | ⬜ pending |
| 16-09 T1 | 16-09 | 8 | STAT-01, STAT-02 | T-16-40..42 | per-fact grouping on `fact_id`; both denominators; clustered bootstrap descriptive, Wilson labelled; no bare `0%` | unit | `.venv/bin/pytest tests/test_phase16_stats.py -q` | ❌ W0 | ⬜ pending |
| 16-09 T2 | 16-09 | 8 | STAT-02, STAT-06 | T-16-38/39/39b/39c | enumerated sign test; ties against with `n` fixed at 8; **D-29 direction filter** (`1.0` unless `positives > n/2`); `SIGN_TEST_ALTERNATIVE` a committed literal; Holm closed at 6 | unit + AST | `.venv/bin/pytest tests/test_phase16_stats.py -q` | ❌ W0 | ⬜ pending |
| 16-09 T3 | 16-09 | 8 | STAT-06 | T-16-38/43 | nothing outside the 6 pairs enters the verdict path, statically and at runtime | AST + unit | `.venv/bin/pytest tests/test_phase16_stats.py tests/test_phase16_driver.py tests/test_phase16_ladder.py -q` | ❌ W0 | ⬜ pending |
| 16-10 T1 | 16-10 | 9 | PERS-03 | T-16-44 | truncation derived from crossing `block_size`; all dilution inside the persona span; statement at the head and provably outside the trailing 256-token window; overwrite is a statement string (no new `persona=` / `draw_all` site) | unit + AST | `.venv/bin/pytest tests/test_phase16_driver.py tests/test_phase16_stats.py -q` | ❌ W0 | ⬜ pending |
| 16-10 T2 | 16-10 | 9 | STAT-02, STAT-05 | T-16-47..50 | every verbatim clause, four parity columns, D-25 at 0.05, arm-D soft row stated as structural, truncation caveat, no bare `0%`, never `39.2` | unit + AST | `.venv/bin/pytest tests/test_phase16_driver.py -q` | ❌ W0 | ⬜ pending |
| 16-10 T3 | 16-10 | 9 | PERS-02 | T-16-45/46 | one condition per process, no `--all`; `--report` refuses on SHA / parity / `seed_index` mismatch | unit | `.venv/bin/pytest tests/test_phase16_driver.py tests/test_phase16_stats.py tests/test_phase16_ladder.py -q` | ❌ W0 | ⬜ pending |
| 16-11 T1 | 16-11 | 10 | PERS-02 | T-16-52 | four fresh processes, one shared git SHA, four distinct pids, identical `seed_index` sets | artifact | `.venv/bin/python -c "…4 arm JSONs, 1 sha, 4 pids"` | n/a run | ⬜ pending |
| 16-11 T2 | 16-11 | 10 | STAT-01/02/06, PERS-03/04, PREREG-02 | T-16-51/53/55 | the committed report: 6 Holm rows, no bare `0%`, never `39.2`, verdict cites the ladder | artifact + unit | `.venv/bin/pytest tests/test_phase16_prereg.py tests/test_phase16_fixture_regen.py -q` | ✅ / ❌ W0 | ⬜ pending |
| 16-11 T3 | 16-11 | 10 | SC1-SC5 | T-16-51/54 | human confirms the verdict matches the Holm table and claims no more than the ladder licensed | checkpoint | `make test` + `.venv/bin/pytest tests/test_phase16_prereg.py -q` | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Requirement → test surface** (from `16-RESEARCH.md` §Validation Architecture):

| Req | Surface | File | Owning task |
|---|---|---|---|
| STAT-01 | cell statistic counts **questions**, not draws | `tests/test_phase16_ladder.py`, `tests/test_phase16_stats.py` | 16-04 T2, 16-09 T1 |
| STAT-02 | every proportion ships a denominator + bound; zero cells emit `rule_of_three`, never `0%` | `tests/test_phase16_ladder.py`, `tests/test_phase16_stats.py` | 16-04 T2, 16-09 T1 |
| STAT-04 | `pyproject.toml` byte-identical to its v2.0-close state | `tests/test_package.py` | 16-01 T3 |
| STAT-05 | threshold literals equal their derivation; `licensed_headline()` imports constants, never retypes them; `SIGN_TEST_ALTERNATIVE` committed before any run | `tests/test_phase16_ladder.py`, `tests/test_phase16_stats.py` | 16-04 T2, 16-09 T2 |
| STAT-06 | exactly 6 comparisons enter Holm; enumeration reproduces 0.0078125 / 0.0703125 / 0.015625; ties count against; **D-29 direction filter returns 1.0 for `[0]*8` and `[-1]*8`** | `tests/test_phase16_stats.py` | 16-09 T2, T3 |
| PERS-01 | `licensed_headline()` is **total** over the rung lattice; all-fail branch returns the SC1 capability-deficit statement | `tests/test_phase16_ladder.py` | 16-04 T2, 16-06, 16-07 |
| PERS-02 | arms share the four scalar parity fields via one config object (`forbid` runtime-injected, content-hashed); `CONDITION_ORDER` locked; `PER_QUESTION_KEYS` uniform across arms | `tests/test_phase16_driver.py` | 16-08 T1, T2 |
| PERS-03 | truncation cells derived from the dilution axis crossing `block_size` (D-27); dilution persona-span-internal; statement at the head, outside the trailing 256-token window on truncated cells | `tests/test_phase16_driver.py` | 16-10 T1 |
| PERS-04 | arm D pool is exactly the 20-value lexicon, chance floor literal **0.05**; scored by the same `contains_value` as A/B/C | `tests/test_phase16_driver.py` | 16-08 T3 |
| PERS-05 | `run_fairness_control` passes `item.seed_index` — behavioural **and** AST | `tests/test_phase14_scoring.py` | 16-02 T1 |
| PERS-06 | `assert_value_in_prompt` named + parameterized; every `draw_all` call site asserts; `persona=` guard scans `scripts/*.py` and `src/` with hard-equality allowlist | `tests/test_phase14_scoring.py` | 16-02 T2, 16-03 T1 |
| PREREG-02 | `erasure_gate.py`'s commit is a git **ancestor** of every v3.0 results artifact; fails loudly on shallow clone; fails if it checked nothing | `tests/test_phase16_prereg.py` | 16-01 T1, T2 |
| — | no fact strings at import; fixture unchanged | `tests/test_phase14_factset.py`, `tests/test_phase16_fixture_regen.py` | pre-existing ✅ |

---

## Wave 0 Requirements

Every Wave 0 item below has an **owning task**, so nothing is scheduled to exist without a plan
that creates it.

- [x] `.github/workflows/ci.yml` — `fetch-depth: 0` on the checkout step → **16-01 Task 1**.
      **Must land before** `tests/test_phase16_prereg.py`, or the PREREG-02 guard is green-but-blind
      in CI: `actions/checkout@v4` defaults to a shallow clone, `23a830c` is absent from it, and
      `git merge-base --is-ancestor` errors rather than failing the assertion. Ordering is proved
      with `git log -S'fetch-depth: 0'`, **not** `--diff-filter=A` (which returns the file's
      original creation commit and passes regardless of order).
- [x] `tests/test_phase16_prereg.py` — PREREG-02 → **16-01 Task 2**
- [x] `tests/test_phase16_ladder.py` — threshold derivation, `licensed_headline()` totality,
      STAT-01/02 reporting shape, synthetic-value vetting, D-16 import proof → **16-04 Task 2**
      (created), extended by 16-05 / 16-06
- [x] `tests/test_phase16_stats.py` — sign-test enumeration, the D-29 direction filter, Holm family
      closure, tie policy → **16-09 Task 1** (created), extended by T2 / T3
- [x] `tests/test_phase16_driver.py` — arm parity, `CONDITION_ORDER`, arm-D pool and scorer,
      `PER_QUESTION_KEYS`, D-27 sweep structure → **16-08 Task 1** (created), extended by 16-10
- [x] Extend `tests/test_phase14_scoring.py` — PERS-05 behavioural + AST → **16-02**;
      `assert_value_in_prompt`, every-`draw_all`-asserts, widened D-21 guard → **16-03**;
      the `build_far_prompt` allowlist entry → **16-05 Task 1**. **Prove the widened guard RED
      before landing it** (15-03 precedent: a structural guard nobody has watched fail is a guard
      nobody has verified). 16-10 does **not** touch this file.
- [x] Extend `tests/test_package.py` — `pyproject.toml` byte-identity literal (STAT-04) →
      **16-01 Task 3**
- Framework install: **none** — pytest 9.0.3 already present.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| The synthetic-value vetting run (`--vet`) | PERS-01, STAT-05 | Loads the real base model to probe >= 36 candidates (~576 completions); not CPU-only, not CI-runnable | 16-05 Task 2: launch in the BACKGROUND (`2>&1 \| tee /tmp/phase16_vet.log`) and poll — the Bash ceiling is 10 min and the run is **15-25 min**; a foreground call leaves a truncated `results/phase16_ladder_material.md`. The committed audit record is that material report; the raw log is scratch and is not committed. |
| The ladder run | PERS-01 | Requires the real 13.9M weights on MPS; ~90 min ±15%; not CPU-only, not CI-runnable | 16-07: run the committed driver on the local M3 after the full CPU suite is green. Background + poll — the Bash ceiling is 10 min. Record raw per-question output as log evidence. |
| The four-arm run | PERS-02, PERS-04 | Real weights; ~39 min (35-44) across four fresh processes | 16-11 Task 1: one process per condition, in `CONDITION_ORDER`, never concurrent. |
| The context-pressure sweep | PERS-03 | Real weights; **100 min floor, up to ~3 h** — the 3.18 s/question median was measured at the 46-token nominal prompt and cells run to 448 tokens with no KV cache | 16-11 Task 1, inside the `prompt-stuffed` invocation. A 2 h cell is expected, not a hang. Record per-cell wall clock. |
| Verdict confirmation | SC1-SC5 | Human judgement against the phase's own success criteria | 16-11 Task 3 — `checkpoint:human-verify`, blocking. |

Everything else has automated CPU-only verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references, each with a named owning task
- [x] No watch-mode flags
- [x] Feedback latency < 10 s
- [x] Every automated command uses `.venv/bin/python` / `.venv/bin/pytest` (Python 3.11 venv), never
      the unsupported system 3.14
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated against the 11 committed plans (2026-08-12, post-plan-check revision round 3).
Wave column realigned to the plans' own `wave:` frontmatter (1,1,2,3,4,5,6,7,8,9,10) — the table had
16-02 at 2 and 16-03 at 3, and placed 16-03 and 16-04 in the same wave despite
`16-04 depends_on: ["16-03"]`. The frontmatter graph was correct and is unchanged.
