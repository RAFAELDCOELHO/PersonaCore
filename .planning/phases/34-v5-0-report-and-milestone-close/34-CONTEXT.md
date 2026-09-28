# Phase 34: v5.0 Report and Milestone Close - Context

**Gathered:** 2026-09-28
**Status:** Ready for planning

<domain>
## Phase Boundary

v5.0 is published as measured. The v5.0 section of `docs/REPORT.md` and the README glance are
rendered from committed records under the numeral scan, and the frozen v4.0 block re-renders
byte-identical (RPT-04). A test proves runtime dependencies identical across every milestone tag,
v5.0's included (RPT-05). The milestone closes only on a green CI run of the developer's push, and
that run id is recorded. Claude never pushes (RPT-06, D-38).

The phase stops at report + ledger + hand ticks of RPT-04..06. `PROJECT.md`, `MILESTONES.md` and the
`v5.0` tag belong to `/gsd-complete-milestone`. This is Phase 28 D-34's boundary, carried unchanged.

</domain>

<decisions>
## Implementation Decisions

**Carried from Phase 28 and binding here without re-litigation:**
- a template with named bindings (D-16);
- byte-identity re-render against the committed records (D-17);
- a numeral scan over the template SOURCE with the strict identifier grammar (D-18/D-19);
- FROZEN AT PUBLISH, with corrections only as dated addenda through `scripts/_addendum.py` (D-20);
- the renderer reads committed records directly and carries a sha256 per source (D-21);
- cross-surface prose goes through `scripts/_prose.py::normalized` (D-22);
- the date stamp is a pinned constant (D-24);
- one ledger per milestone with a closed disposition domain, where `FIXED` requires a test (D-28/D-29);
- the register is the ledger filtered to NAMED-LIMITATION (D-30);
- STATE/ROADMAP/REQUIREMENTS are edited by hand with a snapshot before and a diff of all three
  after, and zero `gsd-sdk` mutation handlers (D-34).

### Area A — Renderer and the frozen v4.0 block (RPT-04, SC1)

- **D-01: A new module `scripts/phase34_report.py` imports phase28_report's engine and never edits
  `scripts/phase28_report.py`.** Measured 2026-09-28: `Bindings`, `render`, `resolve`, `_fmt` and
  `_Template` are importable. `Bindings.__getitem__`, however, dispatches on phase28's module-level
  `RECORDS` / `TABLES` / `DERIVED` / `PATHS` dicts, which are v4.0's. The new module therefore
  subclasses (or re-parametrizes) `Bindings` with its own records, tables and derived values instead
  of calling phase28's as-is.
- **D-02: New sentinels `PHASE34-REPORT` and `PHASE34-GLANCE`.**
  - The report block is appended after `<!-- PHASE28-REPORT-END -->` (`docs/REPORT.md:1609`).
  - The glance block is inserted in `README.md` ABOVE `<!-- PHASE28-GLANCE-BEGIN -->`
    (`README.md:111`), at the top of the "Results at a glance" list, with zero deletions.
  - `python scripts/phase28_report.py check` must stay exit 0 throughout. That is SC1's
    "frozen v4.0 block re-renders byte-identical", tested as it stands and never re-rendered with
    `write`.
- **D-03: Test file naming follows `tests/test_phase34_*.py`.** It needs a byte-identity test of
  both new blocks, a numeral scan of the new template sources (natural RED, per the memory rule),
  and an assertion that the v4.0 `check` still passes.

### Area B — What the v5.0 section publishes (RPT-04)

- **D-04: The verdict comes first, then the mechanism, with n8 and n64 as distinct findings from
  line 1.** The lead has one line per leg, bound to `results/phase32_frontier.json::verdicts.
  tallies_by_leg`:
  - `advr_n8`: 0 of 6 PASS, all 6 INCONCLUSIVE;
  - `advr_n64`: 6 of 6 REFUSED.

  Then comes `results/phase33_admission.json::admission.verdict` (MOOT), with its three `reasons`
  quoted verbatim. No aggregate "0 of 12" headline hides the per-leg split.
