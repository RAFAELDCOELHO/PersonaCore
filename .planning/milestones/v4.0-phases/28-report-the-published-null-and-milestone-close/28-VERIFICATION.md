---
phase: 28-report-the-published-null-and-milestone-close
verified: 2026-09-22T21:30:00Z
status: passed
score: 4/4 roadmap success criteria verified (35/35 plan-level must-have truths)
overrides_applied: 1
overrides:
  - must_have: "pyproject.toml carries forward sha256-identical (SC3, first clause)"
    reason: "Measured FALSE as written before the phase began: 5065bc5 (2026-09-01) added the single line `license = \"MIT\"` and re-pinned PYPROJECT_SHA256 in the same commit; the whole diff against v3.0 is that line and no dependency changed. The substantive guarantee — zero new runtime dependencies for a fourth milestone — is proven mechanically by tests/test_package.py::test_runtime_dependencies_identical_across_four_milestones (tomllib equality of [project].dependencies at v1.0/v2.0/v3.0/HEAD). The clause is published as a dated one-liner in docs/REPORT.md (ledger row SC3-SHA256-CLAUSE, ACCEPTED) per locked decision D-27, not reverted."
    accepted_by: "developer — 28-CONTEXT.md D-27 (locked 2026-09-17); ledger rows approved unchanged 2026-09-21 (28-03 Task 3)"
    accepted_at: "2026-09-21T00:00:00Z"
---

# Phase 28: Report, the Published Null, and Milestone Close — Verification Report

**Phase Goal:** Publish whichever way the numbers came out — including the expected DP null at both
capacities — with every number in prose generated from a committed record rather than authored.
**Verified:** 2026-09-22T21:30:00Z (HEAD `9dcf1fb`)
**Status:** passed
**Re-verification:** No — initial verification

Stance taken: SUMMARY claims were treated as hypotheses. Every truth below was checked against the
working tree, git history, the committed records, the `gh` API, and by running the Phase-28 guard
tests in this verifier's own process (`.venv/bin/pytest`). The full ~23-min suite was not re-run
(orchestrator rule); the last full runs are CI `35770563251` at `d2dcbe2` (2845 passed / 72 skipped)
and the orchestrator's post-wave local suites.

## Goal Achievement

