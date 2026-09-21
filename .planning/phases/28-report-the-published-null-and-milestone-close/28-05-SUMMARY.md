---
phase: 28-report-the-published-null-and-milestone-close
plan: 05
subsystem: report-tests
tags: [tests, template-scan, obligations, provenance, ancestry, rpt-01]
requires: ["28-04"]
provides:
  - tests/test_phase28_report.py — template scan (+ planted RED), obligation resolution, constants vs module pins, provenance digests, confound, lead/caveat, D-07, torch-free + no-clock probes, dead-quote census
  - tests/test_phase28_prereg.py — every QUOTES entry verbatim at its pinned source; c673b4c a strict ancestor of every results/phase2[0-8]_* first-add, shallow-refusing
affects: ["28-06 (adds the byte-identity tests to test_phase28_report.py once the blocks are installed; TD-XC-README-GLANCE evidence cites this file)"]
tech-stack:
  added: []
  patterns: [strip-placeholders-then-exempt-grammar scan of .tmpl sources, collect-then-assert over record paths, git-derived first-adds with shallow refusal, AST reads of frozen modules]
key-files:
  created:
    - tests/test_phase28_report.py
    - tests/test_phase28_prereg.py
  modified: []
decisions:
  - "The wildcard obligation `points.<key>.verdict.*` expands over all 16 `canary.audited_point_keys`; the sigma=0 control (canary `verdict: null`, frontier `epsilon: null`, `comparison` starting `VACUOUS BY CONSTRUCTION`) is accepted as the record's own named degenerate case rather than a miss — 15 expansions per wildcard path, counted from the record"
  - "Provenance digests are read from the rendered `### Provenance` table (the ledger row via its `(rows only)` suffix) — `table.sources` is dispatched inside `Bindings`, not in `TABLES`, so the rendered section is the one artifact the reader sees"
  - "Prose compared against blockquoted slices is dequoted (`^> ?` stripped per line) before `normalized`, because the `> ` prefix lands inside a wrapped paragraph after whitespace collapse"
metrics:
  duration: "1 session"
  completed: "2026-09-21"
---

# Phase 28 Plan 05: Renderer Guards as CPU Tests Summary

SC2's guarantees are now tests: the two template sources carry no numeral outside the D-19 grammar (scan of the `.tmpl` files only, planted REDs in `tmp_path`), all 14 obligation paths resolve against the assembled records and every scalar is published in the rendered block, every ε/σ/C/q/δ/K the report binds equals its module pin (q/clip_norm over the 30 noised DP points only, count record-derived), every provenance digest recomputes from `read_bytes()` / the canonical rows dump, the confound and the lead are the records' own strings under `_prose.normalized`, the renderer is torch-free and clock-free, and `c673b4c` is a strict ancestor of the earliest first-add of all 97 tracked `results/phase2[0-8]_*` files, derived from git at test time.

## Commit

| Task | Commit | Content |
|------|--------|---------|
| 1 + 2 | `13ce840` | `tests/test_phase28_report.py` (15 tests), `tests/test_phase28_prereg.py` (5 tests) |

## Test counts

