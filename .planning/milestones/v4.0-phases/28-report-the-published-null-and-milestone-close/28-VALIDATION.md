---
phase: 28
slug: report-the-published-null-and-milestone-close
status: planned
nyquist_compliant: true
wave_0_complete: false
created: 2026-09-20
updated: 2026-09-20
---

# Phase 28 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `28-RESEARCH.md` §Validation Architecture; per-task map filled by the planner from the seven PLAN files.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest `~=9.0` (`pyproject.toml [project.optional-dependencies].dev`) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests"]`, `pythonpath = ["."]`) |
| **Quick run command** | `.venv/bin/pytest tests/test_phase28_report.py tests/test_phase28_prereg.py tests/test_phase28_ledger.py tests/test_package.py tests/test_phase18_docs.py tests/test_phase15_docs.py tests/test_phase25_correction.py -q` |
| **Full suite command** | `make test` (= `.venv/bin/pytest -q`) — committed tree only, `run_in_background`, never behind `timeout 300` |
| **Lint** | `make lint` |
| **Estimated runtime** | quick: seconds · full: ~21–24 min (2871 tests at HEAD + Phase 28 additions) |

---

## Sampling Rate

- **After every task commit:** Run the quick run command + `make lint` (< 1 min)
- **After every plan wave:** Run `make test` uncapped, in the background, on the committed tree (no untracked `results/`/`tests/`/`scripts/` files present) — required at the end of 28-03, 28-05, 28-06, 28-07
- **Before `/gsd:verify-work`:** Full suite green locally AND the D-38 CI run on `origin/main` green (28-07 Task 1)
- **Max feedback latency:** 60 s per task; ~24 min per wave

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 28-01 T1 | 28-01 | 1 | RPT-03 / SC3 | T-28-04, T-28-SC | `[project].dependencies` equal at v1.0/v2.0/v3.0/HEAD via tomllib; shallow/tagless clone refuses; sha pin renamed (D-25, D-26, D-27) | unit (git + tomllib) | `.venv/bin/pytest tests/test_package.py -q -x` | ✅ (edit) | ⬜ pending |
| 28-01 T2 | 28-01 | 1 | RPT-03 / SC3 | T-28-05, T-28-09 | D-32 docstrings true; guard status re-measured before edit; tests back both FIXED rows | unit | `.venv/bin/pytest tests/test_perplexity.py tests/test_phase16_driver.py tests/test_phase16_prereg.py -q -x` | ✅ (edit) | ⬜ pending |
| 28-02 T1 | 28-02 | 1 | RPT-03 / SC3 | T-28-05, T-28-07 | quick-task SUMMARYs renamed + `status: complete`; debug stamp `resolved` with evidence commit (D-39) | CLI (read-only gsd-sdk) | `gsd-sdk query audit-open` → `debug_sessions + quick_tasks == 0` (see plan verify) | n/a | ⬜ pending |
| 28-02 T2 | 28-02 | 1 | RPT-03 / SC3 | T-28-05, T-28-10, T-28-11 | Phase-19 PLAN artifact names real; 19-16 casing; 25-UAT complete; 24-UAT items 2-3 resolved; 23/27 VERIFICATION untouched (D-31, D-35, D-36, D-37) | CLI + grep | plan verify (grep gates + `verify.artifacts` quoted) | n/a | ⬜ pending |
| 28-02 T3 | 28-02 | 1 | RPT-03 | T-28-10 | 24-UAT stamp set by developer ruling | checkpoint:decision | plan verify (`status:` ∈ {complete, partial}, 0 pending) | n/a | ⬜ pending |
| 28-03 T1 | 28-03 | 2 | RPT-03 / SC3 | T-28-01, T-28-05 | one row per open item; closed domain; record-field reasons pasted from `python -c` (D-28, D-29) | inline python (plan verify) | plan verify script over `results/phase28_ledger.json` | ❌ W0 → created here | ⬜ pending |
| 28-03 T2 | 28-03 | 2 | RPT-03 / SC3 | T-28-05, T-28-12 | schema/domain/FIXED-has-collectable-test/len() counts/stamp + artifact regression tests; planted REDs | unit | `.venv/bin/pytest tests/test_phase28_ledger.py -q -x` | ❌ W0 → created here | ⬜ pending |
| 28-03 T3 | 28-03 | 2 | RPT-03 | T-28-05 | developer read the rows before they render | checkpoint:human-verify | `.venv/bin/pytest tests/test_phase28_ledger.py -q -x` on the reviewed tree | ✅ | ⬜ pending |
| 28-04 T1 | 28-04 | 3 | RPT-01 / SC2 | T-28-01, T-28-06, T-28-13, T-28-14 | renderer torch-free; bindings resolve by `[]`; (a)/(b) derived from rows+sigma; `epsilon_for` re-derives record ε; no clock/HEAD/logs (D-06, D-16, D-21, D-24) | inline python (plan verify) | plan verify script (`Bindings` assertions + source-string checks) + ruff | ❌ W0 → created here | ⬜ pending |
| 28-04 T2 | 28-04 | 3 | RPT-01 / SC2 | T-28-03, T-28-06 | templates carry no bare numeral outside D-19 grammar; rendered blocks carry the required record strings in D-01 order | inline python (plan verify) | plan verify script (scan + rendered-content asserts) | ❌ W0 → created here | ⬜ pending |
| 28-05 T1 | 28-05 | 4 | RPT-01 / SC2, SC4 | T-28-03, T-28-01, T-28-06, T-28-14, T-28-15 | template scan (+planted RED), obligation resolution by len(), constants == module pins, digests recompute, confound + lead are the records' words, torch-free + no-clock probes (D-18, D-19, D-23, D-06, D-21, D-08, D-09, D-02, D-03) | unit | `.venv/bin/pytest tests/test_phase28_report.py -q -x` | ❌ W0 → created here | ⬜ pending |
| 28-05 T2 | 28-05 | 4 | RPT-01 / SC1 | T-28-04 | every QUOTES entry verbatim at its source (`git show c673b4c:…`); c673b4c ≺ earliest first-add of every `results/phase2[0-8]_*`; shallow refusal; planted HEAD-as-prereg RED (D-04, D-05) | unit (git) | `.venv/bin/pytest tests/test_phase28_prereg.py -q -x` | ❌ W0 → created here | ⬜ pending |
| 28-06 T1 | 28-06 | 5 | RPT-01 / SC2 | T-28-02, T-28-16 | byte-identity tests RED (sentinels absent) → GREEN after `write`; register widened + renamed; README-glance ledger row flipped to FIXED before install; heading-prefix guards green (D-17, D-22, D-11) | unit | `.venv/bin/pytest tests/test_phase18_docs.py tests/test_phase15_docs.py tests/test_phase28_report.py tests/test_phase25_correction.py -q -x && python scripts/phase28_report.py check` | ✅ (edit) | ⬜ pending |
| 28-06 T2 | 28-06 | 5 | RPT-01 | T-28-17 | developer reads both rendered blocks before the freeze | checkpoint:human-verify | `python scripts/phase28_report.py check && pytest tests/test_phase28_report.py -q -x` | ✅ | ⬜ pending |
| 28-06 T3 | 28-06 | 5 | RPT-01 / SC1, SC2 | T-28-02, T-28-07 | publishing commit; frozen at publish; `check` exit 0; full suite green on committed tree (D-20, D-24) | unit + full suite (background) | plan verify (`git log -1 -- docs/REPORT.md`, `check`, quick suite) ; `make test` in background | ✅ | ⬜ pending |
| 28-07 T1 | 28-07 | 6 | RPT-01, RPT-03 | T-28-08, T-28-18 | developer pushes; CI `success` on `origin/main` with head containing the publishing commit (D-38) | checkpoint:human-action + gh | plan verify (`git rev-list --count origin/main..main == 0`, `gh run list … conclusion == success`) | n/a | ⬜ pending |
| 28-07 T2 | 28-07 | 6 | RPT-01, RPT-03 | T-28-02, T-28-07, T-28-19 | run id in `close.ci_run`, rows unchanged (byte-identity still green); RPT ticks + ROADMAP + STATE by hand with snapshot/diff; PROJECT/MILESTONES/tag untouched (D-34) | unit + grep gates | plan verify (ledger `close` assert, REQUIREMENTS/ROADMAP greps, `check`, `pytest tests/test_phase28_ledger.py tests/test_phase28_report.py`) | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

