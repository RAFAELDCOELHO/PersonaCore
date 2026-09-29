---
phase: 34-v5-0-report-and-milestone-close
plan: 04
subsystem: v5.0 report renderer (scripts/phase34_report.py)
tags: [report, renderer, templates, numeral-scan, post-hoc-contract]
requires: [results/phase32_frontier.json, results/phase33_admission.json, results/phase34_ledger.json, scripts/phase28_report.py (frozen, imported)]
provides: [phase34_report.Bindings, render_report, render_glance, install_glance, check, CONTRACT, COVERED_BY, phase34_report.md.tmpl, phase34_glance.md.tmpl]
affects: [34-05 (install + byte-identity tests + developer read)]
tech-stack:
  added: []
  patterns: [subclass of the frozen phase28 Bindings with its own dispatch, KeyError on unknown prefix, post-hoc contract with COVERED_BY coverage]
key-files:
  created:
    - scripts/phase34_report.py
    - scripts/phase34_report.md.tmpl
    - scripts/phase34_glance.md.tmpl
    - tests/test_phase34_report.py
  modified: []
decisions:
  - "CONTRACT names verdicts.condition_c_vs_v4 field by field (rows, by_leg, notes, statement), so that dropping ${table.condition_c_vs_v4} is actually uncovered"
  - "ledger_by_reference_count = rows whose milestone is not v5.0 (the v4.0 and v3.0 rows carried by reference: 5), not milestone == v4.0 (3)"
requirements-completed: []
# RPT-04 is not ticked here: nothing is installed until 34-05, and ticks happen only in 34-06 Task 2 (D-16, carried D-34).
metrics:
  duration: ~75 min (including the 38m56s full suite)
  completed: 2026-09-28
---

# Phase 34 Plan 04: v5.0 renderer over the frozen Phase 28 engine

`scripts/phase34_report.py` subclasses phase28's `Bindings` and binds it to the three v5.0 records (frontier, admission, ledger), which it reads as bytes with a sha256 each. It renders a lead with one line per leg, states n64 as NOT MEASURED, renders the v4.0→v5.0 condition (c) table directly from the record's rows, and declares a post-hoc contract. `scripts/phase28_report.py` is byte-unchanged. Nothing was installed into docs/REPORT.md or README.md.

## Commit

| Task | Commit | Files |
|------|--------|-------|
| 1–3 (one commit, per plan step 5) | `1eadf11` | scripts/phase34_report.py, scripts/phase34_report.md.tmpl, scripts/phase34_glance.md.tmpl, tests/test_phase34_report.py |

## Rendered title line

```
## v5.0 — admission MOOT: advr n8 PASS 0 of 6, INCONCLUSIVE 6 of 6; advr n64 REFUSED 6 of 6 (recorded 2026-09-28)
```
Anchor (`derived.report_anchor`): `v50--admission-moot-advr-n8-pass-0-of-6-inconclusive-6-of-6-advr-n64-refused-6-of-6-recorded-2026-09-28`

Lead as rendered:
```
- `advr_n8`: PASS 0 of 6, INCONCLUSIVE 6 of 6.
- `advr_n64`: REFUSED 6 of 6 — NOT MEASURED: refused under `refused_prereg03` (`verdicts.leg_refusals.advr_n64`, quoted below).
```
It is followed by "Admission: `MOOT`." and the three reasons, quoted verbatim.

## Numeral scan: natural RED, then GREEN

The first draft of `scripts/phase34_report.md.tmpl` typed D-04/D-05's own wording. `_bare_numerals` printed:
```
[(3, '- `advr_n8`: 0 of 6 PASS, all 6 INCONCLUSIVE.'), (4, '- `advr_n64`: 6 of 6 REFUSED — NOT MEASURED.'), (8, '### advr_n64 — not measured'), (10, 'Its own control: unlearnable true, taught [0, 1008], heldout [1, 648].')]
```
The first bound draft still had one hit: line 29 typed `verdicts.condition_c_vs_v4.rows` in prose, and the `4` in the name is a bare numeral. I reworded that line. Final result for both templates: `[('scripts/phase34_report.md.tmpl', []), ('scripts/phase34_glance.md.tmpl', [])]`.

In-test RED evidence, `test_template_scan_typed_count_is_red`: appending `- the first leg: 0 of 6 PASS, all 6 INCONCLUSIVE.` to the real template gave `[(72, '- the first leg: 0 of 6 PASS, all 6 INCONCLUSIVE.')]`. That is exactly one hit, on the appended line.

