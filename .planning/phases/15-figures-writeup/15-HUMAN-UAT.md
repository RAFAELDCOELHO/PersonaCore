---
status: partial
phase: 15-figures-writeup
source: [15-VERIFICATION.md]
started: 2026-08-02T21:17:31Z
updated: 2026-08-02T21:17:31Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. GitHub inline legibility of the two v2.0 figures

expected: Open `README.md` on GitHub (rendered, not raw) at default desktop width and read the gray
disclosure line at the bottom of each embedded figure *without* clicking through to full size. Both
lines should be legible in place — VIZ-03's "the naive and EWC panels share ONE log scale … the
Fisher panel has its own because its units differ", and VIZ-02's "… so this figure is NOT comparable
to the VIZ-03 delta panels".

why_human: `results/phase15_fisher_ewc.png` is 2250×750; GitHub's ~880px content column downscales
it by 0.391, rendering the 8pt disclosure text at roughly 3pt equivalent. D-04's whole purpose is
that the PNG cannot be misread when it travels alone — whether that survives inline downscale is a
rendering/perception question the filesystem cannot answer. (VIZ-02 downscales by 0.772, ~6.2pt
equivalent — likely fine.) If VIZ-03's line is unreadable inline, the fix is a `figsize`/`fontsize`
bump and a figure regeneration, not a claim change.

result: [pending]

### 2. Two-halves narrative independence in `docs/REPORT.md`

expected: Read lines 664-831 (`## Milestone 2 Results` through `### What Remains Uncertain`) end to
end without reading any `## Decision:` section. Then read the seven v2.0 `## Decision:` sections
(lines 490-663) without the results narrative. Each half should read as a complete story; neither
should be the other's summary, and neither should leave a forward reference the reader must resolve
in the other half.

why_human: 15-05's must-have is a reading-experience property. The structural precondition is
verified — the halves are disjoint line ranges and the report asserts the property at lines 486-488
— but "follows as a complete story" is prose judgment no grep can settle.

result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
