# Phase 34: v5.0 Report and Milestone Close - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-28
**Phase:** 34-v5-0-report-and-milestone-close
**Areas discussed:** v5.0 section content, Renderer + sentinels, RPT-05 vs missing v5.0 tag, Ledger + close boundary; then (explore more) ledger census, 33-REVIEW WR-01/02, ship block

---

## Area selection — developer's stated positions (free text)

The developer selected all four areas and stated positions before seeing any options:
1. A new module, phase34_report.py, that imports phase28_report's engine without editing the frozen file.
2. The same verdict-then-mechanism order as Phase 28, with n8 and n64 as distinct findings, citing `condition_c_vs_v4` instead of rebuilding it in prose.
3. The tension between "the test runs today without a v5.0 tag" and RPT-03's discipline (anchor on a fixed tag, not a moving HEAD) needs explicit resolution, not a presumed one.
4. The ledger as an extension of phase28_ledger.json with a milestone column, but the tension with the new-module decision in (1) must be resolved (data may not carry the same risk as code).

**Premises measured before accepting:**
- (1) TRUE. The engine is importable, but `Bindings` dispatches on phase28's module-level dicts, so it must be subclassed or re-parametrized.
- (2) TRUE. `verdicts.condition_c_vs_v4` exists, with `by_leg` and `rows`.
- (4) FALSE as stated. The frozen v4.0 block embeds the phase28 ledger rows digest `bb9f82fe…` in `docs/REPORT.md`, and it renders the register, withheld claims and counts from all rows unfiltered. Appending rows breaks SC1.
- (3) The tension is real, with precedent: Phase 28 used v1–v3 + HEAD. The current test omits v4.0. MILESTONES.md carries `(Shipped: …)` headings that can serve as a derivation source.

## RPT-05 tag anchoring

| Option | Description | Selected |
|--------|-------------|----------|
| Required tags derived from MILESTONES | Every "Shipped" milestone's tag is required, and deps are equal across them and HEAD. The v5.0 tag is required automatically once complete-milestone marks v5.0 shipped. | ✓ |
| Pin at the green-CI SHA | The ledger records the CI head, and the test compares deps there and against the v5.0 tag when present. | |
| Both | Maximum coverage, maximum cost. | |

## Ledger form

| Option | Description | Selected |
|--------|-------------|----------|
| New phase34_ledger.json | Same schema; one source per milestone; v4.0 open rows by reference. | ✓ |
| Extend phase28_ledger | Needs a frozen-renderer edit and changes the published digest, breaking SC1. | |

## Lead line

| Option | Description | Selected |
|--------|-------------|----------|
| Per leg + MOOT | One line per leg from `tallies_by_leg`, then admission MOOT with its reasons verbatim. | ✓ |
| admission.reasons verbatim | Faithful, but aggregates the legs. | |

## v4→v5 comparison

| Option | Description | Selected |
|--------|-------------|----------|
| Per-ratio table | Rendered from `condition_c_vs_v4.rows` + `by_leg`, with the record's notes. | ✓ |
| by_leg summary only | Shorter; the reasons are not visible. | |

## Figures

| Option | Description | Selected |
|--------|-------------|----------|
| No figures | No phase32 PNG exists; deferred. | ✓ |
| Generate phase34 plots | New plotter. | |

## Publication contract

| Option | Description | Selected |
|--------|-------------|----------|
| Declared post-hoc contract | A `(field_path, why)` tuple with a resolution test, explicitly NOT a pre-registration. | ✓ |
| Numeral scan + byte-identity only | Omissions go undetected. | |

## Push timing (D-38)

| Option | Description | Selected |
|--------|-------------|----------|
| Two pushes | The first at phase start (75 commits, the Phase 32–33 code never in CI), the second after publishing, whose run is recorded. | ✓ |
| One push after publishing | The 28-07 flow. | |

## Ledger census scope

| Option | Description | Selected |
|--------|-------------|----------|
| All of v5.0 + open v4.0 rows | All carried items from 29–33 + the 6 v4.0 RE-DEFERRED rows by reference. | ✓ |
| Only the 15 staged + 33-REVIEW | Leaves the rest without an owner. | |

## 33-REVIEW WR-01/WR-02

| Option | Description | Selected |
|--------|-------------|----------|
| RE-DEFERRED | The module is pinned in the record (`2041aecc…`, guarded at test_phase33_admission.py:424). Fix with a dated continuation before reuse. | ✓ |
| FIXED + continuation | Touches published evidence for a defect the record did not suffer. | |

## Ship / withheld block

| Option | Description | Selected |
|--------|-------------|----------|
| Rendered from the ledger | The Phase 28 D-13 pattern. | ✓ |
| No ship block | | |

## Claude's Discretion

Template/constant names, the `Bindings` re-parametrization mechanism, section title wording (it must name MOOT + the per-leg outcome), and plan/wave sequencing of the checkpoints.

## Deferred Ideas

- v5.0 frontier plots.
- A README "Repository status" entry (v4.0 is still described as in progress).
