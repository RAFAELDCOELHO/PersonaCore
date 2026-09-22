---
phase: 28
slug: report-the-published-null-and-milestone-close
status: verified
threats_open: 0
threats_total_rows: 40
threats_distinct_ids: 20
asvs_level: 1
created: 2026-09-22
audited_at_head: 51bed45
---

# Phase 28 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Register authored at plan time (`register_authored_at_plan_time: true`). This document
> **verifies** the declared mitigations exist in implemented code. It does **not** scan for
> new threats.

**Gate status: CLOSED.** `threats_open: 0`. 40 register rows across 7 plans, **20 distinct threat
IDs** (T-28-01 … T-28-19 plus `T-28-SC`, which every plan carries), every row resolved to `closed`
by a mitigation measured in code or git at HEAD `51bed45`, or by the one logged plan-time accepted
risk (AR-28-01, `T-28-SC`). **No plan-stated mitigation was found absent or contradicted.** Three
code-review Warnings (28-REVIEW WR-01, WR-03, WR-04) and one Info (IN-04) weaken a guard a register
row names; each is recorded as a Finding under its threat, with the measurement that shows the
plan sentence still holds today, and is deliberately **not** logged as an accepted risk — no
developer ruling names them yet. WR-02 is CLOSED at `a4971cb` (quick task 260922-qlm) and now
strengthens T-28-01's 28-04 row.

---

## Boundary of this audit — read this first

What was done (auditor: gsd-security-auditor, from the seven plan-time `<threat_model>` blocks,
HEAD `51bed45`, CPU only, `.venv/bin/python` 3.11, no full suite):

- **Register extracted** from all seven `<threat_model>` blocks: 28-01 (4 rows), 28-02 (5), 28-03
  (5), 28-04 (7), 28-05 (7), 28-06 (6), 28-07 (6) = 40 rows, 20 IDs. IDs recur across plans by
  design; rows are keyed on (threat_id, plan, component). The orchestrator's brief listed 19 IDs;
  the 20th is `T-28-SC` (package installs), present in every plan — `mitigate` in 28-01, `accept`
  in 28-02 … 28-07.
- **Guard suites re-run here:** `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase28_report.py
  tests/test_phase28_prereg.py tests/test_phase28_ledger.py tests/test_package.py
  tests/test_phase25_correction.py tests/test_phase18_docs.py tests/test_phase15_docs.py
  tests/test_perplexity.py::test_docstring_states_the_true_denominator
  tests/test_phase16_driver.py::test_overwrite_statement_docstring_does_not_type_the_allowlist_size`
  → **91 passed in 17.46s, 0 failed, 0 skipped**. `git status --short` before and after: only the
  pre-existing ` D .claude/scheduled_tasks.lock`.
- **Renderer drift check:** `.venv/bin/python scripts/phase28_report.py check` → exit 0.
- **Git facts measured:** non-shallow (`false`); tags `m1-demo-v1 v1.0 v2.0 v3.0`; `git tag -l v4.0`
  empty; `main == origin/main == 51bed45`, `origin/main..main` = 0 commits; `git diff 3b63b7d HEAD --
  docs/REPORT.md README.md` empty and `git log 3b63b7d..HEAD -- docs/REPORT.md README.md` empty;
  `git merge-base --is-ancestor 3b63b7d d2dcbe2` → 0; `results/phase25_frontier.json` at exactly one
  commit; `results/phase25_operational_note.md` untouched since the `OP_NOTE_FROZEN_AT` pin
  `ce2a151`; `results/phase28_ledger.json` at three commits (`841e7df` first-add 2026-09-21,
  `3b63b7d`, `fd03998`); `.planning/PROJECT.md`, `.planning/MILESTONES.md`, `pyproject.toml`,
  `requirements.txt`, `Makefile`, `.github/workflows/ci.yml`, `23-VERIFICATION.md`,
  `27-VERIFICATION.md` and `19-13-SUMMARY.md` all at **0 commits** in `62fd5db..HEAD` (the phase's
  first commit `62fd5db` is dated 2026-09-20); `shasum -a 256 pyproject.toml` = `15ffd6b5…926f` =
  `tests/test_package.py::PYPROJECT_SHA256`; all 18 evidence commits the SUMMARYs cite resolve with
  `git cat-file -e`.
