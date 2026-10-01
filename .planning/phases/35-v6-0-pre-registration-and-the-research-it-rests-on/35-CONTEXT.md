# Phase 35: v6.0 Pre-Registration and the Research It Rests On - Context

**Gathered:** 2026-10-01
**Status:** Ready for planning

**Provenance of this discussion:** every decision below was decided by Rafael in
`/gsd-discuss-phase 35` (2026-10-01). Asked how to record the drafting provenance of his answers,
Rafael said not to bother ("não ligue para isso"), so none is claimed here. Nothing below is
recorded as "selected by THE USER, verbatim".

<domain>
## Phase Boundary

One CPU-only v6.0 pre-registration module, ancestry-guarded ahead of every v6.0 result record, that
fixes the CORE (every v6.0 record path, every rule and threshold that does not depend on a v6.0
measurement, a confirmation that the inherited pins/guards/values still hold) plus a REGISTRY OF
DEFERRED SLOTS for every threshold that depends on a later input. Plus the PREREG-09 research note
and the CPU reproduction it requires. No training, no scoring, no MPS time; no v6.0 number is
produced in this phase.

Requirements: PREREG-05, PREREG-06, PREREG-07, PREREG-08, PREREG-09.

**Scope correction made in this discussion:** ROADMAP Phase 35 SC1 and REQUIREMENTS PREREG-05
said the module "fixes every front's rule, record paths and thresholds", which contradicted Phases
37, 40 and 41 (they derive their thresholds later). Both were reworded on 2026-10-01 to "core +
registry of deferred slots". The v4.0/v5.0 prefixes were verified byte-identical, and
`phase28_report.py check` and `phase34_report.py check` both exit 0.

</domain>

<decisions>
## Implementation Decisions