- `.venv/bin/pytest tests/test_phase28_report.py -q` → **15 passed in 0.65s** on the committed 28-04 tree (`e319acb`), first run.
- `.venv/bin/pytest tests/test_phase28_prereg.py tests/test_phase28_report.py -q` → **20 passed in 9.59s** (the ancestry test runs ~97 `git log --diff-filter=A` calls).
- `make lint` → All checks passed, 288 files formatted (after `ruff format` fixed six E501 lines).
- Census over `scripts/` + `tests/`: `test_phase25_driver test_phase25_epsilon test_phase25_plots test_phase25_watch test_phase21_sc5 test_lora_inject test_phase25_grid test_phase25_probe2` → 115 passed, 2 failed while the files were untracked (`…from_import_variant…` and `…planted_bit_identity…` are clean-tree probes: `?? tests/test_phase28_prereg.py / ?? tests/test_phase28_report.py`); both pass after the commit (2 passed).
- **Full suite NOT run** (~25 min; the orchestrator runs it after the wave, per the execution brief — the plan's "background full suite" step was superseded by that instruction).

## RED transcripts

**Natural RED, `test_template_scan_report_has_no_bare_numeral`** — a bare `32` planted in the working-tree template (`sed` on line 7, then `git checkout scripts/phase28_report.md.tmpl`; `git status --short scripts/` empty afterwards):

```
>       assert hits == [], "\n".join(f"{n}: {line}" for n, line in hits)
E       AssertionError: 7: The mechanism: 32 of ${derived.noised_dp_total} noised DP points cleared condition (a) and ${derived.noised_dp_cleared_b} cleared condition (b) — ${frontier.verdicts.dp_recall_disclosure.finding} DP removed the leakage by removing the memory.
E       assert [(7, 'The mec...the memory.')] == []
tests/test_phase28_report.py:94: AssertionError
1 failed in 0.17s
```

**Planted REDs inside the suite (tmp_path only):** `test_template_scan_planted_numeral_is_red` (one hit on line 3, `32 of`), `test_template_scan_bare_year_and_all_digit_sha_are_hits` (`2026` and `1234567` each one hit), `test_template_scan_exempt_tokens_are_not_hits` (`Phase 28 RELRN-02 D-25-18-ADV64-REFUSED 2026-09-05 c673b4c §12.5c 23-12 v3.0 sha256` → no hit).

**Ancestry RED, `_assert_recorded_before("HEAD", [tracked[0]])`** (the mechanism `test_a_planted_later_commit_is_red` wraps in `pytest.raises`):

```
RED: CalledProcessError Command '('git', 'merge-base', '--is-ancestor', 'e319acbb33ec7936ee35ebbf23fe3f8b941278db', '2a3239491549c96c882c8ef0addfc8b1ad2239d4')' returned non-zero exit
```

## What each test binds to (measured on the records, never typed)

- Constants: `epsilon_for(16.0, 200, 1e-05) == points.dp_n8_sigma16p000000.epsilon`; `derived.sigma_for_eps4 == repr(sigma_for(4.0, steps, δ))` (renders `15.289937507119`); `CURVE_K == verdicts.curve_k`, `FULL_FIDELITY_K == verdicts.full_fidelity_k == AST-read phase18_extraction.K`; `DELTA` and `STEP_BUDGET` over all 44 points; `SAMPLING_RATE_Q`/`CLIP_NORM` over `noised = dp arms with sigma > 0` (`len(noised) == len(dp_keys) - len(dp_sigma_zero)`), the two σ=0 controls asserted `clip_norm != CLIP_NORM`, the twelve `adv_*` points asserted `q is None and clip_norm is None`; `SIGMA_LADDER == sorted dp_n8 sigmas`; `F_Y == admission.budget.f_y`, `MARGIN_K == admission.budget.margin_k`.
- Lead: (a)/(b) re-derived from `admission.rows` + frontier `sigma` (30 of 30, 0); Relearning section carries `cleared_counts.b` and every `by_leg.<leg>.b`, with `sum(by_leg.b) == cleared_counts.b`; the `87/1008` caveat (built from `control_readings.dp_n64.recall_counts.taught`) precedes the first `\n### `.
- Confound: `adversarial_no_replay.{finding,log_line,log_source,dp_replay_source}`, `amended_criterion`, `leg_refusals.adv_n64`, the first refused point's `early_return_reason`, and the first paragraph of §12.5c of the operational note are all in the (dequoted) block; `logs/` is absent from the renderer source; `phase25_sweep.out` occurs in the block exactly as often as inside the two record fields (2).
- Provenance: 10 rows (six JSON records + ledger `rows` + three results/*.md) — every sha256 and byte count recomputes; the ledger row re-hashes `json.dumps(rows, sort_keys=True, ensure_ascii=False)` independently.
- Quotes: all 7 `QUOTES` present verbatim in their sources; 3 name `git:c673b4c:`; both templates use every quote (no dead quote); `72σ` and `σ ≥ 15.3` (sliced from the quotes by regex) are restated in `.planning/REQUIREMENTS.md` and `.planning/ROADMAP.md` at HEAD.

## Deviations from Plan

**1. [Plan premise vs record] The σ=0 control has no canary verdict.** The plan's wildcard expansion "asserting `verdict.verdict ∈ VERDICTS` for that row" cannot hold for `dp_n8_sigma0p000000`: the canary record stores `verdict: null` with `comparison: "VACUOUS BY CONSTRUCTION: …"` (as `tests/test_phase26_canary.py:665-666` already asserts). The test accepts that row only when the frontier's `epsilon` is also `null` and the `comparison` names the case; the 15 real expansions per wildcard path are counted from `len(audited_point_keys) - 1`. Not a renderer change.

**2. [Plan premise vs 28-04 code] `TABLES["sources"]` does not exist.** `table.sources` is dispatched inside `Bindings.__getitem__` because it needs the `load()` digests. The provenance test parses the rendered `### Provenance` section instead (the plan's stated alternative).

**3. [Rule 1 - Test correctness] Blockquoted slices are dequoted before comparison.** `blockquote.op_note_12_5c` prefixes each line with `> `, so a wrapped paragraph normalizes to `… control, zero adversarial > episodes …`; the test strips `^> ?` per line before `normalized`, otherwise the §12.5c check would be a false RED.

**4. [Orchestrator instruction] Full suite not launched in the background.** The plan's Task 2 asks for it; the execution brief forbids it (~25 min) and assigns it to the orchestrator after the wave.

**5. Plan-listed analog helpers not copied verbatim:** `_called_names`/`_markers`/`_span` from `test_phase25_correction.py` were not needed (no sentinel or call-site checks in this plan); `_anchored_section` was copied from `test_phase18_docs.py` with `stop` defaulting to `### ` since every section here is a third-level heading.

## Known Stubs

None.

## Threat Flags

None — the tests read committed records, the two templates, the renderer source and git history; no new surface.

## Note for 28-06

- Byte-identity tests go into `tests/test_phase28_report.py` (reuse the `records`/`block` fixtures; compare `phase28_report._span(REPORT_PATH, REPORT_STEM) == render_report()` with `==`, per D-22).
- `test_every_obligation_path_resolves` and `test_provenance_digests_recompute_from_bytes` re-render on every run, so flipping `TD-XC-README-GLANCE` (rows digest change) needs no test edit — the ledger row is recomputed from the record.
- `test_expectation_commit_precedes_every_v4_result` globs `results/phase2[0-8]_*`, so any new `results/phase28_*` file committed by 28-06/28-07 is automatically covered; c673b4c (2026-08-20) precedes all of them by construction.

## Self-Check: PASSED

- `tests/test_phase28_report.py` FOUND · `tests/test_phase28_prereg.py` FOUND · both tracked (`git ls-files` → 2)
- commit `13ce840` FOUND on `main`; `scripts/`, `.planning/STATE.md`, `.planning/ROADMAP.md` untouched (`git status --short` empty for all three)