- **D-05: n64 is stated as NOT MEASURED, never as "the mitigation held".** Its refusal is quoted
  verbatim from `verdicts.leg_refusals.advr_n64`, and its control's readings are bound to
  `verdicts.control_readings.advr_n64`: `unlearnable: true`, taught `[0, 1008]`, heldout `[1, 648]`.
  This follows Phase 33 D-08's wording discipline.
- **D-06: The v4→v5 comparison is a table rendered from `verdicts.condition_c_vs_v4.rows`.** For
  each ratio it shows the (c) label and `quoted_reasons` for v4 and v5 side by side, plus the
  `by_leg` summary (`tk/tn`, `hk/hn`, `v4_state`/`v5_state`, `k5`/`k6`). It is never reconstructed
  in prose. The record's own `notes` travel with it, covering why the ratio-0 control's dialogue
  half passes by self-reference (D-18) and why `k5` excludes it.
- **D-07: No figures.** No phase32 PNG exists. With 0 PASS and n64 refused, the table carries the
  finding. Generating plots is deferred.
- **D-08: A post-hoc publication contract, declared as NOT a pre-registration.**
  `phase34_report.py` declares a `(field_path, why)` tuple covering at least:
  - `verdicts.tallies_by_leg`, `verdicts.leg_refusals` and `verdicts.control_readings`;
  - `verdicts.condition_c_vs_v4`;
  - `admission.verdict` / `admission.reasons`, `limitation` and `scope` from the phase33 record.

  A test resolves every path against the committed records and requires a binding for each in the
  template. The module's docstring states the contract was written after the results. A late
  pre-registration would be refused by `phase29_prereg`'s ancestry guard and would claim something
  false. No v5.0 `PUBLICATION_OBLIGATION` exists in `phase29_prereg.py` (measured).
- **D-09: The ship / withheld-claims block is rendered from `results/phase34_ledger.json`**, the
  Phase 28 D-13 pattern.
  - Withheld: the NAMED-LIMITATION rows + `leg_refusals` + the admission `reasons`; any claim that
    replay-bearing adversarial training preserves weight-based memory while removing leakage; any
    conclusion at n64.
  - Shipped: the replay-bearing recipe, each leg's own control, and the refusal surface as
    CPU-tested code. Per Phase 33 D-08, the text never says the relearning apparatus was "built and
    never exercised", only that the refusal surface exists.

### Area C — RPT-05 and the tag that does not exist yet

- **D-10: The required tag set is DERIVED from `.planning/MILESTONES.md`, not typed.** The test
  parses the `## vX.Y … (Shipped: …)` headings. It requires every shipped milestone's tag to be
  present and asserts `[project].dependencies` (stdlib `tomllib`) equal across all of them and HEAD.
  - **Today:** MILESTONES lists v1.0–v4.0 as shipped, so the test requires those four tags, and
    HEAD stands in for v5.0. The current test hardcodes `v1.0/v2.0/v3.0` and does not even include
    `v4.0`; that gap closes with this change.
  - **After `/gsd-complete-milestone`:** once it writes "v5.0 … (Shipped: …)", the v5.0 tag is
    required without any hand edit, so the test anchors on a fixed tag, not a moving HEAD. A clone
    missing a required tag goes RED instead of passing vacuously.

  Keep the existing shallow-clone refusal. Test 1 renames or supersedes
  `test_runtime_dependencies_identical_across_four_milestones` (its name would turn false), and the
  `PYPROJECT_SHA256` change detector stays as it is (Phase 28 D-26).
- **D-11: A hand-off obligation on the milestone close, recorded in the ledger and in the phase
  SUMMARY.** From the moment MILESTONES.md says v5.0 shipped, CI needs the `v5.0` tag on origin.
  The developer must push the tag together with main, or the next CI run is RED. This is the
  v2.0/v3.0 "tags never pushed" lesson from 28-07.

### Area D — Ledger (single source per milestone)

