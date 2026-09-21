---
phase: 28-report-the-published-null-and-milestone-close
plan: 04
subsystem: report-renderer
tags: [renderer, template, bindings, byte-identity, rpt-01]
requires: ["28-03"]
provides:
  - scripts/phase28_report.py — stdlib-only renderer (resolve, Bindings, DERIVED, TABLES, QUOTES, SLICES, render_report, render_glance, install, check, main)
  - scripts/phase28_report.md.tmpl — the docs/REPORT.md section, placeholders only, D-01 order
  - scripts/phase28_glance.md.tmpl — the README `Results at a glance` v4.0 + v3.0 bullets
affects: ["28-05 (tests bind to these names)", "28-06 (runs `write`, flips TD-XC-README-GLANCE, may edit PUBLISHED before the publishing commit)", "28-07 (fills ledger close.ci_run; rows digest unaffected)"]
tech-stack:
  added: []
  patterns: [string.Template with a dotted braceidpattern, Mapping-dispatch bindings, quotes proved verbatim under _prose.normalized at render, anchored .md slices, produced-bytes prefix proof]
key-files:
  created:
    - scripts/phase28_report.py
    - scripts/phase28_report.md.tmpl
    - scripts/phase28_glance.md.tmpl
  modified: []
decisions:
  - "Repo paths are bound through a `path.<name>` prefix: a path such as `scripts/phase28_report.py` carries digits the D-19 grammar does not exempt, and extending the grammar would weaken the scan 28-05 makes a test"
  - "The `##` title is a derived binding (`derived.report_title`) so the README anchor (`derived.report_anchor`, `_github_anchor` rule) is computed from the same string and cannot drift from the heading"
  - "The provenance table digests only FROZEN sources (the six JSON records, the ledger `rows`, three results/*.md); `.planning/REQUIREMENTS.md` and `ROADMAP.md` are quoted/sliced (proved verbatim at render) but not digested — they are edited at milestone close, so a digest over them would break byte-identity by construction"
  - "The canary `epsilon_sentence` (7,026 chars, 12 newlines) is not a per-row table column; the bracket point's first paragraph is quoted once beside its verdict (`derived.canary_epsilon_sentence_bracket`)"
  - "The σ=0 row of the ε table renders the first clause of `epsilon_report.control_has_no_epsilon` and the first clause of the canary point's own `comparison` field (`VACUOUS BY CONSTRUCTION`) — the canary record stores `verdict: null` for the control"
metrics:
  duration: "1 session"
  completed: "2026-09-21"
---

# Phase 28 Plan 04: The Report Renderer and Templates Summary

A stdlib-only renderer whose every output number is addressed by a `${prefix.path}` binding to a committed record field, module constant, ledger row, verified verbatim quote or record-derived function — and two templates whose source carries no bare numeral outside the D-19 grammar. Nothing was written into `docs/REPORT.md` or `README.md`; `check` exits 1 with `PHASE28-REPORT sentinels absent (pre-publish state)` / `PHASE28-GLANCE sentinels absent (pre-publish state)`.

## Commit

| Task | Commit | Content |
|------|--------|---------|
| 1 + 2 | `1a89294` | `scripts/phase28_report.py`, `scripts/phase28_report.md.tmpl`, `scripts/phase28_glance.md.tmpl` |

## Binding-name inventory (133 distinct `${…}` across both templates, measured by regex)