## Contract RED evidence

`test_dropping_a_contract_binding_is_red`: with `${table.condition_c_vs_v4}` removed from a tmp copy of the template, `_uncovered` returned `['frontier.verdicts.condition_c_vs_v4.rows']`.

## Pre-publish `check` output

```
$ .venv/bin/python scripts/phase34_report.py check
[phase34_report] docs/REPORT.md: PHASE34-REPORT sentinels absent (pre-publish state)
[phase34_report] README.md: PHASE34-GLANCE sentinels absent (pre-publish state)
exit 1
$ .venv/bin/python scripts/phase28_report.py check
exit 0
```

## KeyError check (Task 1 acceptance)

A single `python -c` over `Bindings(load())` gave:
- `KeyError frontier.nonexistent 'nonexistent'`
- `KeyError quote.anything 'quote.anything'`
- `KeyError derived.leg_label.advr_n9 'advr_n9'`
- `KeyError const.x 'const.x'`

`'torch' in sys.modules` was `False`. The committed test `test_unknown_prefix_never_reaches_the_v4_dispatch` repeats this check.

## Gates

- `tests/test_phase34_report.py`: **19 passed**. These are the 18 named tests plus `test_unknown_prefix_never_reaches_the_v4_dispatch`.
- Quick run plus census (test_phase34_ledger, test_package, test_phase28_report/_ledger/_prereg, test_phase25_correction, test_phase15_docs, test_phase18_docs, the accountant and dp-control AST guards, test_phase21_sc5, the os.replace census, test_resume_from_none_is_inert): **118 passed**.
- Plan verify on the committed tree: **70 passed**, then `phase28_report.py check` gave 0. `git diff --quiet HEAD -- scripts/phase28_report.py docs/REPORT.md README.md` passed and scripts/ and tests/ were clean. It printed `VERIFY-OK`.
- `make lint`: `All checks passed!` and `310 files already formatted`.
- Both renders have zero `\b0(\.0+)?%` matches. The glance has no `![`, no `## ` and none of 0.3483 / 8.52417066884246 / 3.229.
- **Full suite**, detached on committed tree `1eadf11`: `3299 passed, 4 skipped, 83 warnings in 2336.83s (0:38:56)`, `EXIT=0`. That is 3280 + 19 new, 0 failed.

## Deviations from Plan

1. **[Rule 1 - Bug] CONTRACT granularity for condition_c_vs_v4.** If the contract path were `frontier.verdicts.condition_c_vs_v4`, `${frontier.verdicts.condition_c_vs_v4.statement}`/`.notes` placeholders and `table.condition_c_by_leg` would still cover it. Dropping `${table.condition_c_vs_v4}` would then stay green, which is the false-green the plan's behavior bullet forbids. So CONTRACT lists `.rows`, `.by_leg`, `.notes` and `.statement` separately. `test_every_contract_path_resolves_and_is_bound` requires each of D-08's minimum paths to be a CONTRACT path or a parent of one.
2. **[Rule 1 - Bug] `ledger_by_reference_count`.** The ledger's non-v5.0 rows are 3 × v4.0 and 2 × v3.0, all `P28-*` ids carried by reference. Counting `milestone == "v4.0"` would have published 3, not 5. It now counts `milestone != "v5.0"`, and the template calls these "earlier-milestone rows carried by reference".
3. **Parametrized derived names.** `derived.leg_label.<leg>`, `derived.leg_total.<leg>` and `derived.recall.<leg>.<tier>` live in a `DERIVED_BY_ARG` dict next to `DERIVED`. An unknown leg raises KeyError.
4. The report template spells "heldout", never "held-out", so the `\bheld\b` prose scan has no carve-out.

## Known Stubs

None. `PUBLISHED = "2026-09-28"` is the D-24 pin; 34-05 sets the publishing day.

## Self-Check: PASSED

- FOUND: scripts/phase34_report.py, scripts/phase34_report.md.tmpl, scripts/phase34_glance.md.tmpl, tests/test_phase34_report.py
- FOUND: commit 1eadf11
- STATE.md / ROADMAP.md / REQUIREMENTS.md / docs/REPORT.md / README.md: not modified. No gsd-sdk mutation handler was called.