- **D-12: A new `results/phase34_ledger.json`, NOT an extension of `results/phase28_ledger.json`.**
  Measured 2026-09-28: the frozen v4.0 block embeds the phase28 ledger's rows digest
  `bb9f82fe290d7578…` literally in `docs/REPORT.md`. It also renders the NAMED-LIMITATION register,
  the withheld claims and the per-disposition counts from ALL rows, with no milestone filter
  (`scripts/phase28_report.py:552-576`). Appending v5.0 rows would therefore break SC1's
  byte-identical re-render. The data is a digested input of the frozen block, so it carries the
  same freeze as code.
  - The new ledger uses the same schema (`id`, `milestone`, `source`, `disposition`, `evidence`,
    `reason`, plus `target`/prerequisite where RE-DEFERRED) and the same closed domain.
  - `close.ci_run` sits outside the rows digest, as in phase28.
  - The path is already under `phase29_prereg`'s ancestry guard (`results/phase34_*`, RPT-04).
- **D-13: The census covers the whole of v5.0 plus v4.0's still-open rows.**
  - All carried items from REVIEW / VERIFICATION / SECURITY / UAT across Phases 29–33, including:
    - the 15 rows staged in `33-03-SUMMARY.md` (P31-WR-01; P32 CR-01/WR-01/WR-02/WR-04/WR-05 +
      IN-*; IN-03's dated continuation; ACTRL-01 NAMED-LIMITATION);
    - `33-REVIEW.md` WR-01/WR-02/IN-01..03;
    - what 30/31/32 carried forward.
  - The 6 RE-DEFERRED rows of `results/phase28_ledger.json` are re-disposed in the v5.0 ledger BY
    REFERENCE (id + the phase28 ledger's sha256). They are never copied back into the frozen file.
  - Ids carry the phase prefix (Phase 33 D-11).
  - The planner re-measures each item's guard status before assigning a disposition, per the
    Phase 28 D-32 pattern: this list is the pattern, not the census. Every count in prose comes
    from `len()`.
- **D-14: 33-REVIEW WR-01 (`git_sha()` reads the cwd) and WR-02 (`--out` bypasses write-once) are
  RE-DEFERRED, not fixed.**
  - Measured: `scripts/phase33_admission.py` is pinned in `results/phase33_admission.json::
    provenance.module_sha256` (`2041aecc…` = live), guarded at `tests/test_phase33_admission.py:424`,
    so a fix reddens that guard.
  - The record is unaffected, because it was written from the repo root and its `git_sha` holds.
  - Target: "the milestone that reuses `phase33_admission`". Prerequisite: fix with a dated pin
    continuation before reuse. This is the same treatment as AR-32-02/03.

### Area E — Close and the push (RPT-06, D-38)

- **D-15: Two developer pushes, both human checkpoints. Claude never runs `git push`.**
  - **Push 1, at the START of the phase, before the publishing commit.** Measured: `main` is 75
    commits ahead of `origin/main` (`68d2bee`, the Phase 31 close), so none of the Phase 32–33 code
    has run in CI. Any CI defect then surfaces before the freeze. In Phase 28 the first push found
    4 failures only after publishing.
  - **Push 2, after the publishing commit.** Its green run id, head sha, conclusion and url are
    recorded in `results/phase34_ledger.json::close.ci_run`, and the rows stay byte-unchanged.
  - Record the id and head of the run from push 1 as well, for the audit trail. Only push 2's run
    closes RPT-06.
- **D-16: Ticks and the boundary.** RPT-04..06 are ticked by hand only after their evidence exists.
  RPT-06 needs a green run whose head contains the publishing commit. `/gsd-complete-milestone`
  owns PROJECT.md, MILESTONES.md and the `v5.0` tag (see D-11).

### Claude's Discretion
- Template file names (`scripts/phase34_report.md.tmpl` / `phase34_glance.md.tmpl` are the
  expectation) and the constant naming inside `phase34_report.py`.
- How `Bindings` is re-parametrized (subclass versus constructor arguments), as long as
  `phase28_report.py` is byte-unchanged.
- Section title wording. Constraint: it names MOOT and the per-leg outcome, not a phrase describing
  them.
- Plan/wave structure and sequencing of the two push checkpoints and the developer's read of the
  rendered blocks before the publishing commit (the 28-06 pattern).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope
- `.planning/ROADMAP.md` §"Phase 34: v5.0 Report and Milestone Close" — goal + SC1..SC3
- `.planning/REQUIREMENTS.md:646-648` — RPT-04, RPT-05, RPT-06

### The v4.0 precedent (the pattern this phase follows)
- `.planning/milestones/v4.0-phases/28-report-the-published-null-and-milestone-close/28-CONTEXT.md` — D-01..D-39, the discipline carried above
- `scripts/phase28_report.py` — engine to import (never edit); `check` must stay green
- `scripts/phase28_report.md.tmpl`, `scripts/phase28_glance.md.tmpl` — template grammar
- `tests/test_phase28_report.py` — byte-identity + numeral-scan test pattern
- `results/phase28_ledger.json` — schema/domain to copy; its 6 RE-DEFERRED rows are re-disposed by reference
- `scripts/_addendum.py`, `scripts/_prose.py` — post-freeze corrections, prose normalization

### v5.0 records (the only numeric sources)
- `results/phase32_frontier.json` — `verdicts.{tallies_by_leg, leg_refusals, control_readings, condition_c_vs_v4, replicated_at_second_seed, route}`
- `results/phase33_admission.json` — `admission`, `scope`, `limitation`, `provenance`
- `results/phase30_calibration.json`, `results/phase31_budget.json`, `results/phase31_probe_*.json`, `results/phase32_point_*.json` — available bindings
- `scripts/phase29_prereg.py` — `V5_RESULT_PATHS` / `ARTIFACT_PATHSPECS` (results/phase34_* is guarded)

### Ledger inputs (the census)
- `.planning/phases/33-admission-and-relearning-on-admitted-points/33-03-SUMMARY.md` — 15 staged rows
- `.planning/phases/33-admission-and-relearning-on-admitted-points/33-REVIEW.md` — WR-01/02, IN-01..03
- `.planning/phases/33-admission-and-relearning-on-admitted-points/33-CONTEXT.md` — D-08, D-10, D-11, D-14, D-15 dispositions
- `.planning/phases/3[0-2]-*/3*-REVIEW.md`, `*-VERIFICATION.md`, `*-SECURITY.md` — carried items (32-SECURITY.md:107-110 = AR-32-02/03)

### RPT-05
- `tests/test_package.py` — current four-tag test (to supersede) + `PYPROJECT_SHA256` detector (keep)
- `.planning/MILESTONES.md` — `## vX.Y … (Shipped: …)` headings = the derived tag set
- `.github/workflows/ci.yml` — `fetch-depth: 0` (tags must be fetched)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `phase28_report.Bindings` / `render` / `_Template` / `_fmt` / `resolve` / `ledger_rows_digest`: the binding engine.
- `phase28_report.install` / `check` / `_span`: the sentinel install/check pattern. It is PRE-PUBLISH ONLY for write.
- `tests/test_package.py::_git`, `_deps`: the tomllib + `git show` helpers for RPT-05.

### Established Patterns
- Records are loaded as bytes with a sha256 per source. A missing binding raises and is never blank.
- The ledger `close` block sits outside the rows digest and the frozen-bytes view.
- Planning files are edited by hand. `gsd-sdk` mutation handlers corrupt frontmatter (see memory).

### Integration Points
- `docs/REPORT.md` after line 1609; `README.md` above line 111.
- `phase29_prereg` ancestry guard over `results/phase34_*`: the ledger must be committed after the
  prereg, which is already true.

</code_context>

<specifics>
## Specific Ideas

- The developer's framing is that n8 and n64 are distinct findings, never one aggregate, and that
  the comparison is cited from `condition_c_vs_v4`, never rebuilt in prose.
- The developer asked that the RPT-05 tension between "the test runs today without a v5.0 tag" and
  "anchor on a fixed tag, not a moving HEAD" be resolved explicitly. D-10 resolves it by deriving
  the required set from MILESTONES.md.
- The developer's premise that the ledger could be extended because data carries less risk than
  code was measured FALSE for `phase28_ledger.json` (D-12). The single-source discipline holds per
  milestone instead.

</specifics>

<deferred>
## Deferred Ideas

- Frontier plots for the v5.0 sweep (`results/phase34_*.png`). Not needed with 0 PASS and n64
  refused; they can be added in a future milestone that has a non-empty frontier.
- README "Repository status (recorded 2026-09-02)" still describes v4.0 as in progress. That is a
  dated corrections-table entry for the milestone close or a later docs pass, not this report.

</deferred>

---

*Phase: 34-v5-0-report-and-milestone-close*
*Context gathered: 2026-09-28*