- **admission (10):** apparatus.reason · apparatus.status · cleared_counts.b · cleared_counts.by_leg.{adv_n64,adv_n8,dp_n64,dp_n8}.b · provenance.git_sha · verdict.reasons.0 · verdict.verdict
- **blockquote (2):** op_note_12_5c · roadmap_v5
- **canary (16):** auditor_ceiling · curve_total_is_context_only · emitted_git_sha · exclusions.out.n · exclusions.out.of · exclusions.rule · points.dp_n8_sigma12p000000.verdict.verdict · points.dp_n8_sigma16p000000.verdict.verdict · power_gate.{control_epsilon_lower,passed,sentence,threshold} · reachable_claims · summary.{BROKEN,CONSISTENT,INCONCLUSIVE}
- **const (1):** phase25_prereg.CANARY_RESERVATIONS.canary_population_rule (dict descent implemented; `const.phase18_extraction.K` resolves by AST and is asserted `'48'` in the verify probe)
- **derived (25):** adv_n64_dialogue_range · adv_n64_refused_count · adv_n64_retention_range · canary_audited_count · canary_epsilon_sentence_bracket · capacity_n8 · capacity_n64 · ledger_named_limitation_count · ledger_total · ledger_v3_count · ledger_v3_stale_stamp_count · ledger_v3_tech_debt_count · ledger_v4_count · noised_dp_cleared_a · noised_dp_cleared_b · noised_dp_total · recall_fraction.{dp_n8,dp_n64}.{taught,heldout} · report_anchor · report_title · reproduce_sigma · sigma_for_eps4 · target_epsilon_fact
- **frontier (38):** arms.0..3 · epsilon_report.{control_has_no_epsilon,curve_total_epsilon,k,selection_accounted,selection_accounted_reason,total_delta} · points.adv_n64_ratio0p000000.verdict.early_return_reason · points.dp_n64_sigma0p000000.sigma · points.dp_n8_sigma0p000000.sigma · points.dp_n8_sigma12p000000.{epsilon,sigma} · points.dp_n8_sigma16p000000.{composed_steps,delta,epsilon,sigma} · provenance.git_sha · verdicts.adversarial_no_replay.{code_source,dp_replay_source,finding,log_line,log_source,note} · verdicts.amended_criterion · verdicts.arm_existentials.{adversarial,dp} · verdicts.capacity_branch · verdicts.dp_recall_disclosure.finding · verdicts.leg_refusals.adv_n64 · verdicts.tallies_by_leg.{adv_n64.REFUSED,adv_n8.INCONCLUSIVE,dp_n64.FAIL,dp_n64.PASS,dp_n8.FAIL,dp_n8.PASS}
- **ledger (8):** row.CANARY-COULD-NOT-HAVE-FAILED.{id,reason} · row.D40-LIMITATION-2.id · row.RELRN-02.reason · row.SC3-SHA256-CLAUSE.{id,reason} · row.WR-05.{id,reason}
- **path (16):** admission · canary_script · erasure_report · extraction_report · figure_adv · figure_dp · frontier · ledger · op_note · prereg_test · privacy_pkg · relearn_script · renderer · requirements · research_summary · roadmap
- **quote (7):** expectation_l8 · expectation_lever · expectation_threshold · req_23_12_retraction · v3_erasure_verdict · v3_extraction_verdict · v3_ship_decision (each proved present in its source under `_prose.normalized` at bind time; the three expectation quotes against `git show c673b4c:.planning/research/SUMMARY.md`)
- **table (10):** adv_points · build_pointers · cleared_by_leg · epsilon_by_sigma · ledger_by_disposition · named_limitations · self_corrections · sources · tallies_by_leg · withheld_claims

