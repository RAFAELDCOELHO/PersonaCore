---
phase: quick-260819-sgh
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - README.md
  - docs/REPORT.md
  - results/phase18_extraction_report.md
autonomous: true
requirements: [ATK-04, ERASE-01, STAT-02, STAT-06]
must_haves:
  truths:
    - "README.md names all five published pin defects by the canonical LETTERS A-E with their line numbers in the closed pin, and states the four-vs-five distinction (A-D block the pin's own `_cmd_report`; E sits in the `erase` subcommand, a path the render never called)"
    - "README's flip gate fires: `grep -cE '\\*\\*E\\*\\*|defect E' README.md` goes 0 -> >=1"
    - "docs/REPORT.md carries a dated section telling the deep-link reader that the Phase 18 exposure table at results/phase18_extraction_report.md:145-154 is a RANK-ONLY reading now scope-limited by the dated continuation at :340-405 of that same file"
    - "docs/REPORT.md's flip gate fires: `grep -c ':340' docs/REPORT.md` goes 0 -> >=1"
    - "docs/REPORT.md:1140-1141 (the outbound pointer) and :1145 (the 'No line above this heading is altered' claim) are BYTE-INTACT, and the new section says in so many words WHY the pointer was not edited in place"
    - "results/phase18_extraction_report.md states the MECHANISM that reconciles item (4) sitting inside the scope limit with LEAKAGE_DEMONSTRATED being exempt: :1636 reads the exposure rank as a presence check only, :1657 decides the verdict on `attack_successes`, i.e. on generation"
    - "That file's flip gate fires: `grep -ci 'null_result_is_admissible' results/phase18_extraction_report.md` goes 3 -> >=4"
    - "All three diffs are PURE INSERTIONS — `git diff --numstat` shows deletions == 0 on every file, and each file's pre-edit bytes are a byte-exact PREFIX of its post-edit bytes"
    - "Nothing is retracted anywhere: the FAILURE verdict, DO NOT SHIP, LEAKAGE_DEMONSTRATED, 92/104, the 0/104 control and every measurement stand exactly as published"
    - "No frozen pin is edited; the suite stays at 845 passed / 1 skipped and ruff stays clean"
  artifacts:
    - path: "README.md"
      provides: "the dated A-E labelling section that retires the four-defect undercount republished at :253-255"
      contains: "**E**"
    - path: "docs/REPORT.md"
      provides: "the dated deep-link redirect scoping the Phase 18 exposure table the pointer at :1140-1141 sends readers to"
      contains: ":340"
    - path: "results/phase18_extraction_report.md"
      provides: "the dated continuation stating the presence-check/generation mechanism behind item (4) vs the verdict"
      contains: "null_result_is_admissible"
  key_links:
    - from: "scripts/_addendum.py::append_addendum"
      to: "results/phase18_extraction_report.md"
      via: "identity marker pair — EXTRACTION_SHIP_RECORDED_LINE passed as BOTH pending and recorded"
      pattern: "append_addendum\\(.*pending=.*recorded=.*\\)"
    - from: "results/phase19_erasure_report.md:564-574"
      to: "README.md"
      via: "the canonical A-E letter table restated on the milestone's most-read surface"
    - from: "results/phase18_extraction_report.md:340-405"
      to: "docs/REPORT.md"
      via: "the appended redirect naming the continuation the outbound pointer cannot reach"
---

