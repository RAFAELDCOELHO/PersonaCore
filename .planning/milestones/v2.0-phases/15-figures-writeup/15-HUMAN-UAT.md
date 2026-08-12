---
status: complete
phase: 15-figures-writeup
source: [15-VERIFICATION.md]
started: 2026-08-02T21:17:31Z
updated: 2026-08-12T00:00:00Z
---

## Current Test

[none — session complete 2026-08-12, both tests passed, no gaps opened]

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

result: pass — human confirmed both disclosure lines are legible inline on rendered GitHub at default
desktop width, no click-through needed. The `why_human` concern does not reproduce: it estimated
"~3pt equivalent" from the 0.391 downscale of the nominal 8pt text, which conflates point size with
rendered pixel density — the PNG is drawn at high DPI, so 880px still carries enough pixels, and
Retina renders it at 2x. Corroborated before asking: a Lanczos resample of `phase15_fisher_ewc.png`
(2250x750 -> 880x293) reproduced the VIZ-03 line readably ("the naive and EWC panels share ONE log
scale ... the Fisher panel has its own because its units differ ..."). VIZ-02 (0.772) was never at
risk. No `figsize`/`fontsize` bump needed; figures ship as generated.

### 2. Two-halves narrative independence in `docs/REPORT.md`

expected: Read lines 664-831 (`## Milestone 2 Results` through `### What Remains Uncertain`) end to
end without reading any `## Decision:` section. Then read the seven v2.0 `## Decision:` sections
(lines 490-663) without the results narrative. Each half should read as a complete story; neither
should be the other's summary, and neither should leave a forward reference the reader must resolve
in the other half.

why_human: 15-05's must-have is a reading-experience property. The structural precondition is
verified — the halves are disjoint line ranges and the report asserts the property at lines 486-488
— but "follows as a complete story" is prose judgment no grep can settle.

result: pass — human read both halves and confirmed each stands as a complete story. Corroborated by
a full read of both ranges before asking: the results half (664-831) opens with its own "claim under
test" framing and carries the four experiments, the two figures, the correlation and its bounds
without needing a Decision section; its one cross-reference (`:671`, "every choice behind them is
justified in its own `## Decision:` section above; none of that reasoning is repeated here") is an
explicit pointer, not a dependency, and the forward reference at `:829-831` points at Limitations, a
third section, not the other half. The Decisions half (490-663) is Choice / Rationale /
Alternative-rejected throughout, each complete on its own terms. One borderline spot was surfaced to
the human rather than silently passed: `:594-597` names Phase 12's lambda-sweep verdict and the later
production lambda=0.01 choice without stating what the verdict said (that lives at `:673-682`). Judged
acceptable because the decision being argued is the *rule* — never edit a recorded verdict in place —
which is fully argued without the verdict's content. No REPORT.md change needed.

## Summary

total: 2
passed: 2
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

None. Both tests passed on first presentation and neither opened a gap, so no fix plan was needed.

Both `why_human` predictions were tested rather than assumed, and one of them was wrong in the safe
direction: test 1's "roughly 3pt equivalent … likely unreadable" concern did not reproduce, because
it reasoned from nominal point size rather than rendered pixel density. The figures ship unchanged —
no `figsize`/`fontsize` bump, no regeneration, and no claim change in `docs/REPORT.md`.
