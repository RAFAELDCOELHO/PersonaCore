---
status: partial
phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
source: [24-VERIFICATION.md]
started: 2026-08-30T19:23:45Z
updated: 2026-08-30T21:10:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Give ADVT-01 an owning phase in ROADMAP.md  [RESOLVED]
expected: ADVT-01 has a phase that formally claims it. Today REQUIREMENTS.md:476 maps it to
Phase 24; Phase 24's own `**Requirements**` line (ROADMAP.md:718) claims it and its traceability
row correctly declares it unsatisfiable ("no adapter has been trained"). Phase 25 — which actually
does the work, per its SC2 "intensity for adversarial ... swept to the never-taught floor" — does
NOT list it: ROADMAP.md:814 reads `CTRL-01, CTRL-02, FRONT-01, FRONT-02, FRONT-03, FRONT-04`.
Verified by the orchestrator: `grep -n "ADVT-01" .planning/ROADMAP.md` returns hits only inside
Phase 24's block (718, 723, 785, 807). The requirement is currently unownable by the process.
Suggested fix: append `, ADVT-01` to ROADMAP.md:814.
RESOLVED 2026-08-30 at commit e5a2474 — ROADMAP.md:814 now carries ADVT-01, and the resulting
two-phase span (24 builds, 25 satisfies) is recorded as a dated additive amendment under
REQUIREMENTS.md's Traceability heading rather than by editing the dated 2026-08-20 count.
why_human: Editing the roadmap's requirement mapping is a planning decision. The verifier can
observe the hole but must not silently reassign a requirement.
result: resolved (developer decision 2026-08-30; commit e5a2474)

### 2. Decide ADVT-02's ticked wording vs the actual mechanism
expected: The requirement prose says A2 "is REFUSED at the episode builder, not dropped". The
mechanism is filter-then-refuse: A2 rows are excluded by the list comprehension at
scripts/phase24_adversarial.py:289-292 (`row["family"] in TRAINED_FAMILIES`), and the SystemExit
at :300 is explicitly belt-and-braces behind it — the code's own comment reads "BELT AND BRACES
beside the filter above, not instead of it" — firing only if the filter widens. The operative
property (A2 never trains) holds doubly and is verified. Question is whether the ticked prose
should read "filtered out AND refused behind the filter".
why_human: Editorial call on the wording of an already-ticked requirement.
result: [pending]

### 3. Confirm 24-04's instrumentation is intended for Phase 25 consumption
expected: `contains_refusal` / `score_refusal` / `clean_frame_probe_populations` in
scripts/phase14_recall.py are called by Phase 25's sweep driver. Today they are exercised only by
tests/test_phase24_refusal_rate.py — verified correct in isolation (112 vs 112 distinct,
budget-matched, disjoint, 0 of 10 published values across 224 questions) but consumed by no running
pipeline. No ROADMAP SC required them wired during Phase 24, so this is not a gap against the
contract.
why_human: An unconsumed instrument is how a planned measurement quietly never gets taken.
result: [pending]

### 4. Decide how to close the stale provenance pins in results/phase24_token_budget.json  [RESOLVED]
expected: `provenance.module_sha256` matches the live modules, and drift is caught by a test.
Measured 2026-08-30 at HEAD: 2 of 4 pins are STALE — `scripts/phase24_adversarial.py`
(recorded 8f884fd7… / live b679c6f6…) and `scripts/teach_persona.py` (recorded e2709e54… /
live 82da6c3a…). Both drifted because plan 24-08's blocker fixes edited those modules AFTER the
record was emitted. The committed NUMBERS are unaffected — re-verification re-derived every figure
and all 12 cross-sums intact — and the emitter's docstring declares a non-matching digest to be the
designed visible signal.
The defect is that the signal is INVISIBLE: `grep -rn "module_sha256" tests/` returns nothing, while
`corpus_sha256` IS checked against live at tests/test_phase24_record.py:274. So the suite stays
green while the pin drifts — the green-but-blind mode this project names as its most recurring
defect, and which .github/workflows/ci.yml's own comment calls out by name.
Two candidate closures: (a) add a guard asserting module_sha256 == live AND re-emit the record so
the pins are true again (the numbers should be byte-identical; re-verification proved they are
unaffected), or (b) keep the pins as a historical "produced by these module versions" record and
add a guard asserting drift is DECLARED rather than absent.
why_human: This changes a committed result artifact's provenance semantics. (a) and (b) mean
different things about what the pin promises.
RESOLVED 2026-08-30 by plan 24-09 — closure (a), developer decision. The guard landed first and was
watched RED against the REAL drift (`46f07d5`, disclosed one-commit RED window): *"2 of 5 provenance
digests no longer match the files on disk"*, naming both modules with recorded and live in full. The
record was then re-emitted through the emitter's own sanctioned route — the write-once refusal's
"Delete … to re-run", which `_PUBLICATION_PATHSPEC`'s record exclusion exists to make reachable —
and all four pins now match live (`aaea029`). **Every substantive figure came out byte-identical,
proved three ways** and not eyeballed: remainder sha256 `739658923d00…` on both sides after
excluding only `module_sha256` / `git_sha` / `written_utc`; a recursive walk over 529 leaf scalars
(317 numeric) differing in 0; `git diff` = 4 lines, all inside `provenance`. The guard covers
`tokenizer_sha256` too — it was unguarded for the same reason and is one line.
CORRECTION to this item's own reasoning, measured rather than assumed: 24-VERIFICATION's reason 4
("re-emitting is blocked anyway: `refuse_if_dirty` counts untracked files as dirty and the tree
carries `M .gitignore` and `?? .planning/todos/`") is FALSE. `_PUBLICATION_PATHSPEC` is
`(scripts, src, results, artifacts, :(exclude)<record>)` — 24-07 deliberately narrowed it from `.`
for exactly these two paths — so
`git status --porcelain -- scripts src results artifacts ':(exclude)results/phase24_token_budget.json'`
was EMPTY and the guard never fired. Nothing was blocked; the option was open all along.
result: resolved (developer decision 2026-08-30, closure (a); commits 46f07d5, aaea029)

## Summary

total: 4
passed: 2
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