Requirement → test map from RESEARCH (all rows now owned): RPT-01/SC1 lead+expectation → 28-05 T1/T2; SC1 ancestry → 28-05 T2; SC2 byte-identity → 28-06 T1; SC2 template scan → 28-04 T2 (verify) + 28-05 T1 (test); SC2 constants → 28-05 T1; SC2 obligations → 28-05 T1; SC2 `normalized` register → 28-06 T1; heading guard → 28-06 T1; provenance → 28-05 T1; RPT-03 deps → 28-01 T1; sha pin rename → 28-01 T1; ledger → 28-03 T1/T2; D-32 docstrings → 28-01 T2; SC4 confound → 28-05 T1; D-31/D-39 tool counts → 28-02 T1/T2 (manual-CLI, recorded as ledger evidence); D-38 CI → 28-07 T1.

---

## Wave 0 Requirements

Wave 0 is distributed: each new test file lands in the plan that creates the code it guards, and every task has an automated verify (inline python / grep gate / gsd-sdk read-only query) even before the pytest file exists.

- [ ] `tests/test_phase28_ledger.py` — 28-03 T2 (schema / domain / FIXED-has-test / len() counts / stamp + artifact regressions / planted REDs)
- [ ] `tests/test_phase28_report.py` — 28-05 T1 (scan, obligations, constants, digests, confound, lead, probes) ; 28-06 T1 adds byte-identity + sentinel + heading + zero-deletion + pinned-date tests
- [ ] `tests/test_phase28_prereg.py` — 28-05 T2 (D-04 quotes at c673b4c, D-05 ancestry, planted RED)
- [ ] `tests/test_package.py` — 28-01 T1 (D-25 test added, D-26 rename)
- [ ] `tests/test_perplexity.py`, `tests/test_phase16_driver.py` — 28-01 T2 (D-32 docstring tests)
- [ ] `tests/test_phase25_correction.py` — 28-06 T1 (register widened, renamed)
- [x] Framework install: none — pytest present

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `gsd-sdk query audit-open` count drops from 9 to the intended residue; `verify.artifacts` on the five Phase-19 plans passes | D-31 / D-39 (28-02) | GSD CLI state, not pytest-reachable (the pytest regressions in 28-03 T2 cover the file-level facts) | `gsd-sdk query audit-open`; `for p in .planning/milestones/v3.0-phases/19-selective-memory-erasure/19-{08,09,12,13,16}-PLAN.md; do gsd-sdk query verify.artifacts "$p"; done` — outputs quoted in the 28-02 SUMMARY and cited as ledger evidence |
| 24-HUMAN-UAT stamp ruling | D-37 (28-02 T3) | human ruling | reply `complete` / `stay-partial` |
| Ledger rows read before rendering | discretion (28-03 T3) | human review | read every row; approve or list changes |
| Rendered report and README bullets read before the freeze | D-20 (28-06 T2) | human review; frozen at publish | `git diff docs/REPORT.md README.md`; approve or request template-level wording changes |
| Green CI on `origin/main` after push | D-38 (28-07 T1) | requires network + push; human checkpoint | `git push origin main`; `gh run watch <id> --exit-status`; run id → ledger `close.ci_run` |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (every task carries an `<automated>` command; test files are created in-plan before they are relied on)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (distributed per plan above)
- [x] No watch-mode flags
- [x] Feedback latency < 60s per task (full suite runs only per wave, in the background)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** planner 2026-09-20 — pending execution