### Observable Truths — ROADMAP Success Criteria (the contract)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC1 | Report publishes the measured outcome incl. the DP null at both capacities, quoting the standing expectation (72σ at L=8, σ ≥ 15.3, Secret Sharer Table 3) as recorded before any run, on its own surface | ✓ VERIFIED | `docs/REPORT.md` ends with one `## v4.0 — the published null: \`null-at-both-capacities\` (recorded 2026-09-21)` section (281 lines, last `##` in the file, zero `##` after it). Lead line quotes `verdicts.capacity_branch` and both `arm_existentials` verbatim ("0 of 32 point(s) examined returned PASS" / "0 of 6"); line 2 the mechanism 30 of 30 cleared (a), 0 cleared (b) derived from `admission.rows`+`sigma>0` (not `cleared_counts.b`=4); line 3 the n=64 caveat `87/1008` before the first `###`. `### The standing expectation, recorded before any run` quotes `72σ`, `σ ≥ 15.3`, `Secret Sharer Table 3` from `.planning/research/SUMMARY.md` at `c673b4c`; `tests/test_phase28_prereg.py::test_expectation_commit_precedes_every_v4_result` derives every `results/phase2[0-8]_*` first-add from `git log --diff-filter=A` (no hardcoded SHA — `grep -c 9bb34ad` = 0) and asserts `merge-base --is-ancestor`, refusing on a shallow clone. All 5 prereg tests green here. |
| SC2 | Every ε/σ/C/q/δ in `docs/REPORT.md` asserted by test to match the module constant; tables generated from committed records and re-render byte-identically; every doc-consistency check routes through `_prose.normalized` | ✓ VERIFIED | `tests/test_phase28_report.py::test_constants_match_modules_and_record` (sigma_for/epsilon_for recompute, CURVE_K, FULL_FIDELITY_K==AST-read phase18 K, DELTA, STEP_BUDGET, SAMPLING_RATE_Q/CLIP_NORM over the 30 noised DP points, SIGMA_LADDER, F_Y, MARGIN_K); `test_report_block_is_byte_identical` / `test_glance_block_is_byte_identical` compare `_span(...) == render_*()` with `==`; `scripts/phase28_report.py check` exits 0 on HEAD; `git diff 3b63b7d HEAD -- docs/REPORT.md README.md` is empty (frozen since publish, D-20). Independent template scan (strip `${…}` + D-19 grammar) → zero bare numerals in both `.tmpl` files. `_EARLIER_GUARD_FILES` in `tests/test_phase25_correction.py` now lists all three `test_phase28_*.py`; "three files wide"/"THREE GUARD FILES" gone (0 hits). 73 tests across the Phase-28 files + test_package + test_phase25_correction + the two D-32 tests: **73 passed**. |
| SC3 | `pyproject.toml` sha256-identical; zero new runtime deps for a fourth milestone; 16 inherited v3.0 debt items + 6 stale-stamp items each closed / re-deferred with reason / named limitation | ✓ VERIFIED (sha256 clause: PASSED by override, see frontmatter) | `tests/test_package.py::test_runtime_dependencies_identical_across_four_milestones` (tomllib, refuses shallow/tagless clone) green; `test_pyproject_unchanged_since_v2_close` no longer exists (0 hits), pin renamed `test_pyproject_sha256_pin_detects_any_change`; `shasum pyproject.toml` = `15ffd6b5…926f` unchanged. Ledger `results/phase28_ledger.json`: 69 rows, exactly the 7 keys each, closed 6-value domain; v3.0 `tech-debt` filter = **16**, v3.0 `stale-stamp` filter = **6** (both asserted against the parsed audit block / STATE table in `test_v3_counts_derive_from_the_sources`). Dispositions at HEAD: NAMED-LIMITATION 23 · ACCEPTED 18 · FORBIDDEN-BY-GUARD 10 · FIXED 9 · RE-DEFERRED 5 · CLOSED-EARLIER 4. Every one of the 9 FIXED rows cites a commit that `git cat-file -e` resolves and a node id that `pytest --collect-only` collects (checked individually). |
| SC4 | Adversarial arm published as recipe-confounded, not a ratio result: (c) fails for the recipe (no replay; `build_bins` refuses replay+adversarial; `7,581 teaching + 0 replay` vs DP replay windows), the n=64 leg REFUSED by the coverage route because its ratio-0 control scored held-out 0/648, no conclusion about adversarial ratio; cause quoted from §12.5c and `phase25_frontier.json`, never re-derived | ✓ VERIFIED (D-09 corrections applied) | Span lines 56–121: `adversarial_no_replay.finding`, `log_line` (`7,581 teaching + 0 replay`), `code_source` (`build_bins refuses replay_ratio > 0 together with adversarial_ratio > 0`), `dp_replay_source` (**`replay_windows=32` at n=8 and `replay_windows=256` at n=64** — D-09(i), SC4's bare "32" is the n=8 figure), the anchored §12.5c blockquote, `amended_criterion` verbatim (`held-out recall 0/648`, `Y_heldout = 0.7 x 0 = 0`, `Decided by the orchestrator 2026-09-09; reversible in seconds`, `3-66 of 416 > X`), `leg_refusals.adv_n64`, `early_return_reason` `REFUSED by the sanctioned route before the pin was reached`, and the explicit sentence that (c) **was never applied** to the 6 `adv_n64` points (D-09(ii)) while failing on the 6 `adv_n8` points. Ship block line 201: "No conclusion is drawn about the adversarial ratio." README bullet: "no conclusion about adversarial ratio". `test_confound_is_quoted_from_the_records` green; `logs/` absent from the renderer source (0 hits); `phase25_sweep.out` appears only inside the two quoted record fields. |

**Score:** 4/4 roadmap SCs verified (1 clause by override).

### Observable Truths — PLAN frontmatter must-haves (35, grouped by plan)

| Plan | Truths | Status | Evidence (spot) |
|------|--------|--------|-----------------|
| 28-01 | 5 | ✓ 5/5 | tomllib test present (`git show <tag>:pyproject.toml`); `corpus_len - n_windows` 0 hits / `corpus_len - 1` 1 hit in `perplexity.py`; `exactly two entries` 0 hits in `phase16_persistence.py`; both D-32 tests collected + green; `test_phase16_prereg.py` untouched-module guard evidenced in 28-01 SUMMARY and CI. |
| 28-02 | 6 | ✓ 6/6 | `audit-open` counts now `debug 0 / quick 0 / todos 0 / uat_gaps 0 / verification_gaps 2 / total 2`; quick-task dirs each contain exactly `SUMMARY.md` with `status: complete`; debug session `status: resolved`; `verify.artifacts` on 19-08/09/12/13/16: every tracked `results/` path passes, only the two gitignored `checkpoints/*.pt` false (recorded, D-31); 25-UAT `status: complete`; 24-UAT items 2–3 `[RESOLVED]`, 0 `[pending]`, note names `phase24_adversarial.py:289` (2 hits) **and** the measured `:296-301`/`:309`; 23- and 27-VERIFICATION both still `human_needed` and byte-untouched since `18680f7`; `19-13-SUMMARY.md` untouched. |
| 28-03 | 8 | ✓ 8/8 | Ledger schema/domain/FIXED-has-test/record-bound reasons all asserted by the 15 ledger tests (green); todo in `.planning/todos/completed/` with `status: resolved`, `pending/` empty; developer review "approved 2026-09-21" (28-03 SUMMARY; rows unchanged after, `git status` clean). |
| 28-04 | 6 | ✓ 6/6 | Renderer imports torch-free in a fresh interpreter (`'torch' in sys.modules` → False); source has none of `today()`, `datetime.now`, `rev-parse`, `os.replace`, `logs/`, `mitigation_point_verdict`, `import phase18_extraction`, `train_arm(`; `_sigma_for_eps4` `_prove`s `epsilon_for(16.0, steps, delta) == p["epsilon"]` before printing `15.289937507119`; `install` uses `Path.write_text` and proves sentinel counts; `PUBLISHED = "2026-09-21"` == `git log -1 --date=short 3b63b7d`; provenance table digests + ledger rows-only digest (`bb9f82fe…`) present; section order matches D-01 (13 headings listed in order in the span). |
| 28-05 | 9 | ✓ 9/9 | All named tests exist and pass (15 report tests + 5 prereg tests at 28-05; 44 after 28-06/28-07 additions); template-scan planted REDs in `tmp_path`; obligation resolution over `PUBLICATION_OBLIGATION` + `_CONTINUATION` by `len()`; D-07 test on the bracket ε lines; provenance digests recomputed from `read_bytes()`; lead/caveat test re-derives (a)/(b) from `rows`. |
| 28-06 | 7 | ✓ 7/7 | One sentinel pair in each surface (2 markers each); README span sits inside `## Results at a glance`, no `##` inside it, README diff at publish = +19/−0, REPORT = +283/−0 (zero deletions); byte-identity tests green; register widened; developer "approved" 2026-09-21 before the publishing commit `3b63b7d`; `check` exit 0; `tests/test_phase18_docs.py` + `test_phase15_docs.py` **15 passed** here. |
| 28-07 | 5 | ✓ 5/5 | `gh run view 35770563251` → `conclusion: success`, `headSha d2dcbe2…`, `git merge-base --is-ancestor 3b63b7d d2dcbe2` exits 0; `close.ci_run` filled with id/url/head_sha/conclusion/recorded and `rows` digest unchanged (`bb9f82fe…` = the published provenance row); RPT-01/RPT-03 `[x]` with `**SATISFIED` traceability rows; ROADMAP 7 × `[x] 28-0N-PLAN.md`, progress row `7/7 | Plans complete — verification pending`, `- [ ] **Phase 28` heading checkbox untouched; STATE frontmatter parses; `PROJECT.md`/`MILESTONES.md` byte-untouched since `18680f7`; `git tag -l v4.0` empty; Claude never pushed (three unpushed commits confirm the push is the developer's). |

### CONTEXT decisions the orchestrator asked to be checked explicitly

| Decision | Honored? | Evidence |
|----------|----------|----------|
| D-01 one appended section, null → confound → canary → MOOT → corrections → ship → register → v5.0 | Yes | Heading order in span: expectation(11) · ε/σ(25) · adversarial(56) · canary(123) · relearning(129) · corrected(144) · figures(157) · ship(167) · register(203) · v5.0(244) · build pointers(256) · provenance(265) |
| D-05 "recorded before any run" as a git-derived CPU test | Yes | `test_phase28_prereg.py`: `is-shallow-repository`, `diff-filter=A`, `merge-base --is-ancestor` present (4 hits), no hardcoded first-add |
| D-11 README bullets rendered, zero deletions | Yes | `git diff 236018e 3b63b7d -- README.md` = +19/−0; `test_glance_deleted_nothing` green |
| D-16..D-19 named bindings, byte-identity, template-source scan, strict grammar | Yes | 49 dotted placeholders in the report template; independent scan zero hits; planted-RED probes; `==` byte tests |
| D-20 frozen at publish | Yes | `git diff 3b63b7d HEAD -- docs/REPORT.md README.md` empty; the post-publish renderer change (`ledger_frozen_bytes`, `89aae4f`) reproduces the published 49057-byte provenance row so no re-render or addendum was needed; `check` exit 0 |
| D-21 records read directly, digests in the block | Yes | `load()` uses `json.loads(path.read_bytes())`; provenance table lists sha256 + bytes per record; `test_provenance_digests_recompute_from_bytes` green |
| D-27 SC3 sha256 clause published as a dated one-liner | Yes | Ledger row `SC3-SHA256-CLAUSE` ACCEPTED, evidence `5065bc5`; rendered in the register via `${ledger.row.SC3-SHA256-CLAUSE.reason}` |
| D-31 repair only active tool errors | Yes | `path:` fields clean (0 stale names on `path:` lines); whole-file grep still finds 5/6/4/3 stale names in prose / `files_modified` / recorded `<automated>` commands — **by design** (28-02 deviation 3, T-28-11); ruled acceptable, see Gaps Summary |
| D-34 hand edits, zero mutation handlers | Yes (as far as observable) | STATE/ROADMAP/REQUIREMENTS frontmatter intact; the plan-level diff summaries in 28-07 SUMMARY match the observed state; `completed_phases` still 7 (phase-complete step left to the orchestrator) |
| D-36 25-UAT `complete` | Yes | `25-HUMAN-UAT.md:2 status: complete` |
| D-37 24-UAT items disposed, prose untouched | Yes | items `[RESOLVED]`, 0 pending; stamp `complete` by developer ruling 2026-09-21 (`4b00c80`) |
| D-38 push + green CI as a human checkpoint | Yes | run `35770563251` success on head containing `3b63b7d`; first run `35719377808` failed on 4 tests, 3 causes fixed at `d2dcbe2` |
| D-39 stale workflow stamps evidenced | Yes | each stamp cites its commit in the SUMMARY; all three evidence commits (`7af6006`, `4012a61`, `c71bade`…) resolve |

### Required Artifacts

`gsd-sdk query verify.artifacts` on all seven PLANs: 28-01 3/3 · 28-02 3/3 · 28-03 2/2 · 28-04 3/3 · 28-05 2/2 · 28-06 3/3 · 28-07 2/2 — every artifact exists, is substantive, and is wired.

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/phase28_report.py` | renderer (resolve, Bindings, DERIVED, TABLES, render_*, install, check, main) | ✓ VERIFIED | 800+ lines; imported by 3 test files; `check` exit 0; torch-free |
| `scripts/phase28_report.md.tmpl` / `phase28_glance.md.tmpl` | placeholders only | ✓ VERIFIED | zero bare numerals under D-19 grammar; every `QUOTES` key used |
| `docs/REPORT.md` span | the published v4.0 section | ✓ VERIFIED | byte-identical to `render_report()`; frozen since `3b63b7d` |
| `README.md` span | rendered glance bullets v3.0 + v4.0 | ✓ VERIFIED | anchor `#v40--the-published-null-null-at-both-capacities-recorded-2026-09-21` matches the rendered `##` title |
| `results/phase28_ledger.json` | 69 rows, closed domain, `close.ci_run` filled | ✓ VERIFIED | byte-stable re-dump; rows digest unchanged since publish |
| `tests/test_phase28_report.py` / `_prereg.py` / `_ledger.py` | guards | ✓ VERIFIED | 24 + 5 + 15 tests green here |
| `tests/test_package.py` | D-25 test + D-26 rename | ✓ VERIFIED | 4 passed |
| `src/personacore/evaluation/perplexity.py`, `scripts/phase16_persistence.py` | D-32 docstring fixes | ✓ VERIFIED | docstring-only hunks; regression tests green |

### Key Link Verification

`gsd-sdk query verify.key-links` reports "Source file not found" for 28-02/03/06/07 because those plans' `from:` fields are descriptive labels (e.g. `FIXED rows' evidence`, `docs/REPORT.md new section`) rather than paths, and one 28-04 pattern is a regex the tool double-escapes. Each was verified by hand:

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/test_package.py` | tags v1.0/v2.0/v3.0 | `git show <tag>:pyproject.toml` → tomllib | WIRED | tool 2/2 |
| 19-*-PLAN.md artifacts | `phase19_erasure.py` constants | `results/phase19_` names | WIRED | 15/9/13/12/8 hits across the five PLANs; `verify.artifacts` green |
| 24-HUMAN-UAT item 2 | `phase24_adversarial.py:289-292,:300` | dated note | WIRED | 2 hits + measured `:296-301`/`:309` named beside them |
| ledger FIXED rows | pytest node ids | `--collect-only` | WIRED | 9/9 collected in this verifier's process |
| `phase28_report.py` | frontier / accountant / ledger | `json.load`, `sigma_for`, NAMED-LIMITATION filter | WIRED | tool 3/4; the 4th (`\$\{[a-z_]+\.` placeholders) verified: 49 matches in the template |
| `test_report_block_is_byte_identical` | `docs/REPORT.md` span | `_span(...) == render_report()` | WIRED | `render_report()` appears in the test body; green |
| `docs/REPORT.md` new section | `test_docs_continuation_is_additive` | appended after last `##` | WIRED | 15 docs-guard tests passed here |
| `close.ci_run.head_sha` | publishing commit | `merge-base --is-ancestor` | WIRED | exit 0 |
| REQUIREMENTS RPT-01 row | `PHASE28-REPORT` stem + guard node ids | traceability row | WIRED | 1 hit of `PHASE28-REPORT` in REQUIREMENTS.md |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
|----------|---------------|--------|--------------------|--------|
| `docs/REPORT.md` span | every `${…}` binding | `results/phase25_frontier.json`, `phase26_canary.json`, `phase27_admission.json`, `phase23_*.json`, `phase28_ledger.json`, `git show c673b4c:…` | Yes — `derived.noised_dp_cleared_b` = `0` from rows (record's `cleared_counts.b` = 4 is rendered beside it and decomposed by leg); `sigma_for_eps4` recomputed at render | ✓ FLOWING |
| `README.md` span | same bindings | same records | Yes | ✓ FLOWING |
| Ship block "withholds" table | ledger `NAMED-LIMITATION` filter + existentials | ledger rows | Yes — 23 rows + 2 existentials rendered | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Phase-28 guards + D-32 + package + register | `pytest tests/test_phase28_report.py tests/test_phase28_prereg.py tests/test_phase28_ledger.py tests/test_package.py tests/test_phase25_correction.py <2 D-32 node ids> -q` | `73 passed in 16.24s` | ✓ PASS |
| Docs heading-prefix guards | `pytest tests/test_phase18_docs.py tests/test_phase15_docs.py -q` | `15 passed` | ✓ PASS |
| Re-render drift | `.venv/bin/python scripts/phase28_report.py check` | exit 0 | ✓ PASS |
| Renderer torch-free | `python -c "import phase28_report; 'torch' in sys.modules"` | `False` | ✓ PASS |
| Template scan (independent) | strip `${…}` + D-19 grammar, search `\d` | `[]` for both templates | ✓ PASS |
| FIXED node ids collectable | `pytest --collect-only -q <id>` × 9 | 9/9 collected | ✓ PASS |
| CI close precondition | `gh run view 35770563251 --json conclusion,headSha` | `success`, `d2dcbe2…` | ✓ PASS |
| Full suite on HEAD `9dcf1fb` | orchestrator's detached run | **not available** — scratchpad `wave6_suite.log` stalled at 51% (1691 B); last completed full run is CI at `d2dcbe2` | ? SKIP (reported, not assumed) |

### Probe Execution

No `scripts/*/tests/probe-*.sh` probes exist in this repository and none are declared by the Phase-28 PLANs/SUMMARYs — SKIPPED.

### Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| RPT-01 | 28-04, 28-05, 28-06, 28-07 | Milestone report publishes whichever way the numbers came out, incl. the DP null; every number generated from a committed record | ✓ SATISFIED | SC1/SC2/SC4 above; `- [x] **RPT-01**` at REQUIREMENTS.md:449; traceability row :579 `**SATISFIED (plans 28-04, 28-05, 28-06)**` |
| RPT-03 | 28-01, 28-02, 28-03, 28-07 | Zero new runtime dependencies; pin carries forward; 16 + 6 inherited items dispositioned | ✓ SATISFIED | SC3 above; `- [x] **RPT-03**` at :455; row :580 `**SATISFIED (plans 28-01, 28-03)**`, measured 16 / 6 |
| Orphan check | — | REQUIREMENTS.md rows mapped to `Phase 28` | none orphaned | Only RPT-01 and RPT-03 map to Phase 28 (`grep "| Phase 28 |"`); RPT-02 is mapped to Phase 20/25 by the 2026-08-31 amendment and its third-clause routing (`normalized` register) is nonetheless satisfied here via `tests/test_phase25_correction.py` |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/test_phase28_report.py` | 44, 60 | `_PLACEHOLDER` (regex constant name) | ℹ️ Info | false positive of the marker scan — it is the `${…}` regex, not a stub |
| `tests/test_phase25_correction.py` | 34 | "PLACEHOLDER-COUNT rule" in a pre-existing docstring | ℹ️ Info | pre-existing prose, not introduced by this phase |

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK` markers in any file this phase created; none in the added hunks of `scripts/phase16_persistence.py` / `tests/test_phase16_driver.py`. No empty returns, hardcoded empty data, or console-only handlers — the renderer raises `KeyError` on a missing binding rather than rendering blank.

### Human Verification Required

None outstanding. The four human checkpoints the phase designed were all answered by the developer and their outcomes are observable in the tree: 24-UAT stamp ruling (`4b00c80`), ledger rows approved unchanged (rows digest stable since `841e7df`+flip), rendered report approved before the publishing commit (`3b63b7d` follows the read), push + green CI (`35770563251`). No PLAN carries a deferred `<human-check>` block (0 across all seven).

### Deviations ruled on (recorded in SUMMARYs; the orchestrator asked for rulings rather than rediscovery)

1. **28-02 deviation 3 (D-31 whole-file grep unsatisfied).** Stale names remain in PLAN prose, `files_modified`, task `<files>` and recorded `<automated>` commands (5/6/4/3 hits). Only `path:` / `key_links` were rewritten. **Ruling: acceptable.** The must-have truth is "verify.artifacts reports every tracked results/ path as existing" — true; the plan's acceptance grep over-reached D-31's own boundary ("repair ONLY what makes a tool report an active error") and rewriting recorded commands would falsify what ran (T-28-11).
2. **28-02 deviation 1 (measured lines `:296-301`/`:309` vs D-37's `:289-292`/`:300`).** The UAT note names both; the ledger cites the measured lines. **Ruling: acceptable** — the plan's must-have literal is present (2 hits) and the truth is more precise, not less.
3. **28-06 `_adv_points` fix pre-publish.** Reasons column switched from `reasons[0]` (condition (a)'s bare `0.0000%`) to the condition-(c) reasons or the refusal. Happened before `3b63b7d`; STAT-02 guard green. **Ruling: correct** — a re-render before the publishing commit is exactly what D-20 permits.
4. **28-07 `ledger_frozen_bytes` post-publish renderer change (`89aae4f`).** The provenance row sized the whole ledger file, so filling `close` moved 49057 → 49297 while the rows digest stood. The fix sizes the frozen view (`close.ci_run = None`) — measured equal to `git show 3b63b7d:results/phase28_ledger.json | wc -c`. Published bytes unchanged (empty `git diff 3b63b7d HEAD -- docs/REPORT.md README.md`), `check` exit 0, new regression test `test_ledger_size_column_is_invariant_under_close`. **Ruling: D-20 honored** — the block was not edited or re-rendered; the renderer was made to agree with what it had already published.
5. **SC3 sha256 clause and SC4 wording (D-27, D-09).** Both were measured false as written before the phase; the phase publishes what the records state and records the correction. SC3's literal clause is carried as the single override above; SC4's two wording corrections (32 vs 256 replay windows by leg; (c) never applied to the refused `adv_n64` leg) are quoted from the record's own fields, so SC4 is VERIFIED as the records state it.

### Gaps Summary

No gaps. The phase goal is achieved in the codebase: the null is published on its own surface with the pre-run expectation quoted from a commit proven older than every v4.0 record; every number in both surfaces is a binding to a committed record or module constant, re-renders byte-identically, and is guarded by tests that ran green in this verifier's process; the adversarial arm is published as recipe-confounded in the records' own words; the dependency claim is a tomllib test; the 16 + 6 items each hold a tested disposition; CI is green on a head containing the publishing commit.

Two informational notes for the orchestrator (not gaps under any must-have as written):

- **Three commits are unpushed** (`89aae4f` renderer + test change, `fd03998` close, `9dcf1fb` SUMMARY) and therefore have not run in CI. All targeted tests pass on HEAD locally; the published bytes are unchanged. Recommend the developer pushes before `/gsd-complete-milestone` so the final full run covers the `ledger_frozen_bytes` change.
- **The final full-suite result on `9dcf1fb` was not available** to this verifier (scratchpad log stalled at 51%). Stated rather than assumed; CI at `d2dcbe2` (2845 / 72 / 0) is the last completed full run.

The ROADMAP `- [ ] **Phase 28` heading checkbox is deliberately untouched — owned by the orchestrator's close (D-34).

---

_Verified: 2026-09-22T21:30:00Z_
_Verifier: Claude (gsd-verifier)_