### Architecture: the core plus a registry of deferred slots (PREREG-05)
- **D-01:** The Phase 35 module locks NOW everything that does not depend on a v6.0 measurement:
  - the `seed_list` (D-05);
  - the four E1 targets and their selection rule (D-03);
  - the R1a exact assertions;
  - the AUDIT-02 cut rule;
  - the imported D-01 dialogue band;
  - the provenance rule (D-08);
  - the slot registry (D-02);
  - every v6.0 record path.

  The R1a assertions are k = 78, target 0/27, 7/7 non-targets beyond 0.2962962962962963, and
  77.6370113463966% of the adaptation destroyed.

  The D-01 band is `mitigation_gate.dialogue_gap_band`, imported for ERASE-09.

  Confirming that the inherited pins, guards and values still hold is part of the core. That
  covers F_Y = 0.7 and F_C = 0.5 (`mitigation_gate.py:203,217`, already labelled "PREFERENCE, not
  a derivation") and the AUDIT-02 cut.
- **D-02:** Every deferred slot is declared NOW with four fields: name, owning phase, the rule by
  which the value will be derived, and the input record it depends on.

  Each owning phase has its own ancestry-guarded pre-registration module (the phase23 / 25 / 26 /
  27 precedent: `phase23_prereg`, `phase23_matched_prereg`, `phase23_resume_prereg`,
  `phase25_prereg`, `phase26_prereg`, `phase27_prereg`). It is committed before any record of that
  phase.

  A test reddens in three cases:
  1. a slot appears that is not in the Phase 35 registry;
  2. a slot is filled outside its owning phase;
  3. a slot is filled by a rule different from the declared one.

  Starting registry, from the requirements. Rafael named the first three as examples; the planner
  completes and classifies the rest:

  | Slot | Owner | Rule / input |
  |------|-------|--------------|
  | E2 `S` | Phase 40 | from the Phase 36 COST-01 probe record under the COST-02 budget; capped by D-06 |
  | R1b tolerance + definition of "replicated" | Phase 37 | REPRO-03; before the MPS replica runs |
  | E1 checkpoint grid | Phase 41 | design already fixed by ERASE-07: grid read with A2 at K = 16, first zero confirmed at K = 48, a non-zero K = 48 continues; the grid itself is settled in Phase 41's discuss |
  | E1 per-target condition-(a) floors | Phase 41 | ERASE-06; calibration per ordering, and per seed if the derivation requires it |
  | E1 alternative ordering | Phase 41 | ERASE-04 (see D-04) |
  | E3 grid subset (~12 configs, LR × steps × batch at σ ∈ {0.5, 1}, n = 8) | Phase 42 | inputs: the Phase 36 probe at the longest step count and the PREREG-09 note |
  | E4 parameters (canaries incl. any Phase-17-cleared mints, inclusion probability, guesser, confidence) | Phase 43 | inputs: the PREREG-09(a) note and its reproduction (D-11) |
  | E5 set sizes (≤ 512, as far as minting allows) and the minting rule | Phase 38 | RANK-01; before any scoring |
  | E6 subset of the 216 A2 entries entering the full-context NLL | Phase 39 | CTX-01; before any scoring |
  | v6.0 budget and stop line | Phase 36 | COST-02, from the probe records; ceiling 90 h MPS |
- **D-03:** E1 targets: the rule reads `phase19_erasure.TARGET_RANKING` and selects the rows where
  successes == n_questions (13/13). Today that yields `pet_name`, `cat_name`, `street` and
  `sibling_name`. The rule is code. The four names are its output and are asserted, never typed
  as the source.
- **D-04:** If a slot does not actually depend on a measurement, the planner classifies it. The
  E1 alternative ordering and the E6 entry subset are design choices, not measurements, so they
  may be lockable now. If such a slot is locked in Phase 35, the planner must say so explicitly
  and give the entry its full provenance fields (D-08). Otherwise the slot stays owned by its
  phase.

### seed_list (PREREG-05)
- **D-05:** `seed_list` IS `phase23_run.SEED_LADDER` = (1337, 2024, 1338, 2025, 1339), obtained by
  IMPORT, never copied.
  - **Mechanics (Rafael chose "Import lazy + trava"):** a function `seed_list()` imports
    `phase23_run` inside its body and returns `SEED_LADDER` by identity. This follows the
    `replay_windows` / v5.0 D-04 precedent and keeps the module torch-free at import. This
    matters because `phase23_run.py:105` imports `teach_persona` (torch) at module level.
  - **The lock:** `phase23_run.py` is not frozen. Its own docstring (`:140-145`) says the ladder is
    "NOT ancestry-bound" and lives in a file later plans re-edit; the file has had 15 commits.
    So a test reads `scripts/phase23_run.py` at commit `5303819` (2026-08-27, where the ladder
    landed) via `git show`, parses the tuple with AST, and requires it to equal the live
    `SEED_LADDER`. Any future edit to the ladder reddens the test. There is no copy in code.
  - Record in the entry that 2024 was already the second seed of Phase 19
    (`phase19_erasure.DIALOGUE_NOISE_FLOOR_SEEDS = (1337, 2024)`, Phase 12's own second seed,
    reused). The ladder was committed before any v6.0 result, so it is not a post-hoc choice.
  - E1's two teaching seeds are `seed_list()[0]` = 1337 and `seed_list()[1]` = 2024.
- **D-06:** The length 5 caps E2's `S` at 5, the most Rafael has accepted (NOISE-01: "S = 5
  acceptable"). **If the Phase 36 probe calls for S > 5, STOP and ask Rafael. Never extend the
  list.** This is a coded refusal in the S slot's rule, not a prose note.

### Derivations and proposers (PREREG-06, PREREG-07)
- **D-07:** Every threshold is a structured entry in the module and is checked by a test. Each
  entry has six fields:
  - `value`;
  - `derivation` (short text plus the record or calculation it comes from);
  - `kind` ∈ {`derived`, `preference`};
  - `proposer` ∈ {`Rafael`, `Claude Code`, `Claude (claude.ai)`};
  - `adopted_by`;
  - `source` (a commit or the message where it entered).

  A `.md` of derivations may explain in prose, but the VALUE exists only in the module. The test
  requires every field and rejects a missing or unknown `kind`.
- **D-08:** Provenance for decisions already on record:
  - Decisions that entered REQUIREMENTS from Rafael's pasted answers: `proposer` = "Claude
    (claude.ai)", `adopted_by` = "Rafael", `source` = commit `a9cd408` plus the checkpoint where
    they entered. This applies, for example, to ERASE-07's K = 16 / K = 48 design, RECIPE-04 and
    PREREG-09.
  - Decisions Claude Code proposed: `proposer` = "Claude Code", `adopted_by` = "Rafael". Example:
    the exact AUDIT-02 cut "strictly > 3.7965357228934966" in place of "≥ 3.80", verified in the
    v6.0-opening transcript; Rafael's draft said "≥ 3,80 (Tabela 7)".
  - Never write "selected by THE USER, verbatim" for text drafted by another assistant.
- **D-09:** The AUDIT-02 cut value is READ from `results/phase26_canary.json` at use, never retyped.
  Its definition is the minimum `epsilon_upper` over the noised points where
  `epsilon_upper >= auditor_ceiling`. Verified on 2026-10-01: 11 of 15 noised points, minimum
  3.7965357228934966 at σ = 16, `auditor_ceiling` = 2.7858978325772576. The rule is "E4 runs iff
  the CPU-computed ceiling > that value". `kind` = `derived`.

### PREREG-09 research
- **D-10:** One note in `.planning/research/` with citations verified at the source: arXiv ID,
  version, theorem or algorithm number, and page. For every claim used in a threshold, the note
  paraphrases the passage. If a source is not accessible, write "não verificado" and do not use
  that source to fix any threshold.
- **D-11 (a) one-run audit, Steinke–Nasr–Jagielski 2023:**
  - Implement the bound on CPU and reproduce a value published in the paper itself. The
    researcher/planner picks the value and cites its table or figure and page, with a declared
    tolerance.
  - **Without that reproduction, the AUDIT-01 ceiling is not computed and E4 does not advance.**
  - The reproduction is a committed CPU test.
- **D-12 (b) E3 selection accounting:**
  - Basic composition over the whole grid is the default. It needs no reproduction, only a test
    against a hand-computed example.
  - A finer method may enter only if three things hold:
    1. the note cites the exact theorem (for example Papernot & Steinke, arXiv 2110.03620,
       already cited at `.planning/research/PITFALLS.md:550`);
    2. its hypotheses are checked against our design;
    3. a test checks it against a worked example from the paper.
  - If the hypotheses do not match, only basic composition remains, with
    `selection_accounted = false` declared (RECIPE-02).

### CPU tests (PREREG-08)
- **D-13:** Every rule module has a CPU test. MPS-only tests are skipped in CI with an attributed
  count, following the repository's existing skip-attribution mechanism (planner locates it).

### Claude's Discretion
- Module and test file names (e.g. `scripts/phase35_prereg.py`, `tests/test_phase35_prereg.py`)
  and where the research note lives under `.planning/research/`.
- The slot registry's data shape and how "filled by a different rule" is checked mechanically,
  for example a rule identified by qualified function name and the owning prereg filling through
  that exact callable.
- AST-guard mechanics against re-typed constants, following the phase29 register (`_prove` →
  SystemExit, `is` identity tests, AST binding checks).
- Which published Steinke et al. value to reproduce (D-11), cited by table/figure and page.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope
- `.planning/ROADMAP.md` §"Phase 35" (SC1 reworded 2026-10-01) and §§"Phase 36"–"Phase 45": every
  slot owner's success criteria
- `.planning/REQUIREMENTS.md` §"v6.0 Requirements" (below the frozen v4.0/v5.0 rule — append-only
  discipline; PREREG-05 reworded 2026-10-01)
- `.planning/PROJECT.md` §"Current Milestone: v6.0"

### Pre-registration precedent (copy the register, not the numbers)
- `scripts/phase29_prereg.py`: module docstring register, `_prove`, a single results-path tuple
  with DERIVED pathspecs (`V5_RESULT_PATHS` → `ARTIFACT_PATHSPECS`), lazy torch imports,
  `NAMED_LIMITATIONS`
- `tests/test_phase29_prereg.py`: the ancestry guard
  (`test_phase29_prereg_is_frozen_before_every_v5_result`), the AST census and the `is` tests
- `scripts/phase27_prereg.py:95-110` and `tests/test_phase27_prereg.py:171`: the int-copy +
  equality pattern that D-05 deliberately does NOT use
- `.planning/milestones/v5.0-phases/29-v5-0-pre-registration-and-carried-debt/29-CONTEXT.md`:
  D-01..D-05 (paths, guard scope, lazy import, the route-never-the-pin rule)
- `scripts/_addendum.py`: the only correction route once the first v6.0 record exists

### Closed pins to import (never copy, never edit)
- `scripts/erasure_gate.py`, `scripts/phase19_erasure.py` (`TARGET_RANKING` :604,
  `DIALOGUE_NOISE_FLOOR_SEEDS` :1041), `scripts/mitigation_gate.py` (`F_Y` :203, `F_C` :217,
  `dialogue_gap_band` :526), `scripts/mitigation_budget.py`, `scripts/phase18_extraction.py`,
  `scripts/phase26_canary.py`
- `scripts/phase23_run.py:146` `SEED_LADDER`; first landed at commit `5303819`

### Records read (never retyped)
- `results/phase26_canary.json`: `auditor_ceiling`, `points.*.epsilon_upper` (the AUDIT-02 cut)

### Research inputs
- `.planning/research/PITFALLS.md:550,1318` and `.planning/research/SUMMARY.md:232,858`:
  Papernot & Steinke 2110.03620 (from v4.0 research; to be re-verified at the source per D-10)
- Steinke, Nasr, Jagielski (2023), the one-run audit: not yet in the repo. The researcher fetches
  it at the source (arXiv) and verifies it per D-10/D-11.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `phase29_prereg` structure: results-path tuple → derived pathspecs, `_prove`/`_prove_count`,
  lazy-import functions, `NAMED_LIMITATIONS` dict
- `mitigation_gate.dialogue_gap_band`: the D-01 band ERASE-09 imports
- `phase19_erasure.TARGET_RANKING`: the input of the E1 target rule
- The Phase 26 Wilson/z machinery (`erasure_gate._Z_ONE_SIDED_95`), relevant context for the E4
  confidence parameter

### Established Patterns
- Stdlib-only at import, with torch-importing sources imported lazily inside functions
- Ancestry guard: every commit touching the prereg is a strict ancestor of the first-add of every
  guarded results file (earliest add, `git log --diff-filter=A`)
- Write-once records; corrections only as dated continuations
- Planning files are edited by hand (snapshot + diff), with zero `gsd-sdk` mutation handlers on
  STATE/ROADMAP/REQUIREMENTS

### Integration Points
- Phases 36–43 each add their own prereg that FILLS slots declared here; Phases 40 and 41 call
  `seed_list()`; Phase 43 consumes the D-11 reproduction; Phase 42 consumes D-12
- No `results/phase35_*` … `results/phase45_*` file exists as of 2026-10-01

</code_context>

<specifics>
## Specific Ideas

- Rafael: "Se a sondagem pedir S > 5, PARE e me pergunte; não estenda a lista sozinho." (D-06)
- Rafael: "Sem essa reprodução, o teto do AUDIT-01 não é calculado e o E4 não avança." (D-11)
- Rafael: "Se alguma fonte não for acessível, escreva 'não verificado' e não use a fonte para
  fixar limiar." (D-10)

</specifics>

<deferred>
## Deferred Ideas

None. The discussion stayed within the phase scope. The SC1/PREREG-05 rewording is a correction
of this phase's own scope statement, not new scope.

</deferred>

---

*Phase: 35-v6-0-pre-registration-and-the-research-it-rests-on*
*Context gathered: 2026-10-01*