<objective>
Close the three open audit warnings — **W2** (README republishes the retired four-defect
undercount), **B1-a** (the deep-link reader `docs/REPORT.md` creates never reaches B1's scope limit)
and **B1-b** (B1's exemption is asserted, never shown) — as **dated continuations**. Every fix is
additive; no published dated text is edited in place anywhere.

Purpose: each warning is the same defect class the milestone already raised once — a published
statement its own source has since superseded, left standing on a surface a reader actually reads.
W2 undercounts a phase's own defects on the front page. B1-a leaves the reader who follows
`docs/REPORT.md`'s outbound link landing 190 lines above the limit that scopes what they are about
to read. B1-b leaves the skeptic's strongest objection — "item (4) gates the verdict, so how is the
verdict exempt?" — flagged and unanswered, when the answer exists in the code and was measured.

Output: one appended dated section in each of three published files. Zero deletions in all three.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@scripts/_addendum.py
@.planning/v3.0-MILESTONE-AUDIT.md

Read before drafting:

- `results/phase19_erasure_report.md:552-601` — the canonical A-E letter table and the paragraph
  that states the four/five distinction. This is the SOURCE for Task 1; restate it, do not reinvent
  it, and keep its letters and line numbers exactly.
- `results/phase18_extraction_report.md:340-405` — the existing dated continuation. Its register is
  the register all three new sections match: a `## Dated continuation — YYYY-MM-DD: <subject>`
  heading (or that file's / that document's own heading style), an italic opener stating that
  nothing above the heading is altered and naming the guard that proves it, then the substance.
  Note especially `:379-381`, which flags the item-(4) tension Task 3 resolves.
- `docs/REPORT.md:1136-1146` — the outbound pointer and, four lines below it, the sentence that
  makes editing the pointer impossible.

## Measured already — do NOT re-derive, do NOT contradict

Plans in this repo have repeatedly named paths and APIs the code refuses. Everything below was
measured this session at `07391cd` with a clean tree.

**The writer.** `scripts/_addendum.py:56` — `append_addendum(path, addendum, *, pending, recorded)`.
BOTH kwargs are REQUIRED keywords. In `results/phase18_extraction_report.md` (405 lines):
`EXTRACTION_SHIP_PENDING_LINE` occurs **0** times, `EXTRACTION_SHIP_RECORDED_LINE` occurs **1**
time. The writer refuses at `found != 1`, so the ONLY legal call against this file is the IDENTITY
pair `pending=recorded=EXTRACTION_SHIP_RECORDED_LINE` — which makes the replacement a provable
no-op and the write a pure append. Both constants live in `scripts/phase18_extraction.py:3795` and
`:3797`; IMPORT them, never retype the literals. This exact call already succeeded once, at commit
`7af6006`. It is a proven path, not a guess.

**B1-a cannot be done the way the audit words it.** The audit's suggested fix is "point
`docs/REPORT.md:1140-1141` at the continuation as well as the table". `docs/REPORT.md:1145` asserts
verbatim: *"Appended additively. No line above this heading is altered, and the section above —
Phase 18's extraction audit result — is carried through byte-identically."* The pointer sits FOUR
LINES ABOVE that sentence and INSIDE the section it names. An in-place edit would falsify a
published claim two lines below itself. B1-a therefore ships **additively**, as a new dated `## `
section at the END of `docs/REPORT.md`. `:1140-1141` stays byte-intact, deliberately, and the new
section says so.

**The canonical labels** (`results/phase19_erasure_report.md:564-574`):

| label | defect | line in the CLOSED pin |
| --- | --- | --- |
| A | `zero_results_have_nll` compares an ORDERED tuple against records serialised with `sort_keys=True` — reads False on key order alone while every NLL is present | `:1562` vs `:2948` |
| B | `_calibration_rate()` reads `record["pre_erasure"]["per_fact"]`, i.e. Phase 18's candidate recall, not the calibration arm's own rate | `:3850-3855` |
| C | `rows.update(per_fact_rows(...))` lets one (b) tier overwrite the other; the pinned `report` subcommand SystemExits on the resulting rows | `:2922` |
| D | `_cmd_report` passes `retention_perplexity`'s `[ppl, n]` pair into the gate's scalar `retention_ppl=`, where the comparison raises `TypeError` | `:3811` |
| E | `_selected_components` reads the TARGET's stopping rule on the calibration twin's 6 members while reading every BYSTANDER on 8, inside one call | `:3576` |

A-D are the four that block the pin's own `_cmd_report`. **E** sits in the `erase` subcommand — a
path that render never called — which is why it is not one of the four ways the pinned report path
fails, and why the phase nonetheless publishes **five**. E is published in
`results/phase19_reference_set_correction.md`.

**The W2 defect site.** `README.md:253-255` reads "...on a hand-driven path around **four published
defects** in that pin" and "**all four defects** with their dated corrections stand exactly as
published". README carries **0** mentions of any letter label and — unlike
`results/phase19_erasure_report.md:576-584`, which grants itself an in-file exemption — carries no
exemption, so the phrase reads as a complete enumeration of published defects. It is not.

**B1-b's mechanism, confirmed in `scripts/phase18_extraction.py` this session:**

- `:1636` — `if zero_cells[key]["successes"] == 0 and zero_cells[key]["exposure_rank"] is None`.
  Condition (4) reads exposure as a PRESENCE check only. The rank's VALUE is never read.
- `:1657` — `return (LEAKAGE_DEMONSTRATED if attack_successes > 0 else NULL_ADMISSIBLE), reasons`.
  The terminal ternary decides on GENERATION. Every path to `INCONCLUSIVE` has returned above it.

So the exemption is TRUE, and this is why: item (4) gates ADMISSIBILITY on whether a rank exists,
never on what it says, and the verdict itself is chosen by a generation count.

## Guards that constrain this work — already read, do not re-derive

- `tests/test_phase18_docs.py::test_docs_continuation_is_additive` asserts `## ` heading PREFIX
  EQUALITY for `README.md` (7 baseline entries) and `docs/REPORT.md` (31). A NEW `## ` heading
  appended at the END of either file is legal and lands after the baseline prefix.
- `tests/test_phase18_docs.py::test_claim_sentence_is_verbatim_in_three_surfaces` requires
  `TOGGLE_IS_AVAILABILITY` verbatim and INSIDE README's `## Claim correction` section. Appending at
  EOF does not move it. Do not start a new heading with `## Claim correction`.
- `tests/test_phase18_docs.py::test_no_bare_zero_percent_in_docs` scans README and docs/REPORT.md
  for `\b0(\.0+)?%`. Baseline is 0 in all three files. STAT-02: never publish a bare `0%` — `0/104`
  and `0/27` are fine, `0%` and `0.00%` are not.
- `tests/test_phase15_docs.py::test_headline_numbers_match_sources` splits README on `\n(?=- )` and
  asserts EXACTLY ONE bullet carries each of `0.3483`, `8.52417066884246`, `3.229`. The last chunk
  runs to EOF, so an appended section carrying any of those three strings turns a `== 1` into a
  `== 2`. **Do not write those three numbers into README.**
- `tests/test_phase18_docs.py::test_extraction_report_addendum_is_additive` derives the pre-append
  revision from git, asserts the byte prefix up to the placeholder, asserts `pending` count 0 and
  `recorded` count 1, and asserts the `## Verdict` block byte-identical with `LEAKAGE_DEMONSTRATED`
  still in it. A second identity-pair append keeps all four true.

## Hard prohibitions

- Do NOT edit any frozen pin: `scripts/phase18_extraction.py`, `scripts/phase19_erasure.py`,
  `scripts/erasure_gate.py`, `scripts/phase19_floor.py`, `scripts/phase17_isolation.py`. Editing one
  reddens `tests/test_phase16_prereg.py` permanently.
- Do NOT call `render_report` on the Phase 18 report — it rewrites the whole file.
- Do NOT touch `.planning/ROADMAP.md` or `.planning/STATE.md`.
- No new runtime dependencies. No new file under `scripts/` — the Task 3 driver is a throwaway in
  the scratchpad, as at `7af6006`.
- Use `.venv/bin/python` / `.venv/bin/pytest` / `.venv/bin/ruff`. Baseline: `07391cd`, clean tree,
  845 passed / 1 skipped, ruff clean.
</context>

<tasks>

<task type="auto">
  <name>Task 1: W2 — append README's A-E labelling section</name>
  <files>README.md</files>
  <action>
Append ONE new dated `## ` section at the very END of `README.md`. Change no existing byte.

Heading: sentence case, dated, and NOT prefixed `## Claim correction` — e.g.
`## Pin defect labels — the phase publishes five, A through E (recorded 2026-08-19)`.

The section must:

1. Open in README's own established register — the two sections above both open with
   `**Appended, not edited.**` and a sentence stating that no line above was changed. Match that,
   and state that this is a LABELLING correction that retracts nothing.
2. Carry the five defects by LETTER with their line numbers in the closed pin, sourced from
   `results/phase19_erasure_report.md:564-574` — A (`:1562` vs `:2948`), B (`:3850-3855`),
   C (`:2922`), D (`:3811`), E (`:3576`). A markdown table or a bulleted list is fine. The literal
   `**E**` must appear (it is the flip gate). Name
   `results/phase19_reference_set_correction.md` as where E is published.
3. State the four-vs-five distinction explicitly, in one paragraph: A, B, C and D are the four
   independent ways the pin's own `_cmd_report` cannot reproduce the verdict, which is what the
   ship decision enumerates; **E** sits in the `erase` subcommand — a path that render never called
   — so it cannot be one of the four ways the pinned report path fails, and the phase nonetheless
   publishes five.
4. Record plainly that the phrasing in the section above — "four published defects" and "all four
   defects ... stand exactly as published" at `README.md:253-255` — is correct about the four
   `_cmd_report` failures and UNDERCOUNTS the phase when read as a complete enumeration of
   published defects, which is how it reads here because README grants itself no in-file exemption.
   Say that the earlier phrasing is left standing rather than edited, per this project's
   dated-continuation discipline.
5. Close by confirming nothing moves: the verdict of record is still `FAILURE`, the ship decision
   is still `DO NOT SHIP`, no defect is added or withdrawn and no measurement changes.

Forbidden in this section: the strings `0.3483`, `8.52417066884246` and `3.229` (they would break
the phase-15 one-bullet guard), and any bare `0%` / `0.00%` (STAT-02).
  </action>
  <verify>
    <automated>test "$(git diff --numstat -- README.md | cut -f2)" = "0" && test "$(git diff --numstat -- README.md | cut -f1)" -gt 0 && cmp <(git show 07391cd:README.md) <(head -c "$(git show 07391cd:README.md | wc -c)" README.md) && test "$(grep -cE '\*\*E\*\*|defect E' README.md)" -ge 1 && test "$(grep -cE '\b0(\.0+)?%' README.md)" = "0" && .venv/bin/python -m pytest -q tests/test_phase18_docs.py tests/test_phase15_docs.py</automated>
  </verify>
  <done>
`git diff --numstat -- README.md` shows insertions > 0 and deletions == 0; the pre-edit README is a
byte-exact prefix of the new one; `grep -cE '\*\*E\*\*|defect E' README.md` has flipped 0 -> >=1;
no bare zero percentage; `tests/test_phase18_docs.py` and `tests/test_phase15_docs.py` both green.
  </done>
</task>

<task type="auto">
  <name>Task 2: B1-a — append the deep-link redirect to docs/REPORT.md</name>
  <files>docs/REPORT.md</files>
  <action>
Append ONE new dated `## ` section at the very END of `docs/REPORT.md`. Change no existing byte —
above all not `:1140-1141` (the outbound pointer) and not `:1145` (the claim that no line above it
is altered).

Heading: Title Case, matching this document's style, dated — e.g.
`## Deep-Link Correction: The Phase 18 Exposure Table Is a Rank-Only Reading, Now Scope-Limited (recorded 2026-08-19)`.

The section must:

1. Open with the italic additive note this document uses (`*Appended additively. No line above this
   heading is altered...*`), in the register of the opener at `:1145-1146`.
2. Name the deep link it is correcting: the outbound pointer earlier in this document sends the
   reader to `results/phase18_extraction_report.md` specifically for "the exposure table with all
   three frames and both reductions". That table is at
   `results/phase18_extraction_report.md:145-154`, 190 lines ABOVE the dated continuation that
   scopes it, and it carries no forward pointer to it.
3. State what the table is: every one of its eight slots reads rank 1, and it is a RANK-AND-EXPOSURE
   reading with no generation number beside it — exactly the class of reading Phase 19's
   retroactive scope limit reaches.
4. Send the reader to the limit BY LINE: the dated continuation at
   `results/phase18_extraction_report.md:340-405` (the literal `:340` must appear — it is the flip
   gate), and note that the same continuation names the 73 measured zero-cells behind admissibility
   item (4) at `:236` of that file as sitting INSIDE the limit rather than in its exemption.
5. State WHY the pointer above was not edited in place, plainly: the section immediately below it
   asserts that no line above its heading is altered and that Phase 18's extraction-audit section is
   carried through byte-identically. The pointer sits four lines above that sentence and inside the
   section it names, so editing it would falsify a published claim two lines below itself. The
   redirect is therefore published here, and `docs/REPORT.md:1140-1141` is left byte-intact
   deliberately.
6. Close on what is NOT affected, so this cannot read as a retraction: every Phase 18 reading that
   rests on GENERATION stands — the ASR ladder, 92 of 104 `core_held_out` questions on the best
   family, the adapter-off control at 0/104 at identical budget, the ATK-03 positive control, the
   `LEAKAGE_DEMONSTRATED` verdict and the `(92, 104, 0, 104)` handoff. Nothing above is withdrawn,
   qualified or narrowed.

Forbidden: any bare `0%` / `0.00%` (STAT-02). `0/104` is the correct form.
  </action>
  <verify>
    <automated>test "$(git diff --numstat -- docs/REPORT.md | cut -f2)" = "0" && test "$(git diff --numstat -- docs/REPORT.md | cut -f1)" -gt 0 && cmp <(git show 07391cd:docs/REPORT.md) <(head -c "$(git show 07391cd:docs/REPORT.md | wc -c)" docs/REPORT.md) && cmp <(git show 07391cd:docs/REPORT.md | sed -n '1140,1141p;1145p') <(sed -n '1140,1141p;1145p' docs/REPORT.md) && test "$(grep -c ':340' docs/REPORT.md)" -ge 1 && test "$(grep -cE '\b0(\.0+)?%' docs/REPORT.md)" = "0" && .venv/bin/python -m pytest -q tests/test_phase18_docs.py tests/test_phase15_docs.py</automated>
  </verify>
  <done>
`git diff --numstat -- docs/REPORT.md` shows insertions > 0 and deletions == 0; the pre-edit file is
a byte-exact prefix of the new one; lines 1140, 1141 and 1145 compare byte-identical against
`07391cd`; `grep -c ':340' docs/REPORT.md` has flipped 0 -> >=1; no bare zero percentage; both doc
test files green.
  </done>
</task>

<task type="auto">
  <name>Task 3: B1-b — append the mechanism continuation to the Phase 18 report</name>
  <files>results/phase18_extraction_report.md</files>
  <action>
Append ONE dated continuation to `results/phase18_extraction_report.md` through
`scripts/_addendum.append_addendum`, under the IDENTITY marker pair. No other write path.

**How to drive it.** Write a throwaway driver in the scratchpad (NOT under `scripts/`, matching
`7af6006`) that:

- loads `scripts/phase18_extraction.py` by path with `importlib.util.spec_from_file_location`
  (`scripts/` is not an importable package — copy the shape of `tests/test_phase18_docs.py::_load`)
  and reads `EXTRACTION_SHIP_RECORDED_LINE` off it. Never retype the literal.
- imports `scripts/_addendum.py` the same way and calls
  `append_addendum(path, addendum, pending=RECORDED, recorded=RECORDED)` — the identity pair. This
  is the only legal call: PENDING is already consumed at 0 occurrences, so any other `pending`
  makes the writer SystemExit at `found == 0`.
- runs under `.venv/bin/python`.

**What the continuation must say.** Heading in this file's established form —
`## Dated continuation — 2026-08-19: <subject>` — e.g. *"why item (4) sits inside the scope limit
while the verdict does not"*.

1. Italic opener in the register of the continuation at `:342-347`: appended below the rendered
   report, nothing above the heading altered, written through
   `scripts/_addendum.append_addendum` under the identity marker pair, and guarded by
   `tests/test_phase18_docs.py::test_extraction_report_addendum_is_additive`.
2. Name what it resolves: the 2026-08-19 continuation above (`:374-381`) states that the 73
   zero-cells behind item (4) sit INSIDE the scope limit and that `LEAKAGE_DEMONSTRATED` is exempt,
   and it flags that tension without resolving it. The skeptic's objection is "item (4) gates the
   verdict, so how is the verdict exempt?" This section answers it from the code.
3. State the mechanism with BOTH line numbers cited:
   - `scripts/phase18_extraction.py:1636` — the item-(4) condition is
     `zero_cells[key]["successes"] == 0 and zero_cells[key]["exposure_rank"] is None`. Exposure
     enters as a PRESENCE check and nothing else: item (4) asserts that every measured-zero cell
     CARRIES a rank, and never reads what that rank says. A wrong rank VALUE cannot move this
     condition, because no branch in `null_result_is_admissible` reads the value.
   - `scripts/phase18_extraction.py:1657` — the terminal ternary is
     `return (LEAKAGE_DEMONSTRATED if attack_successes > 0 else NULL_ADMISSIBLE), reasons`. The
     verdict is chosen by a GENERATION count, and every path to `INCONCLUSIVE` has already returned
     above it.
4. Draw the conclusion both ways round, because that is the whole point: item (4) is INSIDE the
   limit as a published READING — 73 cells whose only discriminating evidence is a rank standing
   alone — and the VERDICT it gates is nonetheless EXEMPT, because the gate consumes item (4) as a
   completeness precondition (does a rank exist for every zero cell) rather than as evidence, and
   the value it returns is decided by generation. Both statements are true at once, and the
   presence-check/generation split is what makes them consistent rather than contradictory. State
   the one thing a missing rank WOULD do: send the gate to `INCONCLUSIVE`, never to a different
   admissible verdict.
5. Close on retraction: nothing is withdrawn. The recorded `## Verdict` stands as
   `LEAKAGE_DEMONSTRATED`, the 2026-08-17 ship decision stands as SHIP AS-IS, and the scope limit
   above stands exactly as written — this section adds the mechanism it was missing, and no number
   moves.

The literal `null_result_is_admissible` must appear (flip gate: 3 -> >=4). Forbidden: any bare
`0%` / `0.00%` (STAT-02); `0/27` and `0/104` are the correct forms.
  </action>
  <verify>
    <automated>test "$(git diff --numstat -- results/phase18_extraction_report.md | cut -f2)" = "0" && test "$(git diff --numstat -- results/phase18_extraction_report.md | cut -f1)" -gt 0 && cmp <(git show 07391cd:results/phase18_extraction_report.md) <(head -c "$(git show 07391cd:results/phase18_extraction_report.md | wc -c)" results/phase18_extraction_report.md) && test "$(grep -ci 'null_result_is_admissible' results/phase18_extraction_report.md)" -ge 4 && test "$(grep -c 'Phase 18 ship decision: recorded in the dated continuation' results/phase18_extraction_report.md)" = "1" && test "$(grep -c 'Phase 18 ship decision: not yet recorded' results/phase18_extraction_report.md)" = "0" && test "$(grep -cE '\b0(\.0+)?%' results/phase18_extraction_report.md)" = "0" && .venv/bin/python -m pytest -q tests/test_phase18_docs.py</automated>
  </verify>
  <done>
The append went through `_addendum.append_addendum` under the identity pair; the diff is insertions
only with deletions == 0; the pre-edit file is a byte-exact prefix of the new one; the recorded
ship-decision line is still present exactly once and the pending line still absent;
`grep -ci 'null_result_is_admissible'` has gone 3 -> >=4; no bare zero percentage;
`test_extraction_report_addendum_is_additive` green. No file was added under `scripts/`.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| planner/executor → published dated evidence | Every write in this plan crosses into text that prior commits assert is byte-frozen. This is the only boundary the task touches. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-sgh-01 | Tampering | `README.md`, `docs/REPORT.md`, `results/phase18_extraction_report.md` | mitigate | Every task's `verify` gates on `git diff --numstat` deletions == 0 plus a byte-exact prefix `cmp` against `07391cd`; Task 2 additionally gates lines 1140, 1141 and 1145 individually; Task 3 writes only through `_addendum.append_addendum`, which re-proves the prefix and the unchanged `## Verdict` on the produced bytes. |
| T-sgh-02 | Repudiation | the `## Verdict` / ship-decision blocks in the Phase 18 report | mitigate | Identity marker pair makes the replacement a provable no-op; `recorded` count asserted == 1 and `pending` == 0 post-write; `test_extraction_report_addendum_is_additive` re-derives the pre-append revision from git history in CI. |
| T-sgh-SC | Tampering | package installs | n/a | No installs. Documentation only, no dependency change, `pyproject.toml` untouched. |
</threat_model>

<verification>
Run in order, after all three tasks:

```bash
.venv/bin/python -m pytest -q tests/test_phase18_docs.py
.venv/bin/python -m pytest -q                     # expect 845 passed, 1 skipped
.venv/bin/ruff check . && .venv/bin/ruff format --check .
git diff --numstat                                # every row must end in a 0 deletions column
git status --short                                # only the three target files, plus planning
```

Flip gates, all three must have moved:

```bash
test "$(grep -cE '\*\*E\*\*|defect E' README.md)" -ge 1                                  # was 0
test "$(grep -ci 'null_result_is_admissible' results/phase18_extraction_report.md)" -ge 4 # was 3
test "$(grep -c ':340' docs/REPORT.md)" -ge 1                                             # was 0
```

Byte-prefix gates against the baseline commit, all three files:

```bash
for f in README.md docs/REPORT.md results/phase18_extraction_report.md; do
  cmp <(git show 07391cd:"$f") <(head -c "$(git show 07391cd:"$f" | wc -c)" "$f") || echo "PREFIX BROKEN: $f"
done
cmp <(git show 07391cd:docs/REPORT.md | sed -n '1140,1141p;1145p') <(sed -n '1140,1141p;1145p' docs/REPORT.md)
```

No frozen pin touched:

```bash
git diff --name-only | grep -E 'scripts/(phase18_extraction|phase19_erasure|erasure_gate|phase19_floor|phase17_isolation)\.py' && echo "FROZEN PIN EDITED — revert"
```
</verification>

<success_criteria>
- W2 closed: README names all five pin defects by letter A-E with pin line numbers, states the
  four-vs-five distinction, and records that its earlier "four published defects" phrasing
  undercounts the phase when read as a complete enumeration.
- B1-a closed: `docs/REPORT.md` carries a dated section redirecting the deep-link reader from the
  rank-only exposure table at `results/phase18_extraction_report.md:145-154` to the scope limit at
  `:340-405`, and states why the pointer at `:1140-1141` was deliberately left byte-intact.
- B1-b closed: the Phase 18 report states the presence-check (`:1636`) / generation (`:1657`)
  mechanism that reconciles item (4) sitting inside the limit with the verdict being exempt,
  resolving the tension the previous continuation flagged.
- All three diffs are pure insertions — deletions == 0, pre-edit bytes a byte-exact prefix in every
  file, `docs/REPORT.md:1140-1141` and `:1145` byte-identical to `07391cd`.
- Nothing retracted: `FAILURE`, `DO NOT SHIP`, `LEAKAGE_DEMONSTRATED`, 92/104, 0/104 all stand.
- No frozen pin edited, no file added under `scripts/`, no dependency change.
- Suite 845 passed / 1 skipped; `ruff check` and `ruff format --check` clean.
</success_criteria>

<output>
Create `.planning/quick/260819-sgh-close-w2-b1a-b1b/260819-sgh-SUMMARY.md` when done.
</output>