- **Ledger recomputed:** rows digest `bb9f82fe290d7578…` at `3b63b7d` and at HEAD (equal); 69 rows
  both; `close.ci_run` `null` at `3b63b7d`, `{id 35770563251, head_sha d2dcbe2…, conclusion success,
  recorded 2026-09-22}` at HEAD; `git show 3b63b7d:results/phase28_ledger.json | wc -c` = 49057 =
  `ledger_frozen_bytes` (the published provenance row). WR-03 measured on every FIXED row (see S-2).
- **Files read:** `scripts/phase28_report.py` (docstring, `load`, digests, `_sources`, `install`,
  `_span`, `check`, `main`), the three Phase 28 test files (scan, provenance, lead, glance, clock,
  ancestry and freeze tests), `tests/test_package.py`, the two D-32 tests, `.github/workflows/ci.yml`,
  the seven PLANs/SUMMARYs, 28-REVIEW.md, 28-VERIFICATION.md.

What was **not** done:

- The full suite was not re-run (orchestrator: 2870 / 2885 / 2885 / 2905 / 2913 / 2914 passed across
  the six waves, 2916 after WR-02's guard; CI run 35770563251 at `d2dcbe2`: 2845 passed / 72 skipped).
- `scripts/phase28_report.py write` was **not** run (D-20 freeze; T-28-02).
- No new-threat scan. The review's IN-01 … IN-03 do not bear on a register row and are not classified.
- The Obsidian record of this audit was not written (the auditor has no `obsidian` MCP tool);
  it is pending for the orchestrator.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| git history → `tests/test_package.py` | `git show <tag>:pyproject.toml` is evidence only with full history and tags; shallow / tagless clones refused (28-01) | three tagged `pyproject.toml` blobs |
| docstring → ledger `FIXED` row | a `FIXED` row is only as true as the collectable test that would catch the regression (28-01, 28-03) | node ids, commit SHAs |
| archived planning artifacts → GSD tools | edits limited to what a tool actively misreports; audit-trail prose and verifier verdicts never rewritten (28-02) | `path:` / `key_links` fields, stamps |
| developer → UAT / workflow stamp | a stamp changes only on a cited commit or an explicit human ruling (28-02) | `status:` fields |
| hand-authored ledger rows → report | the ledger is the only hand-authored input the renderer reads; schema, closed domain and record-bound reasons tested (28-03) | 69 rows |
| committed records → prose | the renderer is the only path; `[]`-indexing, `repr` formatting, sha256 + bytes in the provenance table (28-04) | six JSON records, three frozen `.md` |
| template author → numerals | the `.tmpl` source is scanned; quantities enter only through `${…}` bindings (28-04, 28-05) | placeholders |
| renderer → publication surfaces | `install` writes between sentinels only and proves the prefix on the produced bytes (28-04, 28-06) | `docs/REPORT.md`, `README.md` spans |
| git history → ancestry / freeze tests | full clone required; first-adds derived from `git log --diff-filter=A`; op-note freeze pinned at `ce2a151` (28-05, quick 260922-qlm) | commit graph |
| publishing commit → future edits | frozen at `3b63b7d`: byte-identity tests + `check`; corrections only via `append_addendum` (28-06) | published spans |
| local `main` → `origin/main` | outward push is a human action; CI is the first off-host run (28-07) | commits, tags |
| ledger rows (frozen) → close block | only `close.ci_run` changes after publish; the rows digest in the published block detects any row edit (28-07) | `close.ci_run` |
| planning ledgers ← hand edits | snapshot → Edit → `diff -u`; zero `gsd-sdk` mutation handlers by executors (28-02, 28-03, 28-06, 28-07) | STATE / ROADMAP / REQUIREMENTS text |

---

## Threat Register

Line numbers are at HEAD `51bed45`. "PASSED" = observed in this audit's 91-test run quoted above.
Findings are cross-referenced where a review finding weakens a row's guard.

| Threat ID | Category | Component (plan) | Disposition | Mitigation (verified at HEAD `51bed45`) | Status |
|-----------|----------|------------------|-------------|------------------------------------------|--------|
| T-28-04 | Repudiation | (28-01) `tests/test_package.py` D-25 test | mitigate | `test_runtime_dependencies_identical_across_four_milestones` (`:42-68`): `_git("rev-parse", "--is-shallow-repository") == "false"` asserted at `:48` and `tags >= {"v1.0", "v2.0", "v3.0"}` at `:53-54`, both before the tomllib comparison at `:59-64`; no dependency name typed. Measured: non-shallow, tags present. PASSED | closed |
| T-28-05 | Repudiation | (28-01) D-32 `FIXED` rows | mitigate | Both docstring tests exist and are green before the ledger cites them: `tests/test_perplexity.py::test_docstring_states_the_true_denominator` (`:150-156`, asserts `corpus_len - 1` in / `corpus_len - n_windows` not in the module docstring) and `tests/test_phase16_driver.py::test_overwrite_statement_docstring_does_not_type_the_allowlist_size` (`:1818-1829`, asserts `"exactly two entries" not in doc` and `"PERSONA_ALLOWLIST" in doc`) — created at `dd087f7`, cited by ledger rows `TD-19-PERPLEXITY-DOCSTRING` / `TD-18-ALLOWLIST-PARENTHETICAL` first-added at `841e7df`. Both PASSED here. Residual: Finding S-3 (WR-04 — the third assert at `:1829` is vacuous and the module exec is a side effect; the two docstring asserts are the mitigation and are live) | closed |
| T-28-09 | Tampering | (28-01) editing an ancestry-frozen module | mitigate | Guard status re-measured before editing (28-01-SUMMARY "Guard status re-measured"): `grep -rl phase16_persistence.py results/*.json` and the perplexity grep over `results/*.json tests/test_phase16_prereg.py tests/test_phase20_prereg.py` empty at the time. Re-measured here at HEAD: the only hit is `results/phase28_ledger.json` itself, whose `reason`/`evidence` strings name the two files (`:34`, `:92`, `:110`) — not a `module_sha256` pin (the ledger's 8 `module_sha256` mentions are the IN-0x FORBIDDEN-BY-GUARD reasons). Diff at `dd087f7` is docstring-only (`4 ++--` / `7 ++++---`, both hunks inside triple quotes); `tests/test_phase16_prereg.py` + `test_phase18_prereg.py` 109 passed in the executor's run. STOP rule never triggered | closed |
| T-28-SC | Tampering | (28-01) package installs | mitigate | `git log 62fd5db..HEAD -- pyproject.toml requirements.txt Makefile .github/workflows/ci.yml` → 0 commits; `pyproject.toml` sha256 = the pin at `tests/test_package.py:15`; `test_pyproject_sha256_pin_detects_any_change` (`:70-88`) and the D-25 four-tag equality PASSED — any dependency drift is RED at four revisions | closed |
| T-28-05 | Repudiation | (28-02) stamps read as "work done" | mitigate | Every stamp cites its evidence commit (28-02-SUMMARY Task 1 table: `7af6006`, `24d49ad`, `4012a61`, `c90d0c8`, `98d0a60`, `c71bade`) — all six resolve with `git cat-file -e` here; the debug stamp's `grep -n decode-crash results/phase18_extraction_report.md` → line 320 quoted; nothing RE-DEFERRED. Ledger rows `SS-DEBUG-DRAW-ALL`, `SS-QUICK-260819-R1U`, `SS-QUICK-260819-SGH`, `FM-QUICK-260902-DLO` carry `64e7162` and `tests/test_phase28_ledger.py::test_quick_task_summaries_are_named_for_the_audit_tool` / `test_debug_sessions_are_not_left_fixing` (`:237`, `:252`) as the regression, both PASSED | closed |
| T-28-07 | Tampering | (28-02) gsd-sdk mutation handlers | mitigate | Edits landed as `git mv` + Edit: `git show --name-status 64e7162` lists 8 `M` and 3 `R099/R100` renames, `4b00c80` one `M` (2 insertions, 2 deletions, frontmatter only). No `gsd-sdk state.*/roadmap.*/phase.*` invocation appears in any Phase 28 SUMMARY (grep → 0). Measured near-miss: Finding S-6 | closed |
| T-28-10 | Repudiation | (28-02) re-stamping a verifier's verdict | mitigate | `23-VERIFICATION.md:5` and `27-VERIFICATION.md:5` both read `status: human_needed` at HEAD; `git log 62fd5db..HEAD` on both files → 0 commits (D-35 by non-edit). Ledger rows `VER-23-HUMAN-NEEDED` / `VER-27-HUMAN-NEEDED` are `ACCEPTED`, not `FIXED` | closed |
| T-28-11 | Tampering | (28-02) archived prose rewritten under cover of repair | mitigate | 28-02-PLAN `files_modified` (11 paths, `:8-18`) equals the union of `64e7162`'s 11 paths (renames counted by new name) and `4b00c80`'s one path exactly; `git log 62fd5db..HEAD -- …/19-13-SUMMARY.md` → 0 commits; 28-02 deviation 3 records that stale names in PLAN prose / recorded `<automated>` commands were deliberately NOT rewritten, and 28-VERIFICATION ruling 1 accepts that | closed |
| T-28-SC | Tampering | (28-02) package installs | accept | AR-28-01 | closed |
| T-28-01 | Tampering | (28-03) reasons quoting record fields | mitigate | `tests/test_phase28_ledger.py::test_named_limitation_reasons_bound_to_record_fields_match_the_records` (`:160-180`): resolves each bound field by `_resolve` (`[]` descent, `:91-99`) and asserts `_prose.normalized(text) in _prose.normalized(row["reason"])` (`:172`); collect-then-assert. PASSED | closed |
| T-28-05 | Repudiation | (28-03) FIXED without a test / disposition read as fix | mitigate | Closed domain: `DISPOSITIONS` frozenset (`:28-36`), `test_disposition_domain_is_closed` (`:122-125`, also pins `schema.dispositions`); `_fixed_violations` (`:67-88`): `git cat-file -e <sha>^{commit}` (`:74`) and `pytest --collect-only -q <node id>` with the id required in stdout (`:80-86`); `test_fixed_rows_cite_a_commit_and_a_collectable_test` PASSED; planted RED `test_a_missing_test_node_id_is_red` on a `tmp_path` copy. Residual: Finding S-2 (WR-03 — the loose `_SHA` at `:38`; measured harmless on all 9 FIXED rows today) | closed |
| T-28-07 | Tampering | (28-03) gsd-sdk mutation handlers | mitigate | Todo moved with `git mv`: `git log --follow --name-status` shows `R088 .planning/todos/pending/… → .planning/todos/completed/…` at `841e7df`; `audit-open` (read-only query) quoted after the move (total 2). No mutation handler in the SUMMARY | closed |
| T-28-12 | Denial (of evidence) | (28-03) untracked ledger reddening clean-tree probes | mitigate | Ledger first-add `841e7df` (2026-09-21) before the wave-2 full suite (orchestrator: 2885 passed); `test_ledger_redump_is_byte_stable` (`:223`) PASSED; `git status --short results/phase28_ledger.json` empty here | closed |
| T-28-SC | Tampering | (28-03) package installs | accept | AR-28-01 | closed |
| T-28-01 | Tampering | (28-04) record edited to change the report | mitigate | `load()` reads every record with `read_bytes()` and records `(sha256, len)` (`scripts/phase28_report.py:206-213`); `_sources` writes them into the published `### Provenance` table with the record-carried `git_sha` (`:579-608`), the ledger as a rows-only digest + frozen byte count (`:591-599`, `:216-234`), and sha256 + bytes of the three frozen `.md` sources (`:605-607`). Frontier one-commit guard `tests/test_phase27_prereg.py:130` present; measured `git log -- results/phase25_frontier.json` → 1 commit. WR-02 closed: `tests/test_phase28_prereg.py::test_op_note_is_frozen_at_its_pin` (`:184`, `OP_NOTE_FROZEN_AT = ce2a151…` at `:148`, `_assert_frozen_at` `:151-167` with shallow refusal) PASSED; `git log ce2a151..HEAD -- results/phase25_operational_note.md` empty | closed |
| T-28-02 | Repudiation | (28-04) post-publish re-render | mitigate | `write` documented PRE-PUBLISH ONLY in the module docstring (`:18-20`) and `install` docstring (`:730`); `check()` re-renders and diffs both spans, exit 1 on drift or absent sentinels (`:778-798`) — exit 0 measured at HEAD; 28-06's `test_report_block_is_byte_identical` / `test_glance_block_is_byte_identical` (`tests/test_phase28_report.py:530-540`) PASSED. Residual: Finding S-1 (WR-01 — the freeze is discipline; the code half only detects record↔prose drift) | closed |
| T-28-03 | Tampering | (28-04) hand-typed numeral | mitigate | Templates carry only `${…}` placeholders and the D-19 exempt grammar: `test_template_scan_report_has_no_bare_numeral` / `…glance…` (`tests/test_phase28_report.py:95-102`) over `TEMPLATE_REPORT` / `TEMPLATE_GLANCE` (`.tmpl` paths, `phase28_report.py:59-60`) PASSED; 28-05's planted REDs PASSED (row below). Every quantity enters through `Bindings.__getitem__` (`:662-697`), which raises `KeyError` on a missing name | closed |
| T-28-06 | Information disclosure | (28-04) reading gitignored `logs/phase25_sweep.out` | mitigate | `grep -n 'logs/' scripts/phase28_report.py` → 0 hits (the only mention is the docstring's "never read" sentence, which contains no `logs/` token); the log line is bound as `${frontier.verdicts.adversarial_no_replay.log_line}` (28-04-SUMMARY binding inventory); `test_confound_is_quoted_from_the_records` asserts `"logs/" not in source` (`:365`) and that `phase25_sweep.out` occurs in the block exactly as often as inside the two record fields. PASSED | closed |
| T-28-13 | Tampering | (28-04) clock or HEAD SHA in bindings | mitigate | `PUBLISHED = "2026-09-21"` literal (`:53`) = `git log -1 --date=short 3b63b7d`; `grep -n -E 'today\(\)|datetime\.now|rev-parse'` over the renderer → 0 hits; `subprocess` is used only by `_source_text` for `git show <sha>:<path>` (`:237-243`), a pinned read. `test_renderer_has_no_clock_and_no_head_sha` (AST: attributes `today/now/utcnow`, string constants containing `rev-parse`/`logs/`/`mitigation_point_verdict`, `:457-474`) PASSED | closed |
| T-28-14 | Tampering | (28-04) mis-derived count (`cleared_counts.b == 4`) | mitigate | `_noised_dp_rows` selects `admission.rows` with `arm == "dp"` and frontier `sigma > 0` (`:324-331`); `derived.noised_dp_cleared_b` sums `cleared_b` over them (`:382`); 28-04 probe and 28-VERIFICATION SC1 both measured `'0'` while the record's `cleared_counts.b` (4) is rendered beside it and decomposed by leg | closed |
| T-28-SC | Tampering | (28-04) package installs | accept | AR-28-01; renderer imports are stdlib + repo modules only (`:27-50`); `test_renderer_imports_without_torch_in_a_fresh_interpreter` PASSED | closed |
| T-28-03 | Tampering | (28-05) hand-typed numeral in template | mitigate | `_bare_numerals` (`tests/test_phase28_report.py:57-66`: strip `${…}` then the eight `_EXEMPT` patterns, report any remaining digit with the file's own line numbers); `test_template_scan_planted_numeral_is_red`, `…bare_year_and_all_digit_sha_are_hits`, `…exempt_tokens_are_not_hits` all write to `tmp_path` (`:105-130`). All PASSED; 28-05-SUMMARY records the natural RED (`32 of` on template line 7, reverted with `git checkout`) | closed |
| T-28-04 | Repudiation | (28-05) shallow clone / hardcoded ancestry pair | mitigate | `_assert_recorded_before` (`tests/test_phase28_prereg.py:47-66`): `--is-shallow-repository == "false"` (`:49`), first-adds from `git log --diff-filter=A --format=%H -- <artifact>` (`:54`), strict ancestry via `merge-base --is-ancestor` plus a same-commit refusal (`:58-63`); the only hex literals in the file are `c673b4c` (the expectation commit) and `OP_NOTE_FROZEN_AT` — no first-add SHA typed. `test_a_planted_later_commit_is_red` (`:132-137`, HEAD as prereg) PASSED. Glob `results/phase2[0-8]_*` (`:32`) covers the ledger automatically | closed |
| T-28-01 | Tampering | (28-05) digest drift | mitigate | `test_provenance_digests_recompute_from_bytes` (`:286-312`): parses the rendered `### Provenance` table, recomputes every sha256 from `read_bytes()` (`:304`) and the ledger row from an independent `json.dumps(rows, sort_keys=True, ensure_ascii=False)` (`:294-297`), collect-then-assert, and asserts every `RECORDS` path was seen (`:312`). PASSED. Residual: Finding S-4 (IN-04 — the ledger `bytes` cell is compared to `ledger_frozen_bytes` itself; the sha side is independent and the byte-identity test pins the published 49057) | closed |
| T-28-06 | Information disclosure | (28-05) reading `logs/` | mitigate | Source-string check `"logs/" not in source` (`:365`) and the AST constant scan (`:465-474`) both PASSED; measured 0 hits in the renderer | closed |
| T-28-14 | Tampering | (28-05) mis-derived (a)/(b) counts | mitigate | `test_lead_is_the_gates_own_output` re-derives `noised` from `admission["rows"]` + `f["points"][…]["sigma"] > 0` without calling the renderer (`:386-398`), asserts `"{a} of {total}"` and `\b{b}\b` in the second lead line, and that the Relearning section carries `cleared_counts.b` and every `by_leg.<leg>.b` with `sum(by_leg.b) == cleared_counts.b` (`:400-410`). PASSED | closed |
| T-28-15 | Repudiation | (28-05) scan matching the test's own prose | mitigate | The scan reads `phase28_report.TEMPLATE_REPORT` / `TEMPLATE_GLANCE` (`.tmpl` files, `:96`, `:101`) and never a `.py` or rendered `.md`; the file docstring states the rule (`:4`). PASSED | closed |
| T-28-SC | Tampering | (28-05) package installs | accept | AR-28-01 | closed |
| T-28-02 | Repudiation | (28-06) post-publish re-render over published prose | mitigate | `test_report_block_is_byte_identical` / `test_glance_block_is_byte_identical` compare `_span(...) == render_*()` (`:530-540`) — PASSED; `check` exit 0; `git log 3b63b7d..HEAD -- docs/REPORT.md README.md` → 0 commits and the diff is empty, so `write` was not run after the publishing commit (its output would have to be a commit); the post-publish renderer change `89aae4f` (`ledger_frozen_bytes`) reproduces the published 49057-byte row (28-VERIFICATION ruling 4). `append_addendum` route: `tests/test_phase25_correction.py::test_no_continuation_was_written_by_append_addendum` PASSED (pinned total 3). Residual: Finding S-1 | closed |
| T-28-16 | Tampering | (28-06) clobbering prior REPORT/README content | mitigate | `install` proves `updated.startswith(prefix) and block in updated` on the produced bytes before writing (`scripts/phase28_report.py:761-766`) and refuses ambiguous sentinel counts (`:740-744`); `test_glance_deleted_nothing` (`tests/test_phase28_report.py:575-599`: pre-publish blob derived from git, first bullet after END equals the old first bullet, bullet count additive) PASSED; `tests/test_phase18_docs.py::test_docs_continuation_is_additive` + `test_phase15_docs.py` (15 tests) PASSED; publishing diff `docs/REPORT.md` +283/−0, `README.md` +19/−0 | closed |
| T-28-13 | Tampering | (28-06) clock in the block | mitigate | `PUBLISHED` pinned (`:53`); `test_published_date_is_pinned_not_clocked` (`:602-608`: ISO-date `fullmatch`, and the rendered `## ` title carries it) PASSED | closed |
| T-28-07 | Tampering | (28-06) gsd-sdk mutation handlers | mitigate | Publishing commit `3b63b7d` staged six files by explicit path (28-06-SUMMARY); STATE / ROADMAP untouched by the executor; no handler invocation in the SUMMARY (grep → 0). Finding S-6 | closed |
| T-28-17 | Denial (of review) | (28-06) freezing prose nobody read | mitigate | 28-06-PLAN Task 2 is `<task type="checkpoint:human-verify" gate="blocking">` (`:117`) and sits before Task 3 (`:142`); 28-06-SUMMARY records the developer's "approved" (2026-09-21, no wording change) with the publishing commit made after the read. Not provable from git metadata (Finding S-5's limitation applies) | closed |
| T-28-SC | Tampering | (28-06) package installs | accept | AR-28-01 | closed |
| T-28-08 | Elevation | (28-07) machine `git push` | mitigate | 28-07-PLAN Task 1 is `<task type="checkpoint:human-action" gate="blocking">` (`:75`); measured here `main == origin/main == 51bed45`, `origin/main..main` = 0; 28-07-SUMMARY: both pushes and the tag push were the developer's, and the first run `35719377808` failed before the second `35770563251` succeeded. Evidence limitation: Finding S-5 | closed |
| T-28-02 | Repudiation | (28-07) row edit after publish | mitigate | Rows digest recomputed here from `git show 3b63b7d:…` and HEAD: `bb9f82fe290d7578…` both, 69 rows both; `git diff 3b63b7d HEAD -- results/phase28_ledger.json` is the `close` block only (+7/−1, 28-07-SUMMARY); byte-identity tests re-run PASSED; `test_ledger_size_column_is_invariant_under_close` (`:315-331`) PASSED | closed |
| T-28-07 | Tampering | (28-07) gsd-sdk handlers on STATE/ROADMAP/REQUIREMENTS | mitigate | 28-07-SUMMARY quotes `diff -u` hunk counts per file (REQUIREMENTS 2 hunks +4/−2, ROADMAP 2 hunks +2/−1, STATE 5 hunks +17/−10); STATE.md frontmatter fences parse at HEAD; ROADMAP.md and REQUIREMENTS.md carry no frontmatter at HEAD and none at `62fd5db` (first line `# Roadmap: PersonaCore` / `# Requirements — …` at both). Finding S-6 (the orchestrator's `state.begin-phase` near-miss, reverted at `18680f7`) | closed |
| T-28-18 | Repudiation | (28-07) CI "green" on a head lacking the report | mitigate | `git merge-base --is-ancestor 3b63b7d d2dcbe2` → 0 measured here; ledger `close.ci_run` = `{conclusion: success, head_sha: d2dcbe2bb8ec1dac5db4543e877681db3fd577c5, id: 35770563251, recorded: 2026-09-22, url: …}`; `test_close_block_shape` (`tests/test_phase28_ledger.py:215`) PASSED; `ci.yml` `fetch-depth: 0` (`:28`) so the tag / ancestry guards run non-shallow in CI | closed |
| T-28-19 | Tampering | (28-07) scope creep into `/gsd-complete-milestone`'s files | mitigate | `git status --short .planning/PROJECT.md .planning/MILESTONES.md` empty; `git log 62fd5db..HEAD` on both → 0 commits; `git tag -l v4.0` empty | closed |
| T-28-SC | Tampering | (28-07) package installs | accept | AR-28-01 | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

### Open

None.

---

## Threat Flags (from SUMMARY `## Threat Flags`)

| Flag | Source | Maps to | Disposition |
|------|--------|---------|-------------|
| none | 28-01, 28-02, 28-05, 28-07 SUMMARYs each state "None — no new surface" | — | informational |

**Unregistered flags:** none. Two implementation-time additions were checked for unmapped surface
and map to existing IDs: the `path.<name>` binding prefix (28-04 deviation 1) is a template-side
name table read by `Bindings.__getitem__` → T-28-03 (it exists so the numeral scan did not have to
be widened); `ledger_frozen_bytes` (28-07 deviation 1, `89aae4f`) is a pure function of the ledger
dict → T-28-01 / T-28-02.

---

## Findings

- **S-1 (WARNING, measured, UNRULED — deliberately not in the Accepted Risks Log; T-28-02, 28-04 /
  28-06 / 28-07 rows).** 28-REVIEW WR-01: `main()`'s `write` branch (`scripts/phase28_report.py:806-810`)
  calls `install`, whose `n_begin == 1` branch replaces a present span in place (`:745-749`) —
  nothing in the module refuses once the pair exists, and `test_report_block_is_byte_identical`
  compares the committed span with a *fresh* render, so a re-`write` followed by a commit would land
  green. The plan sentences hold as written ("`write` documented pre-publish only; `check` detects
  drift; byte-identity test"; "`write` not run after the commit"), and the freeze is measured intact
  today (0 commits touch `docs/REPORT.md` / `README.md` after `3b63b7d`; `check` exit 0). The
  code-enforced half guards record↔prose drift, not the re-render itself; the freeze rests on D-20
  discipline plus the `append_addendum` census in `tests/test_phase25_correction.py`. The developer
  should rule on WR-01 (the review's one-line `_prove` in `main()` would make the freeze code) or
  carry it to v5.0.
- **S-2 (INFO, measured, UNRULED; T-28-05, 28-03 row).** WR-03: `_SHA = r"\b[0-9a-f]{7,40}\b"`
  (`tests/test_phase28_ledger.py:38`) matches decimal runs and `_fixed_violations` resolves only
  `shas[0]`. Measured on all 9 FIXED rows at HEAD: the loose pattern's first match equals the strict
  pattern's (`(?=[0-9a-f]*[a-f])`, the one `tests/test_phase28_report.py:49` uses) first match on
  every row — `dd087f7` ×2, `64e7162` ×6, `1a89294` ×1 — and every one resolves as a commit. The
  guard is correct on the ledger as it stands; the false-RED / false-GREEN paths open only if a
  future FIXED row's evidence puts a 7+-digit decimal before its SHA.
- **S-3 (INFO, measured, UNRULED; T-28-05, 28-01 row).** WR-04: the third assert of
  `test_overwrite_statement_docstring_does_not_type_the_allowlist_size` (`:1829`,
  `isinstance(len(...), int) and len(...) >= 1`) cannot fail, and `:1823-1828` executes
  `tests/test_phase14_scoring.py`'s top level as a side effect. The two docstring asserts at
  `:1822` and `:1823` are the declared mitigation and are live (natural RED recorded in
  28-01-SUMMARY). No register sentence is falsified.
- **S-4 (INFO, T-28-01, 28-05 row).** IN-04: for the ledger row, `test_provenance_digests_recompute_from_bytes`
  compares the `bytes` cell to `phase28_report.ledger_frozen_bytes(...)` (`:301`) — the renderer's own
  function — while the sha cell is recomputed independently (`:294-297`). The published byte count
  49057 is nonetheless pinned: it equals `git show 3b63b7d:results/phase28_ledger.json | wc -c`
  (measured) and the byte-identity test compares the whole committed span.
- **S-5 (INFO, evidence limitation, T-28-08 / T-28-17).** All 28 commits in `62fd5db..HEAD` carry
  author `Rafael` and 0 `Co-Authored-By` / Claude trailers, so git metadata cannot distinguish the
  developer's pushes and approvals from machine actions. The machine-checkable half is measured
  (`main == origin/main`, the two CI runs and their heads, no `git push` in any executor transcript);
  the human half rests on the two blocking checkpoints and the recorded answers in 28-06-SUMMARY
  Task 2 and 28-07-SUMMARY Task 1 (Phase 27 precedent S-3).
- **S-6 (INFO, measured near-miss, T-28-07).** Zero `gsd-sdk` mutation handlers were called by any
  executor. The orchestrator's single call (`state.begin-phase`) corrupted STATE.md and was reverted
  before commit — the record is the commit message of `18680f7` ("mark phase executing —
  hand-applied (state.begin-phase reverted)", 1 file, +3/−3). This is the eleventh consecutive
  session in which the handlers corrupted planning frontmatter (memory: gsd-sdk mutation handlers);
  the mitigation held because the snapshot → diff discipline caught it.
- **S-7 (WARNING, documentation).** Three of seven SUMMARYs (`28-03`, `28-04`, `28-06`) carry no
  `## Threat Flags` section. Nothing is unmapped (see Threat Flags above), but the executor's
  "no new surface" attestation is absent for the three plans that added the most code (Phase 26/27
  precedent S-1).
- **T-28-09 note.** The 28-01 re-measurement ran on a tree without the ledger; at HEAD the same grep
  hits `results/phase28_ledger.json` because its own row text names both edited files. That is not a
  provenance pin — a future re-measurement should exclude the ledger, or grep for `module_sha256`
  pins specifically.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-28-01 | T-28-SC | Plan-time accept (28-02 … 28-07; `mitigate` in 28-01 by the D-25 test): no package installed in the phase — `git log 62fd5db..HEAD -- pyproject.toml requirements.txt Makefile .github/workflows/ci.yml` → 0 commits; `pyproject.toml` sha256 `15ffd6b5…926f` equals `PYPROJECT_SHA256`; `test_runtime_dependencies_identical_across_four_milestones` and `test_pyproject_sha256_pin_detects_any_change` PASSED; the renderer is stdlib + repo modules only | plan-time disposition (28-01 … 28-07 PLAN); logged by `/gsd:secure-phase 28` | 2026-09-22 |

*Accepted risks do not resurface in future audit runs.*

WR-01, WR-03, WR-04 and IN-04 are **not** accepted here (Findings S-1 … S-4): no developer ruling
names them. They belong on the v5.0 carry list or in a ruling, not in this log.

---

## Security Audit Trail

| Audit Date | Threats Total (rows / ids) | Closed | Open | Accepted | Run By |
|------------|----------------------------|--------|------|----------|--------|
| 2026-09-22 | 40 / 20 | 40 | 0 | 1 row (plan-time `T-28-SC`) | `/gsd:secure-phase 28` — gsd-security-auditor, from the plan-time register, HEAD `51bed45` |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-22