Also addressable but unused by the templates: `meta.published` (folded into `derived.report_title`), `slice.req_23_12_continuation` (84 lines — replaced by `quote.req_23_12_retraction`, its first paragraph, per the plan's >40-line rule), `derived.{noised_dp_cleared_c,sigma_zero_deviation_over_floor,obligation_count,n_arms,ledger_rows_sha256,control_has_no_epsilon_first_clause}`, `ledger.count.<DISPOSITION>`, `sigma_zero.*`, `cost.*`, `control_floor.*` (the phase-23 values are rendered through `table.self_corrections`).

## Dry render

- `/private/tmp/claude-501/-Users-juliorcoelho-PersonaCore/a41ea984-c9aa-44a1-8392-743a747586ce/scratchpad/28-04-render/phase28_report.md` — 283 lines, 54,619 bytes, exactly one `## ` heading
- `/private/tmp/claude-501/-Users-juliorcoelho-PersonaCore/a41ea984-c9aa-44a1-8392-743a747586ce/scratchpad/28-04-render/phase28_glance.md` — 17 lines, no `## `
- Two consecutive `render_report()` / `render_glance()` calls are byte-identical (asserted).

## Residual numeral-scan hits

`grep -nP '\d' scripts/phase28_report.md.tmpl | grep -vP '\$\{[^}]*\}'` → one line: `115:### What v5.0 would measure` (milestone tag, exempt). The plan's full scan (strip `${…}` and the D-19 exempt list, then look for any digit) passes on both templates.

## Acceptance greps on the rendered report (line numbers, before the three end-to-end fixes shifted nothing above line 20)

`null-at-both-capacities` → 2, 6, 10, 170 · `0 of 32 point(s) examined returned PASS` → 6, 199 · `0 of 6 point(s)` → 6, 200 · `Every DP point above sigma=0` → 8 · `87/1008` → 10 · `72σ` → 10, 16 · `5.299979064701441` → 22, 42 · `3.7965357228934966` → 22, 43, 49 · `15.289937507119` → 22 · `2387.299119573244` → 49, 51 · `7,581 teaching + 0 replay` → 61, 71 · `replay_windows=256` → 61 · `D-25-18-ADV64-REFUSED` → 96, 197, 231 · `MOOT` → 130… · `HALT` → 150 · `phase25_frontier_dp.png` → 160 · `### Named-limitation register` → 204 · `### What v5.0 would measure` → 245 · `### Provenance` → 266.

D-07 lines (every line carrying the bracket ε also carries its canary verdict):

- `| "reaching ε_fact ≤ 4 needs σ ≥ 15.3 \`[MEASURED, this synthesis]\`" — … | σ=12.0 → ε 5.299979064701441 (canary \`CONSISTENT\`); σ=16.0 → ε 3.7965357228934966 (canary \`CONSISTENT\`) | \`accountant.sigma_for(target ε = 4.0, steps = 200, δ = 1e-05)\` = 15.289937507119 |`
- ε-table rows `| 12.0 | 5.299979064701441 | FAIL | FAIL | CONSISTENT | …` and `| 16.0 | 3.7965357228934966 | FAIL | FAIL | CONSISTENT | …`
- `The bracket point's own sentence, as the canary record carries it beside its verdict \`CONSISTENT\`: "AT THE PRIVACY UNIT … eps = 3.7965357228934966 …"`

## Verification

- Task 1 probe: torch absent from `sys.modules` after import; `derived.noised_dp_total == '30'`, `noised_dp_cleared_a == '30'`, `noised_dp_cleared_b == '0'` (from `rows` + `sigma > 0`, not `cleared_counts.b`, which is 4); `sigma_for_eps4 == '15.289937507119'`; `const.mitigation_budget.FULL_FIDELITY_K == '48'`, `const.phase18_extraction.K == '48'`; missing field and unknown prefix both raise `KeyError`; source contains none of `today()`, `datetime.now`, `rev-parse`, `os.replace`, `logs/`, `mitigation_point_verdict`, `import phase18_extraction`, `train_arm(`.
- Task 2 verify script (template scan + rendered assertions + D-07 line check + `7,581 teaching + 0 replay` / `replay_windows=256`): `templates OK`.
- `make lint`: All checks passed, 286 files formatted.
- Census tests over `scripts/*.py`: `tests/test_phase25_driver.py tests/test_phase21_unit_continuation.py tests/test_phase23_ctrl.py tests/test_phase21_sc5.py tests/test_phase25_prereg.py tests/test_lora_inject.py` (108 passed, planted/clean-tree probes deselected while the files were untracked) and the `census`/`call_site` selections of `tests/test_phase20_correction.py tests/test_phase23_resume.py tests/test_phase19_erasure.py` (7 passed).
- **Full suite NOT run** (~25 min; the orchestrator runs it after the wave).

## Deviations from Plan

**1. [Rule 3 - Blocking] `path.<name>` binding prefix added.** The D-19 grammar the verify script enforces exempts no path-shaped token, so `scripts/phase28_report.py`, `tests/test_phase28_prereg.py`, `results/phase25_frontier_dp.png` etc. could not be typed in the template. Added a `PATHS` dict and `path.` dispatch rather than widening the scan. Commit `1a89294`.

**2. [Rule 1 - Bug, found reading the dry render] The bracket row said "σ ≥ 16.0 was never run".** The first draft bound `derived.reproduce_sigma` (16.0) where the recorded threshold is 15.3. Fixed by adding `quote.expectation_threshold` ("reaching ε_fact ≤ 4 needs σ ≥ 15.3 `[MEASURED, this synthesis]`", proved verbatim at `c673b4c`) — the number stays a quote, never typed. Same commit.

**3. [Rule 2 - Correctness] Provenance table digests only frozen sources.** The plan's `table.sources` listed every JSON record + the ledger rows digest; the draft also digested `.planning/REQUIREMENTS.md` and `.planning/ROADMAP.md`, which 28-06/28-07 edit at close (RPT ticks, Phase 28 row) — that would make the 28-06 byte-identity test red on the very commit that publishes. Dropped those two rows; `results/phase25_operational_note.md`, `results/phase18_extraction_report.md`, `results/phase19_erasure_report.md` stay (frozen evidence). Quotes and slices from the two planning files are still proved verbatim at every render.

**4. [Rule 1 - Bug] "56 of 56 excluded" misread `canary.exclusions.out`.** `n` is the population size after exclusions (`excluded: []`), not the excluded count. Rendered as "Out-of-corpus canary population after exclusions: 56 of 56 (rule: `either`)".

**5. Plan-permitted substitutions:** `canary.epsilon_sentence` is not a per-row table column (7 kB with blank lines; first paragraph of the bracket point quoted once beside its verdict); `slice.req_23_12_continuation` (84 lines) replaced by `quote.req_23_12_retraction` per the plan's >40-line clause; the ε-table σ=0 row's canary cell is the first clause of the point's `comparison` field because the canary record stores `verdict: null` for the control; `cleared_by_leg` rows are ordered by `frontier.arms`, not the record's alphabetical key order.

## Note for 28-05 / 28-06

- Sentinel stems `PHASE28-REPORT` / `PHASE28-GLANCE`; `render_report()` / `render_glance()` return `"\n" + body + "\n"`, and `install` writes exactly `BEGIN + block + END`, so `_span(...) == render_*()` is the byte-identity comparator.
- `PUBLISHED = "2026-09-21"`; 28-06 may edit it before the publishing commit, never after (the title and README anchor both derive from it).
- Ledger `TD-XC-README-GLANCE` evidence should cite `1a89294` + `tests/test_phase28_report.py::test_glance_block_is_byte_identical`.
- The rows digest at this commit: `2056884a8c3175e712dd94f52348439645091d794fbfbe934adc3dabf0aecd4f` (48,883 B file); it changes when 28-06 flips the row — re-render before the publishing commit.

## Self-Check: PASSED

- `scripts/phase28_report.py` FOUND · `scripts/phase28_report.md.tmpl` FOUND · `scripts/phase28_glance.md.tmpl` FOUND
- commit `1a89294` FOUND on `main`; `docs/REPORT.md`, `README.md`, `.planning/STATE.md`, `.planning/ROADMAP.md` untouched
