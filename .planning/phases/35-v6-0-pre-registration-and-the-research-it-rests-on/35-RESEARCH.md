# Phase 35: v6.0 Pre-Registration and the Research It Rests On - Research

**Researched:** 2026-10-01
**Domain:** CPU-only pre-registration (stdlib Python, AST/ancestry guards) + DP auditing literature (one-run audit bound, hyperparameter-selection accounting)
**Confidence:** HIGH for the repository mechanics and for the PREREG-09 sources. Each was read at the source and every number below was re-computed in this session. MEDIUM for the slot classification, which is a design judgment.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Architecture: the core plus a registry of deferred slots (PREREG-05)
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

#### seed_list (PREREG-05)
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

#### Derivations and proposers (PREREG-06, PREREG-07)
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

#### PREREG-09 research
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

#### CPU tests (PREREG-08)
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

### Deferred Ideas (OUT OF SCOPE)
None. The discussion stayed within the phase scope. The SC1/PREREG-05 rewording is a correction
of this phase's own scope statement, not new scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PREREG-05 | Ancestry-guarded v6.0 prereg: core + deferred-slot registry; imports the six closed pins, never copies them; fixes `seed_list` once | §Precedent mechanics (phase29 register, file:line); §Slot registry design; §Premise verification (which pins pull torch, so must be lazy); §Code Examples 1–4 |
| PREREG-06 | Every threshold has a written derivation; preferences labelled | §Structured entries (D-07 shape); F_Y/F_C labels verified at `mitigation_gate.py:203,217` |
| PREREG-07 | Every locked decision records its proposer | §Provenance of inherited entries; Assumptions A1–A2 (who proposed F_Y/F_C) |
| PREREG-08 | Every rule module has a CPU test; MPS-only skips attributed | §MPS-skip attribution mechanism (`tests/test_phase25_venue.py`); §Validation Architecture |
| PREREG-09 | Research on (a) Steinke–Nasr–Jagielski one-run bound and (b) E3 selection accounting, before any E3/E4 threshold | §PREREG-09 (a): Corollary 5.4 / Appendix D reproduced to < 1e-3 on six published values; §PREREG-09 (b): Papernot–Steinke Thm 2/6 hypotheses do NOT hold for E3, so basic composition with `selection_accounted = false` |
</phase_requirements>

## Summary

Phase 35 ships two files of code and one note. The code is `scripts/phase35_prereg.py`, a stdlib-only module, and `tests/test_phase35_prereg.py`, a CPU-only test. The note is `.planning/research/V6-PREREG-09.md`. Every mechanism the module needs already exists in the repo, so nothing new should be invented:

- **The register.** `phase29_prereg` gives `_prove`/`_prove_count`, a single results-path tuple with derived pathspecs, lazy imports of torch-bearing sources and `NAMED_LIMITATIONS`.
- **The ancestry helper.** `tests/test_phase29_prereg.py::_assert_frozen_before` is already imported by `tests/test_phase31_budget.py:282`.
- **The reservation→fill precedent.** `phase25_prereg.CANARY_RESERVATIONS` is filled by `phase26_prereg.RULE`, with an `is` test.
- **Basic composition.** `phase25_epsilon.curve_total` and `phase25_epsilon.SELECTION_ACCOUNTED = False` already implement it.
- **The skip-count register.** `tests/test_phase25_venue.py` holds the attributed per-host skip counts.

Every factual premise in CONTEXT was measured and holds. Measurement also turned up four facts CONTEXT does not state. The planner must act on them:
1. **More pins load heavy dependencies at import.** `phase19_erasure` imports torch at module level (`phase19_erasure.py:120`), and so does `phase18_extraction`. `phase26_canary` runs `git_sha()` (a subprocess) at import (`phase26_canary.py:66`) and loads the accountant. So the D-03 target rule and the AUDIT-02 reader must import their pins lazily, exactly like `seed_list()`.
2. **`5303819` is the first add of the whole file.** It is the commit that ADDED `scripts/phase23_run.py` (`git log --diff-filter=A`), so the D-05 lock can derive the commit mechanically instead of typing the SHA.
3. **Two R1a values are not in any JSON record.** The 77.6370113463966% and the k = 78 are not stored as fields. They re-derive from `results/phase19_arm_erased.json`: `len(config.ablated_components) == 78`, and the dialogue-gap arithmetic gives 77.6370113463966 exactly. The 0/27 and 7/7 cannot be re-derived from that record without Phase 37's defect routing. The record's `per_fact` gives the target 0/14 (defect C), and `config.k` is 48, the attack budget, not the prefix length.
4. **Two slots have their input inside their own phase.** The Phase 36 budget is derived from Phase 36's own probe records, and the Phase 41 floors from Phase 41's calibration records. So "the owning prereg is committed before any record of that phase" must exclude the slot's declared input records. Otherwise the rule contradicts COST-02 and ERASE-06.

PREREG-09 (a) is fully reproducible on CPU. Steinke, Nasr and Jagielski, arXiv 2305.08846v1 (the only version, 15 May 2023), state the bound in Theorem 5.2 (p. 14). The ternary-guess form, Corollary 5.4 (pp. 15–16), is "the form ... we use in all of our experimental results". Appendix D (pp. 45–46) gives Python pseudocode for it. A stdlib port, written as a throwaway in the scratchpad and not committed, reproduces every worked value it was checked against within one unit in the last printed digit:
- Appendix D, p. 46: `get_eps_audit(1000,100,75,1e-4,0.05)` → 0.673 (ours 0.6729846633970737).
- p. 28: m = 100,000, r = 1510, v = 1439, δ = 1e-5, 95% → 2.675 (ours 2.6758510060608387).

PREREG-09 (b): Papernot & Steinke, arXiv 2110.03620v2 (ICLR 2022), Theorems 2 and 6 (pp. 5, 7), require a **random** number of runs K, drawn from a truncated negative binomial or a Poisson distribution, with a uniformly random candidate per run and only **the best** output released. E3 is a fixed grid run once each, and every configuration's ε is published. The hypotheses fail. Only basic composition remains, with `selection_accounted = false`.

**Primary recommendation:** Build `scripts/phase35_prereg.py` in the phase29 register: stdlib top-level imports of the three torch-free pins and lazy imports for `phase19_erasure`, `phase18_extraction`, `phase23_run` and `phase26_canary`. It holds one `V6_RESULT_PATHS` tuple, one `ENTRIES` dict of D-07 entries, one `SLOTS` dict whose rules are module-level functions reached only through `fill()`, and the stdlib one-run-audit port. Commit it together with its test and the PREREG-09 note before any `results/phase36_*` exists.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Core rules, entries, slot registry, record paths | `scripts/phase35_prereg.py` (stdlib, frozen by ancestry) | — | Must exist before any v6.0 record. Read by Phases 36–45 |
| Ordering proof (prereg precedes every v6.0 record) | `tests/test_phase35_prereg.py` (CPU, git) | CI `fetch-depth: 0` (`.github/workflows/ci.yml`) | Ancestry needs full history; a shallow clone must fail loudly, not skip |
| Seed ladder lock | test (git show + AST at the first add of `phase23_run.py`) | `phase23_run.SEED_LADDER` (live, torch at import) | The module holds no copy; the test compares history with the live value |
| AUDIT-02 cut value | committed record `results/phase26_canary.json` | `phase35_prereg.audit02_cut()` (reads at use) | D-09: never retyped |
| One-run ε bound (D-11) | `phase35_prereg` (stdlib port of App. D) | test pinning the published values | E4's go/no-go depends on it, so it must be frozen with the prereg |
| Slot fills | each owner's own `scripts/phase{NN}_prereg.py` | Phase 35 census test (AST over `scripts/phase3[6-9]_*`, `phase4[0-5]_*`) | D-02 |
| Prose derivations, citations | `.planning/research/V6-PREREG-09.md` | — | D-07: values live only in the module |

## Standard Stack

No new dependency. Stdlib (`ast`, `math`, `subprocess`, `fnmatch`, `json`, `pathlib`) plus the repo's own modules. `[VERIFIED: pyproject.toml, .venv probe]`

### Core (reuse, never re-implement)
| Asset | Location | Purpose | Why |
|-------|----------|---------|-----|
| `_prove` / `_prove_count` | `scripts/phase29_prereg.py:71-83` | SystemExit-based invariants (`python -O`-safe) | House register; copy the 4-line pattern into the new module (each prereg owns its own `_prove`, as phase26/29 do) |
| `_assert_frozen_before`, `_git` | `tests/test_phase29_prereg.py:52-106` | Strict-ancestry check, earliest add, same-commit refusal, shallow-clone refusal | Already imported elsewhere: `tests/test_phase31_budget.py:282` `from test_phase29_prereg import _assert_frozen_before, _git` |
| `_module_targets`, `_numeric_constants`, `_planted` | `tests/test_phase29_prereg.py:426-442, 526-531` | AST binding/literal guards, each watched RED on a `tmp_path` copy | Import them the same way |
| `phase25_epsilon.curve_total(eps, *, delta)` | `scripts/phase25_epsilon.py:271-294` | Basic composition: `(fsum(eps), len(eps)*delta)`; refuses None/inf | D-12 default; already used for v4.0's curve total |
| `phase25_epsilon.SELECTION_ACCOUNTED` | `scripts/phase25_epsilon.py:68` (`False`) | RECIPE-02 flag | By reference |
| `mitigation_unit.DELTA` | `scripts/mitigation_unit.py:171` (`1e-5`) | δ for E3/E4 | By reference |
| `erasure_gate.CONFIDENCE` | `scripts/erasure_gate.py:89` (`0.95`) | Candidate source for E4's β = 1 − CONFIDENCE | By reference (if Phase 43 adopts it) |
| `mitigation_gate.dialogue_gap_band`, `F_Y`, `F_C`, `K_RUNGS` | `scripts/mitigation_gate.py:526, 203, 217`; `K_RUNGS = (48, 24, 16, 8)` | D-01 band, inherited preferences, K menu | By reference (`is`) |
| `mitigation_budget.STEP_BUDGET`, `SIGMA_LADDER`, `CURVE_K` | `scripts/mitigation_budget.py:508`, `:770`; `CURVE_K = 16` | RECIPE-04's T = 200 baseline; σ ∈ {0.5, 1} are ladder members; K = 16 precedent | By reference |
| `phase26_prereg.CEILING_CLAUSE`, `auditor_ceiling` | `scripts/phase26_prereg.py:277-290` | AUDIT-03 "could not have failed" wording/rule | By reference |
| `_addendum.append_addendum` | `scripts/_addendum.py` | Dated continuation of published *markdown* after records exist | The correction route for prose; a Python pin is continued by a new module (phase23_resume_prereg / phase26_prereg precedent) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib binomial (`math.lgamma`) | `scipy.stats.binom` (what App. D calls) | scipy is NOT installed in `.venv` `[VERIFIED: import probe]` and the stack forbids new deps. The stdlib port matched every published value tested |
| int-copy + equality (`phase27_prereg.py:95-110`, test `:171`) | lazy import + historic AST lock | D-05 chose the latter. Do not use the int-copy |

**Installation:** none.

## Package Legitimacy Audit

No package is installed by this phase. `pypdf` was installed only into a throwaway scratchpad venv to read the two arXiv PDFs. It is not a project dependency and must not be added. slopcheck was not run, because there are no packages to vet.

| Package | Registry | Disposition |
|---------|----------|-------------|
| (none) | — | — |

## Precedent Mechanics (exact file:line) `[VERIFIED: codebase read]`

### `scripts/phase29_prereg.py` (662 lines)
- **Docstring register `:1-43`.** It lists WHAT THIS FREEZES, ANCESTRY-GUARDED (with the correction route), CPU-ONLY AT IMPORT (naming the transitive accountant load honestly), THE ROUTE NEVER THE PIN, and the threats mitigated.
- **sys.path insert `:49-53`, then top-level imports of torch-free siblings only, `:55-60`.**
- **`COMMITTED = "2026-09-24"`, `RECORDS_AT_COMMIT = 0` `:67-68`.** The date and the property it certifies.
- **`_prove` `:71-74`.** It raises `SystemExit(f"[phase29_prereg] {message}")`, never `assert`. **`_prove_count` `:77-83`** accepts an int and rejects a bool.
- **By-reference block `:90-93`** (`RATIO_GRID = mitigation_budget.ADVERSARIAL_RATIO_GRID`, `F_Y = mitigation_gate.F_Y`, …). The test asserts `is` at `tests/test_phase29_prereg.py:281-287`.
- **Results paths `:148-158`.** `V5_RESULT_PATHS` is one tuple. **Derived pathspecs `:161`:** `ARTIFACT_PATHSPECS = tuple(sorted({p.split("_", 1)[0] + "_*" for p in V5_RESULT_PATHS}))`.
- **Lazy import `:171-182`.** `replay_windows()` does `import teach_persona` inside the body.
- **`NAMED_LIMITATIONS` `:274-307`.** A dict of `{reason, source, ledger_rows, ...}`, checked against `results/phase28_ledger.json` by `tests/test_phase29_prereg.py:610-621`.
- **D-09 pins as attribute bindings `:315-334`.** The test checks the AST binding shape, because `is` is vacuous on CPython's small-int cache (`tests/test_phase29_prereg.py:1029-1045`).

### `tests/test_phase29_prereg.py` (1093 lines)
- **`_git` `:52-56`.** `subprocess.run(("git", *args), check=True)`.
- **`_assert_frozen_before(prereg_artifact, tracked)` `:69-106`.** It refuses a shallow clone (`rev-parse --is-shallow-repository`). It takes every commit touching the prereg and the earliest add of each tracked artifact (`--diff-filter=A`, `adds[-1]`). It refuses the same commit and requires `merge-base --is-ancestor`. It counts the pairs checked and is honest-green with zero tracked files.
- **The ancestry test `test_phase29_prereg_is_frozen_before_every_v5_result` `:109-117`.** It collects tracked files by `git ls-files <spec>` over `ARTIFACT_PATHSPECS`.
- **`_CALL_TIME_SOURCES` `:123-142`.** Sources resolved at call time are frozen too, with a natural-RED non-vacuity leg. Use it if the one-run-audit port is split into its own file.
- **Derived-pathspec test `:150-158`.** **Disjointness test `:161-174`** reads the v4 set at the immutable tag `v4.0`, after a dated continuation: HEAD had counted v5.0's own first record. For v6.0, read at tag **`v5.0`**, which exists locally and on origin `[VERIFIED: git tag, git ls-remote]`.
- **Torch-free import probe `:290-298`.** It runs a subprocess and asserts `'torch' in sys.modules` is False.
- **AST guards, each watched RED on a planted `tmp_path` copy `:426-586`.** The helpers are `_module_targets` `:426`, `_numeric_constants` `:437`, `_replay_literal_failures` `:445`, `_grid_retype_failures` `:460`, `_gate_retype_failures` `:484` and `_planted` `:526`.
- **Accountant census `:589-596`.** It is scoped to `phase29_*`..`phase34_*` and does NOT cover phase35+. That is correct, since v6.0 E3 needs ε.

### Owning-phase preregs that FILL earlier reservations
- **`phase25_prereg.CANARY_RESERVATIONS` (`scripts/phase25_prereg.py:496`).** A dict of rule strings reserved for Phase 26.
- **`phase26_prereg.RULE = phase25_prereg.CANARY_RESERVATIONS["audit_target_rule"]` (`scripts/phase26_prereg.py:79-80`)** is filled by reference. `SUPERSEDES` names it (`:59-62`), and `tests/test_phase26_prereg.py:103` asserts `is`. `resolve_audit_target` executes the reserved rule and `_prove`s its output (`:85-107`). This is the slot→fill shape to generalize.
- **`phase23_resume_prereg`.** A rule that arrived later goes in a **new file** because a second commit to the frozen `phase23_matched_prereg.py` would redden its guard permanently (`scripts/phase23_run.py:99-103` comment). This is the correction route for a Python pin.
- **`phase26_prereg.ARTIFACT_GLOB = "results/phase26_*"` (`:65`)** gives each owner prereg its own guarded glob.

## Slot Registry Design (D-02, Claude's discretion)

### Data shape (recommended)
```python
# scripts/phase35_prereg.py
def _rule_e2_S(*, budget_record):            # module-level, private; reached ONLY via fill()
    ...
    s = ...                                   # derived from the record
    _prove(s <= len(seed_list()), "the probe asks for S > 5: STOP and ask Rafael (D-06); "
           "the seed list is never extended")
    return s

SLOTS = {
    "e2_S": {
        "owner_phase": 40,
        "rule": _rule_e2_S,                   # the function OBJECT; identity is checkable
        "input_records": ("results/phase36_budget.json",),   # each must match a V6_RESULT_PATHS entry
        "binding": "E2_S",                    # the module-level name the owner must bind
        "derivation": "S = ... from COST-01 probe under COST-02 budget; capped at len(seed_list())",
    },
    ...
}

def fill(slot, **inputs):
    """The ONE door: runs the declared rule for a declared slot."""
    _prove(slot in SLOTS, f"slot {slot!r} is not declared in the Phase 35 registry")
    return SLOTS[slot]["rule"](**inputs)
```
The owner prereg (e.g. `scripts/phase40_prereg.py`) writes exactly `E2_S = phase35_prereg.fill("e2_S", budget_record=...)` at module level.

### Mechanical checks (all AST, all in `tests/test_phase35_prereg.py`)
The census set is every `scripts/phase{36..45}_*.py`, collected with `pathlib.glob` per phase number. Never use a shell multi-glob; under zsh NOMATCH it is blind.
1. **Undeclared slot.**
   - Every `Call` whose func is `Attribute(value=Name("phase35_prereg"), attr="fill")` must have a first arg that is an `ast.Constant` str in `SLOTS`. A non-constant first arg reddens.
   - Every module-level binding in any owner prereg whose name equals some slot's `binding` must be such a call.
   - Every `binding` name that appears anywhere in the census set must belong to a declared slot. This catches `E2_S = 5` in an undeclared form.
2. **Filled outside its owning phase.**
   - The file holding a `fill("x", ...)` call must be exactly `scripts/phase{SLOTS["x"]["owner_phase"]}_prereg.py`.
   - Any reference to a `phase35_prereg._rule_*` attribute outside `phase35_prereg.py` reddens.
3. **Filled by a different rule.**
   - The rule is dispatched from the registry, so the only way to use another rule is to bypass `fill`. Check 1's binding-shape requirement forbids that: a literal, another call, or an import from elsewhere bound to the slot's name reddens.
   - Also assert `SLOTS[s]["rule"].__module__ == "phase35_prereg"` and that its `__name__` is a module-level `FunctionDef` in the file's AST.
   - Assert `fill` calls `SLOTS[slot]["rule"]` and nothing else: AST of `fill`'s body has exactly one `Call` on a `Subscript`.
4. **Ordering (generic over the registry).** For each slot, if `git ls-files results/phase{owner}_*` is non-empty, then:
   - `scripts/phase{owner}_prereg.py` must exist and hold the fill;
   - `_assert_frozen_before(owner_prereg, owner_records − input_records)` must hold;
   - each tracked input record must be a strict ancestor of the owner prereg's first commit (the input existed before it was derived from).

   This is honest-green today, with zero v6.0 records.

**Non-vacuity:** each check must be watched RED on a `tmp_path` planted owner file, as at `tests/test_phase29_prereg.py:526-586`. Use a planted file over a real-tree mutation, because the clean-tree probes forbid untracked files under `scripts/`.

### Classification of every candidate slot (D-04)
"Measured" means the value needs a v6.0 record. "Lockable now" means only a design choice is needed.

| Slot (proposed name) | Owner | Input record(s) | Class | Reasoning |
|---|---|---|---|---|
| `v6_budget_and_stop_line` | 36 | `results/phase36_probe_*.json` (Phase 36's own) | Measured | COST-02 derives it from the probes. **Its input lies inside its own phase**: the ordering check must exclude the probe records (finding 4) |
| `e2_S` | 40 | `results/phase36_budget.json` | Measured | COST-01/02. The rule refuses S > `len(seed_list())` (D-06) |
| `r1b_tolerance_and_replicated` | 37 | `results/phase37_r1a*.json` (the CPU re-derivation) | Design, owned by 37 | No measurement is strictly required, but ROADMAP P37 SC3 assigns it to Phase 37 and R1b depends on Phase 36. Keep it deferred |
| `e1_checkpoint_grid` | 41 | `results/phase36_*` E1 probe | Measured (cost) | ERASE-07 says "settled in E1's discuss" and re-priced by COST-01 |
| `e1_condition_a_floors` | 41 | `results/phase41_calibration_*` (Phase 41's own) | Measured | ERASE-06: calibration per ordering/seed. **Its input lies inside its own phase** (finding 4) |
| `e1_alternative_ordering` | 41 | none | **Lockable in principle; recommend keeping it deferred** | No measurement needed, but no decision on record names which alternative. Locking it here means inventing a choice. If the planner locks it, that needs a Rafael checkpoint and full D-08 provenance |
| `e3_grid_subset` (+ RECIPE-04 P22 assertion inside its rule) | 42 | `results/phase36_*` DP probe + the PREREG-09 note | Measured (cost) | The probe at the longest step count prices it. The rule must also refuse a grid that crosses the P22 region for any T ≠ 200 |
| `e4_parameters` (m, p, guesser k+/k−, β) | 43 | PREREG-09 note + the D-11 reproduction; Phase 38 minting clearance for mints | Mixed | **p = 1/2 is forced by the reproduced method** (App. D assumes 0.5; Prop. 5.7 covers other p but has no reproduced implementation), so the rule should refuse p ≠ 1/2. δ = `mitigation_unit.DELTA`. β could come from `erasure_gate.CONFIDENCE` (0.95 → β = 0.05, matching Phase 26's one-sided 95%). m depends on how many independently-randomized facts exist → measured |
| `e5_set_sizes_and_minting_rule` | 38 | `results/phase36_*` minting sample | Measured | "As far as minting allows" is a yield |
| `e6_entry_subset` | 39 | `results/phase36_*` anchor-context probe | **Measured (cost), keep deferred** | The choice is design, but CTX-01's subset exists to fit the budget. If it were "all 216" it would be lockable now. No such decision is on record |

### Slots the requirements imply that the D-02 table is missing `[VERIFIED: grep of REQUIREMENTS v6.0 + ROADMAP P36–45]`
| Missing slot | Owner | Source text | Why it is a slot |
|---|---|---|---|
| `e3_recall_threshold` | 42 | RECIPE-03 "a recall threshold pre-registered and imported from the v4.0 gate" | The v4.0 rule is `F_Y × control recall` (`mitigation_gate.py:192-203`), but WHICH control reading (E3's own σ = 0 control, or v4.0's `dp_n8` control) is unstated. The rule can be declared now; its input is a record |
| `e1_condition_b_margin` | 41 | ERASE-10 + NOISE-02 ("without amending v3.0's (b) margin") | Does E1 grade damage against v3.0's 0.2962962962962963 or against Phase 40's training-seed floor? Unstated |
| `e1_condition_c_band_inputs` | 41 | ERASE-09 "anchored on the adapted model" | `dialogue_gap_band(*, control_gap, gap_noise_floor)` is core by reference, but both kwargs are measured per seed/ordering |
| `e2_noise_floor_estimator` | 40 | NOISE-02 | The reduction (e.g. `phase19_erasure.nontarget_noise_floor` = max) is design. It could be locked now by reference if Rafael agrees, otherwise it is a Phase 40 slot |
| `e5_rank_moves_and_generation_collapses` | 38 | RANK-02 "states whether the rank moves before generation collapses" | Needs an operational definition of "moves" and "collapses" before scoring |
| `e6_decomposition_rule` | 39 | CTX-03 "separates how much ... instrument ... context" | Needs a pre-registered decomposition |

Core items to lock now (no slot):
- `seed_list()`; the E1 target rule; the R1a assertions.
- The AUDIT-02 cut (`audit02_cut()` + `e4_runs(ceiling)`) and AUDIT-03 (`phase26_prereg.CEILING_CLAUSE` by reference).
- E3 basic composition (`phase25_epsilon.curve_total`, `SELECTION_ACCOUNTED`) and E3's fixed scope from REQUIREMENTS (σ ∈ {0.5, 1}, n = 8, unit "one taught fact", δ = `mitigation_unit.DELTA`). The σ values should be selected from `mitigation_budget.SIGMA_LADDER` by membership so they are not retyped.
- E1 seeds = `seed_list()[:2]`; ERASE-10 "no PASS without the second seed".
- The record paths.

## Premise Verification (CONTEXT measured, 2026-10-01)

| Premise | Measured | Result |
|---|---|---|
| `phase19_erasure.TARGET_RANKING` at `:604`; rows with successes == n_questions | `scripts/phase19_erasure.py:604-613`: `pet_name`, `cat_name`, `street`, `sibling_name` are 13/13; `person_name` 12/13 … `hometown` 8/13 | ✓ matches |
| `DIALOGUE_NOISE_FLOOR_SEEDS = (1337, 2024)` at `:1041` | `phase19_erasure.py:1041` | ✓ |
| `SEED_LADDER` at `phase23_run.py:146` | `:146` = `(1337, 2024, 1338, 2025, 1339)` | ✓ |
| Same content at `5303819` | `git show 5303819:scripts/phase23_run.py`: one module-level `SEED_LADDER` Assign at line 96, `ast.literal_eval` → `(1337, 2024, 1338, 2025, 1339)` | ✓. Also: `5303819` is the file's **first add** (`git log --diff-filter=A`), dated 2026-08-27 |
| 15 commits touch `phase23_run.py` | `git log --oneline -- scripts/phase23_run.py` → 15 | ✓ |
| `phase23_run.py:105` imports `teach_persona` | `:105 import teach_persona as tp` | ✓ |
| Docstring `:140-145` "NOT ancestry-bound" | `:140-144` "HONEST LIMIT … this ladder is NOT ancestry-bound" | ✓ (block is 140-144) |
| `F_Y` `:203`, `F_C` `:217`, labelled PREFERENCE | `F_Y = 0.7  # PREFERENCE, not a derivation (D-15 / D-16 / D-18)`; `F_C = 0.5  # PREFERENCE, not a derivation (D-17 / D-18)` | ✓ |
| `dialogue_gap_band` `:526` | `def dialogue_gap_band(*, control_gap, gap_noise_floor)` at `:526` | ✓ |
| `results/phase26_canary.json`: `auditor_ceiling`, 11/15, min 3.7965357228934966 at σ = 16 | `auditor_ceiling = 2.7858978325772576`; 16 points, 15 with `epsilon_upper`; 11 have `epsilon_upper >= auditor_ceiling`; min = 3.7965357228934966 at `dp_n8_sigma16p000000` | ✓ |
| R1a k = 78 | `results/phase19_arm_erased.json::config.ablated_components` has length 78. Report text `results/phase19_erasure_report.md:134` "k = 78 of 288" | ✓. **Note:** that record's `config.k` is **48** (the A2 attack budget), not the prefix length |
| R1a 77.6370113463966% | not a stored field. Computed from `phase19_arm_erased.json`: pre gap 5.815445876712191 − 4.573349214207799 = 1.2420966625043919; post gap 4.851119149910443 − 4.573349214207799 = 0.2777699357026435; `(1 - g1/g0)*100` = **77.6370113463966**, identical under all five expression orders tried. Text at `results/phase19_erasure_report.md:146,433,496` | ✓ |
| R1a 7/7 beyond 0.2962962962962963 | margin = `results/phase19_noise_floors.json::nontarget_noise_floor.margin_at_gate` = 0.2962962962962963 = 2 × 0.14814814814814814 (`erasure_gate.MARGIN_K = 2`); "all seven gated non-targets exceed" at report `:146` | ✓ (the count is in the report; the per-fact pooled 27-question re-derivation is Phase 37's) |
| R1a target 0/27 | report `:17` "post-erasure: 0/27 questions". **The record's `per_fact.cand_dog_zorp` reads 0/14** (core_taught overwrote core_held_out: defect C, named in `phase19_noise_floors.json::nontarget_noise_floor.denominator_recovery`) | ✓ in the report. The record alone gives 0/14. Do not try to re-derive 0/27 in Phase 35 |
| No `results/phase35_*` … `phase45_*` | `find results checkpoints data -maxdepth 2` → none; `git ls-files` → 0; no `scripts/phase3[5-9]*`/`phase4*`, no tests | ✓ |
| Papernot & Steinke at `PITFALLS.md:550` | `:550` "Papernot & Steinke formalize the RDP cost of DP hyperparameter tuning"; link at `:1318` | ✓ |

**Mismatches found:** none in CONTEXT's stated facts. Four omissions matter for planning: (i) `phase19_erasure`, `phase18_extraction` and `phase26_canary` also need lazy import; (ii) `config.k` = 48 is a trap next to "k = 78"; (iii) the record holds 0/14, not 0/27; (iv) the in-phase input ordering for slots 36/41.

Measured torch/side effects at import (`.venv` 3.11.15, torch 2.7.1):

| Module | torch | other |
|---|---|---|
| `erasure_gate`, `mitigation_gate`, `mitigation_budget` | no | stdlib only: top-level import OK |
| `phase19_erasure` | **yes** (`:120 import torch`) | lazy |
| `phase18_extraction` | **yes** | lazy |
| `phase23_run` | **yes** (+ `teach_persona`) | lazy |
| `phase26_canary` | no | **`git_sha()` subprocess at import (`:66`)** + loads `personacore.privacy.accountant` → lazy |
| `phase25_epsilon` | no | loads the accountant (torch-free) |

## Provenance of inherited entries (D-08)
> **Superseded by D-14 (plan-phase 35, 2026-10-01):** entries carry no `proposer`/`adopted_by` field; the provenance below stays as the record of the research, not as entry content.
- **`F_Y`, `F_C`.** v4.0 `20-DISCUSSION-LOG.md:189-208` shows Claude Code's option menu, with **"User's choice: `f_Y = 0.7`"** and **"User's choice: `f_C = 0.5`"**. CONTEXT `20-CONTEXT.md:159-185` (D-15..D-18) records them. Whether that answer was drafted elsewhere is not recorded. `[ASSUMED]` proposer = "Claude Code" (the menu), adopted_by = "Rafael". **Confirm with Rafael**, and never write "selected by THE USER, verbatim".
- **AUDIT-02 cut.** proposer "Claude Code", adopted_by "Rafael", source a9cd408 + the v6.0-opening transcript (CONTEXT D-08).
- **ERASE-07 K = 16/48, RECIPE-04, PREREG-09.** proposer "Claude (claude.ai)", adopted_by "Rafael", source a9cd408 (CONTEXT D-08).
- **`seed_list`.** Ladder landed in `5303819` (23-08). The v6.0 adoption is this discuss (D-05): proposer and source must name the 35-CONTEXT commit `36ab0b4`.

## MPS-Skip Attribution Mechanism (D-13 / PREREG-08) `[VERIFIED: codebase read]`
- **File:** `tests/test_phase25_venue.py`. Skip counts are stated in advance as sums of **named constants**, each with a dated-continuation comment naming node ids. `_PROMOTION_EMPTY_FRONTIER_SKIPS = 3`, `_RECALL_HOST_ONLY_SKIPS = 7`, `_CANARY_HOST_ONLY_SKIPS = 9`, `_RELEARN_HOST_ONLY_SKIPS = 1`, etc. The sums are split by host: `_M3_*` vs `_UBUNTU_*` (selected by `_MPS_PRESENT`), giving `_UBUNTU_FLAG_UNSET_EXPECTED_SKIPS = 52 + 3 + 7 + 9 + 1 = 72`.
- **Enforcement:** `test_the_sweep_active_skip_count_is_the_number_stated_in_advance` and `test_with_the_flag_unset_the_baseline_is_unchanged` run the inner suite in a subprocess and assert `skipped == …_EXPECTED_SKIPS`. These two make the full suite take ~40 min.
- **Gating helpers:**
  - `tests/conftest.py::sweep_is_active()`, behind the `PERSONACORE_SWEEP_ACTIVE` flag.
  - `tests/test_phase23_mps_venue.py::_MPS_SKIP` / `_DEVICES`, imported by `test_mps_smoke.py:33` and `test_phase22_checkpoint.py:86`.
- **CI baseline:** `72 skipped` on ubuntu (v5.0 close runs 36500648069 / 36562323069, 34-VERIFICATION.md:28,37).
- **Rule for Phase 35:**
  - The new test must contain **zero skips**: it is CPU-only and reads only tracked files.
  - A shallow clone must **fail** (the `_assert_frozen_before` way), never skip.
  - Any MPS-only test a later v6.0 phase adds must use `_MPS_SKIP` and add a NAMED constant plus a dated comment to the ubuntu sums in `test_phase25_venue.py`.
  - If CI ever reports ≠ 72 after Phase 35, measure before diagnosing (memory: execute-phase gates).

## PREREG-09 (a): Steinke, Nasr, Jagielski — one-run audit `[VERIFIED: arXiv PDF read this session]`

- **Source:** "Privacy Auditing with One (1) Training Run", Thomas Steinke, Milad Nasr, Matthew Jagielski. **arXiv:2305.08846, v1 (15 May 2023), the only version** (abs page submission history). PDF footer reads "arXiv:2305.08846v1 [cs.LG] 15 May 2023".
- **Algorithm 1 (p. 3).** m canaries, each included independently with **E[S_i] = 0** (probability 1/2). The auditor scores them and guesses +1 for the top k+ and −1 for the bottom k−, abstaining on the rest; r = k+ + k−. Footnote 1 (p. 3) says other inclusion probabilities are handled by Proposition 5.7 but "seems unlikely to be useful".
- **Theorem 5.2 (Main Result, p. 14).** If M : {−1,+1}^m → [−1,+1]^m is (ε, δ)-DP and S is uniform, then P[W ≥ v] ≤ β + α·2m·δ. Here W = Σ max{0, T_i·S_i} is the number of correct guesses, β = P[W̌* ≥ v], and α = max_i (P[W̌* ≥ v − i] − β)/i over i ∈ {1..m}. W̌* stochastically dominates Σ Š_i|t_i| with Š ~ Bernoulli(e^ε/(e^ε+1)).
- **Corollary 5.4 (Ternary Guesses, pp. 15–16).** For T ∈ {−1,0,+1}^m with ‖T‖₁ ≤ r: P[W ≥ v] ≤ f(v) + 2mδ·max_i (f(v−i) − f(v))/i, with f(v) = P[Binomial(r, e^ε/(e^ε+1)) ≥ v]. The text calls this "the form of Theorem 5.2 that we use in all of our experimental results" (p. 15).
- **ε lower bound (§4.3, Lemma 4.7, pp. 8–9).** It is the largest ε whose null hypothesis is rejected at level β, i.e. p-value < β. The confidence is 1 − β.
- **Inputs:** m (randomized canaries), r (guesses), v (correct guesses), δ, β. **Appendix D (pp. 45–46)** gives `p_value_DP_audit(m, r, v, eps, delta)` and `get_eps_audit(m, r, v, delta, p)`. The latter is a 30-step bisection that returns `eps_min`, the conservative end.
- **Published values reproduced** by a stdlib port in the scratchpad (scipy's `binom.sf/pmf` replaced by an exact `math.lgamma` pmf + `math.fsum`; not committed):

| Where (page) | Inputs (m, r, v, δ, β or ε) | Published | Ours | |diff| |
|---|---|---|---|---|
| App. D, p. 45 | p-value(100,100,75, ε=ln 3, δ=0) | 0.553 | 0.553470823848239 | 4.7e-4 |
| App. D, p. 45 | get_eps(100,100,75, δ=0, β=0.05) | 0.702 | 0.7022139308974147 | 2.1e-4 |
| App. D, p. 46 | get_eps(100,100,75, δ=1e-4, β=0.05) | 0.699 | 0.6994668124243617 | 4.7e-4 |
| **App. D, p. 46 (PIN 1)** | **get_eps(1000,100,75, δ=1e-4, β=0.05)** | **0.673** | **0.6729846633970737** | 1.5e-5 |
| **§7 text, p. 28 (Fig. 11) (PIN 2)** | **m=100000, r=1510, v=1439, δ=1e-5, 95%** | **ε ≥ 2.675** | **2.6758510060608387** | 8.5e-4 |
| §7 text, p. 28 (Fig. 10) | r=10000, v=⌊10000·e⁴/(e⁴+1)⌋=9820, δ=1e-5, 95%; **m not stated** (assumed m=r) | ε ≥ 3.87 | 3.8713169284164906 | 1.3e-3 (do not pin: m is assumed) |

- **Recommended pins:** PIN 1 exercises abstentions and the 2mδ term. PIN 2 uses our δ = 1e-5 and our 95% confidence.
- **Tolerance:** |ours − published| < 10^−d, where d is the number of decimals printed (1e-3 for both pins). Justification:
  - The paper rounds some values and truncates others. 0.67298 prints as 0.673, which is rounding. 2.67585 prints as 2.675, which is truncation. So a half-unit tolerance (5e-4) would wrongly fail PIN 2, and one unit covers both.
  - One unit still discriminates the two natural bugs by ≥ 26×. Measured mutants: dropping δ moves PIN 1 to 0.7022 and PIN 2 to 2.8062. Using r instead of m in 2mδ moves PIN 2 to 2.8051. Changing β from 0.05 to 0.01 moves PIN 2 to 1.6733.
- **Closed-form check (exact, no paper needed):** at δ = 0 and v = r, the p-value is q^r, so ε = −ln(β^(−1/r) − 1). For r = 16, β = 0.05 this gives 1.5803231357927883, and the port gives 1.5803231354802847. Use a 1e-8 tolerance, which covers the bisection precision of 2^−30 · eps_max.
- **Runtime:** PIN 2 takes 0.023 s and PIN 1 0.0013 s on CPU. Both are cheap.
- **Planning-relevant observation (NOT a lock; Phase 43 computes it).** The maximum detectable ε with a perfect guesser (v = r = m), δ = 1e-5, β = 0.05:

  | m | 16 | 32 | 64 | 100 | 128 | 135 | 136 | 184 | 256 | 512 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | ceiling | 1.5798 | 2.3204 | 3.0364 | 3.4902 | 3.7396 | 3.7933 | 3.8007 | 4.1046 | 4.4352 | 5.1245 |

  It exceeds the AUDIT-02 cut 3.7965357228934966 only from **m ≥ 136** independently-randomized canaries. Under the privacy unit "one taught fact", each canary must be a fact, not a question, or group privacy breaks the theorem's one-bit-flip premise. This is the input that will most likely decide E4's branch.
- **Paper caveats that become Phase 43 pitfalls:**
  - p. 25: the authors "evaluate different values of k+ and k− and only report the highest", which they admit "reduc[es] the confidence". Our guesser must therefore fix k+/k− before the run, or use Corollary 5.8 (p. 22).
  - pp. 28–29: the bound is very sensitive to δ and to abstentions, because δ is multiplied by about m/(rβ).

## PREREG-09 (b): E3 selection accounting `[VERIFIED: arXiv PDF read this session]`

- **Source:** "Hyperparameter Tuning with Renyi Differential Privacy", Nicolas Papernot and Thomas Steinke, **arXiv:2110.03620**. v1 is dated 7 Oct 2021 and **v2 14 Mar 2022**; v2 was read and is "Published as a conference paper at ICLR 2022".
- **Theorem 2 (Truncated Negative Binomial, p. 5).** If Q is (λ, ε)-RDP and (λ̂, ε̂)-RDP, Y is totally ordered, and **K ~ D_{η,γ}**, then running Q K times and returning **the best value** is (λ, ε′)-RDP with ε′ = ε + (1+η)(1 − 1/λ̂)ε̂ + (1+η)log(1/γ)/λ̂ + log E[K]/(λ−1).
- **Corollary 3 (p. 6)** is the pure-DP form: ((2+η)ε, 0)-DP, and η = 1 (geometric) gives Liu–Talwar's 3ε. **Corollary 4 (p. 6)** is the zCDP form. **Theorem 6 (Poisson, p. 7)** gives ε′ = ε + μδ̂ + log μ/(λ−1) when e^{ε̂} ≤ 1 + 1/(λ−1).
- **Hypotheses (§3.3, p. 5).**
  1. The number of runs K is **random**, drawn from the stated distribution.
  2. Each run picks a candidate index **uniformly at random** ("random search").
  3. There is a **uniform** (Rényi) DP bound over all candidates.
  4. Only **the best** of the K outcomes is returned. Y is totally ordered.

  The paper says (p. 8) that a point mass on K "correspond[s] to naïve repetition", i.e. composition. It also states (p. 2) that the results apply to *random* repetition, "whereas composition would give linear bounds".
- **E3 against those hypotheses.** E3 is ~12 fixed configurations (LR × steps × batch), σ ∈ {0.5, 1}, n = 8, each run once (RECIPE-01), and **every** configuration's ε is published (RECIPE-02).
  - Hypothesis 1 fails: K = 12 is fixed.
  - Hypothesis 2 fails: it is a grid, not uniform random draws.
  - Hypothesis 4 fails: all outputs are released, not the best one.
  - Hypothesis 3 needs the worst ε over σ ∈ {0.5, 1} and over T. It could be satisfied, but that is moot.

  **Verdict: the finer method does not apply. Only basic composition, with `selection_accounted = false`.** No worked-example test of Papernot–Steinke is required. If one were wanted, Corollary 3 with η = 0 (2ε) and η = 1 (3ε) is hand-checkable.
- **Basic composition worked example** (the D-12 test), using `phase25_epsilon.curve_total`:
  - `curve_total([1.5, 2.25, 0.25], delta=1e-5)` returns `(4.0, 3.0000000000000004e-05)`, measured.
  - The total δ is `len × δ` in float, **not** the literal `3e-05`. The test must compare against `3 * 1e-5` or use `math.isclose`.
  - A grid-shaped example: 6 × 519.6981942303134 (the v4.0 σ = 0.5, T = 200 ε) + 6 × 159.44148628736576 (σ = 1) gives `(4074.8380831060754, 0.00012000000000000002)`.

## Architecture Patterns

### Data flow
```
Phase 35 (now, CPU)                                 later phases
-------------------                                 ------------
closed pins (by reference / lazy) ──┐
results/phase26_canary.json ────────┼─> phase35_prereg ──> V6_RESULT_PATHS ─> ARTIFACT_PATHSPECS
git:<first-add of phase23_run>  ────┘        │                                   │ (ancestry test)
                                              ├─> ENTRIES (D-07)                  ▼
                                              ├─> core rules: seed_list(), e1_targets(),
                                              │     audit02_cut(), e4_runs(), eps_lower_one_run()
                                              └─> SLOTS + fill() ──> scripts/phase{36..45}_prereg.py
                                                                       (fill once, AST-censused,
                                                                        before own records except inputs)
```

### Recommended files
```
scripts/phase35_prereg.py            # the whole core + registry + one-run-audit port (fewest files;
                                     # frozen by one guard). If split, add the split file to a
                                     # _CALL_TIME_SOURCES-style guard (test_phase29_prereg.py:123-142)
tests/test_phase35_prereg.py         # all CPU tests; imports helpers from test_phase29_prereg
.planning/research/V6-PREREG-09.md   # NEW file. Never edit research/SUMMARY.md (phase28_report reads it)
```

### Anti-Patterns to Avoid
- **Typing the four target names, the seed tuple, 3.7965…, F_Y, F_C or K values into the module.** Each must be a rule output, a lazy import, a record read or an attribute binding.
- **Top-level `import phase19_erasure` / `phase26_canary`.** It breaks the torch-free and side-effect-free import.
- **A `.md` holding a value** (D-07).
- **`assert` in the module.** Use `_prove`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ancestry ordering | a new git walker | `test_phase29_prereg._assert_frozen_before` | Already handles the earliest add, the same-commit case and shallow clones |
| Basic composition | `sum(eps)` | `phase25_epsilon.curve_total` | Refuses the None/inf control ε |
| Wilson bounds / z | new CI code | `erasure_gate.wilson_upper_bound`, `phase20_gate_coverage.wilson_lower_bound`, `erasure_gate._Z_ONE_SIDED_95` | Pinned |
| Prose corrections after records exist | edits | `scripts/_addendum.py` (markdown) / a new continuation module (Python) | The ancestry guard is permanent |
| One-run bound | a new derivation | a line-for-line port of App. D (pp. 45–46) | That is what D-11 reproduces |

## Common Pitfalls (repo-specific)

### Pitfall 1: Grep acceptance criteria measure prose
The module's docstring will discuss "selected by THE USER, verbatim", `SEED_LADDER`, `3.7965…` and `torch`. Write every check as an AST gate: `ast.Constant` inside the `ENTRIES`/`SLOTS` dict values, `Import`/`ImportFrom` nodes, `Call` nodes and module-level `Assign` targets. Exclude docstrings and add a non-empty meta-guard so an empty walk cannot pass.

### Pitfall 2: Plans name artifact paths the code refuses
Resolve paths from constants:
- `phase26_canary.RECORD` (lazy) gives `results/phase26_canary.json`;
- the R1a sources are `results/phase19_arm_erased.json` and `results/phase19_noise_floors.json`;
- `PREREG = "scripts/phase35_prereg.py"`.

Every slot `input_records` entry must `fnmatch` some `V6_RESULT_PATHS` entry, and a test checks it. The v6.0 paths are not known in detail yet. Declare concrete names where a slot reads them, and phase globs (`results/phase38_*`) elsewhere. Assert that every entry starts with `results/phase` with a number in 36..45, so the derived pathspecs are exactly `results/phase36_*` … `results/phase45_*`.

### Pitfall 3: The ancestry guard is permanent
Once a `results/phase36_*` file is committed, any commit touching `phase35_prereg.py` reddens the guard forever. Deleting and re-adding cannot launder it, because the guard reads the earliest add. All Phase 35 tasks must land before Phase 36 produces a record, including review fixes. After that, corrections go in a new continuation module (Python) or through `_addendum.py` (markdown). Write `COMMITTED` and `RECORDS_AT_COMMIT = 0` as in phase29.

### Pitfall 4: Execute-phase censuses that bite new files `[VERIFIED: test sources read]`
| Census | Location | Constraint on the new module/test |
|---|---|---|
| ISO-06 `inject_lora` register | `tests/test_lora_inject.py:302` (all `scripts/*.py` + `src`) | Never call `inject_lora` |
| `os.replace` only in `phase25_run.py`/`phase25_record.py` | `tests/test_phase25_driver.py:359` | The module writes nothing; never `os.replace` |
| `== 10` wall | `tests/test_phase21_sc5.py:266` (all `tests/*.py`, comments included) | No `== 10` text anywhere in the new test |
| K menu | `mitigation_gate.ratchet_k`, `K_RUNGS = (48, 24, 16, 8)` | Any K in fixtures/tests must be 8/16/24/48 |
| `mitigation_point_verdict` caller census | `tests/test_phase20_correction.py:1422` | Never import, name-call or define it |
| `privacy_n` via the pin | `tests/test_phase21_unit_continuation.py:83` | Do not reach `mitigation_unit.privacy_n` |
| `retention_perplexity` call sites | `tests/test_phase19_erasure.py:1386` | Do not call it |
| `train_never_taught` / `train_arm(` registers | `tests/test_phase23_ctrl.py:82` + `_TRAIN_ARM_CALL_SITES` | Never define or call |
| `"descriptive_step_mix"` constant | `tests/test_phase30_calibration.py:250` | Do not use that string |
| Clean-tree probes | 11 tests (memory: execute-phase gates) | Run the full suite only on a committed tree |
| Provenance pins `_SUPERSEDED_PINS` | `results/*.json` `module_sha256` | Phase 35 must not edit `teach_persona.py`/`phase30_points.py` (it doesn't need to) |

### Pitfall 5: `config.k` and the 0/14 trap (R1a)
`results/phase19_arm_erased.json::config.k` is 48, not 78, and `per_fact.cand_dog_zorp` is 0/14, not 0/27. Phase 35 cross-checks only what the record supports: `len(ablated_components)`, the destroyed % and the margin. 0/27 and 7/7 are locked as asserted values with `source` = `results/phase19_erasure_report.md:17,146`. Phase 37 owns their routed re-derivation.

### Pitfall 6: The D-05 lock needs full history
`git show <sha>:scripts/phase23_run.py` fails on a shallow clone. Assert `--is-shallow-repository == false` first, as `_assert_frozen_before` does. Derive the commit as the earliest `--diff-filter=A` add of the file, and assert it starts with `5303819` as documentation.

### Pitfall 7: Planning files are frozen inputs
`phase28_report.py` reads `.planning/research/SUMMARY.md`, REQUIREMENTS and ROADMAP live. Put the PREREG-09 note in a **new** file. After any hand edit to STATE/ROADMAP, run `.venv/bin/python scripts/phase28_report.py check` and `scripts/phase34_report.py check`; both exit 0 today, measured. Never use gsd-sdk mutation handlers.

### Pitfall 8: AST `is`-tests are vacuous on small ints and floats
`p.F_Y is mitigation_gate.F_Y` holds today, but so would a retyped literal in some cases. Check the AST binding shape (`Attribute(value=Name(module), attr=name)`), as `tests/test_phase29_prereg.py:1029-1045` does, plus a literal census for `0.7`, `0.5` and `3.7965357228934966` in module code (docstrings excluded).

## Code Examples

### 1. `seed_list()` and its historic lock
```python
# scripts/phase35_prereg.py
def seed_list():
    """THE v6.0 seed list IS phase23_run.SEED_LADDER, by identity (D-05). Lazy: torch at import."""
    import phase23_run  # torch + teach_persona at import — lazy, so this module stays CPU-only

    return phase23_run.SEED_LADDER
```
```python
# tests/test_phase35_prereg.py
def test_seed_ladder_is_unchanged_since_its_first_add():
    import phase23_run  # torch at import — inside the test only

    assert _git("rev-parse", "--is-shallow-repository") == "false"
    first_add = _git("log", "--diff-filter=A", "--format=%H", "--", "scripts/phase23_run.py").split()[-1]
    assert first_add.startswith("5303819")
    tree = ast.parse(_git("show", f"{first_add}:scripts/phase23_run.py"))
    values = [n.value for n in tree.body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == "SEED_LADDER" for t in n.targets)]
    assert len(values) == 1
    assert ast.literal_eval(values[0]) == phase23_run.SEED_LADDER
    assert phase35_prereg.seed_list() is phase23_run.SEED_LADDER
```

### 2. E1 target rule (D-03)
```python
def e1_targets():
    """Rows of the committed ranking at successes == n_questions, in ranking order (D-03)."""
    import phase19_erasure  # torch at import — lazy

    fields = phase19_erasure.TARGET_RANKING_FIELDS
    rows = [dict(zip(fields, r, strict=True)) for r in phase19_erasure.TARGET_RANKING]
    return tuple(r["slot"] for r in rows if r["successes"] == r["n_questions"])
# test: assert e1_targets() == ("pet_name", "cat_name", "street", "sibling_name")  (output, asserted)
```

### 3. AUDIT-02 (D-09)
```python
def audit02_cut():
    """min epsilon_upper over noised points with epsilon_upper >= auditor_ceiling, READ at use."""
    import json
    import phase26_canary  # git_sha() subprocess + accountant at import — lazy

    record = json.loads(phase26_canary.RECORD.read_text(encoding="utf-8"))
    ceiling = record["auditor_ceiling"]
    hits = [p["epsilon_upper"] for p in record["points"].values()
            if p["epsilon_upper"] is not None and p["epsilon_upper"] >= ceiling]
    _prove(hits, "no Phase 26 point is at or above its auditor_ceiling — the AUDIT-02 premise is gone")
    return min(hits)

def e4_runs(one_run_ceiling):
    return one_run_ceiling > audit02_cut()   # strictly greater (AUDIT-02)
```

### 4. One-run bound, stdlib port of App. D (arXiv 2305.08846v1 pp. 45–46)
```python
def _binom_pmf(k, n, q):
    if k < 0 or k > n:
        return 0.0
    if q == 1.0:
        return 1.0 if k == n else 0.0
    return math.exp(math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
                    + k * math.log(q) + (n - k) * math.log1p(-q))

def p_value_one_run(m, r, v, eps, delta):          # Corollary 5.4
    q = 1 / (1 + math.exp(-eps))
    beta = math.fsum(_binom_pmf(k, r, q) for k in range(v, r + 1))
    alpha = acc = 0.0
    for i in range(1, v + 1):
        acc += _binom_pmf(v - i, r, q)
        if acc > i * alpha:
            alpha = acc / i
    return min(beta + alpha * delta * 2 * m, 1)

def eps_lower_one_run(m, r, v, delta, p):           # get_eps_audit: returns eps_min (conservative)
    lo, hi = 0, 1
    while p_value_one_run(m, r, v, hi, delta) < p:
        hi += 1
    for _ in range(30):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if p_value_one_run(m, r, v, mid, delta) < p else (lo, mid)
    return lo
# PIN 1: |eps_lower_one_run(1000, 100, 75, 1e-4, 0.05) - 0.673| < 1e-3   (App. D, p. 46)
# PIN 2: |eps_lower_one_run(100000, 1510, 1439, 1e-5, 0.05) - 2.675| < 1e-3   (§7, p. 28)
```
Validate the inputs with `_prove_count` and `0 <= v <= r <= m`, as App. D's `assert`s do, converted to `_prove`.

## State of the Art

| Old Approach | Current Approach | Impact |
|---|---|---|
| Hundreds of training runs per audit | One run with m independently included canaries (Steinke et al. 2023) | E4 needs one MPS run, but m ≥ 136 fact-level canaries to beat the cut at δ = 1e-5, β = 0.05 |
| Composition over tuning runs | Random-K repetition with log/constant cost (Papernot–Steinke 2022) | Not applicable to a fixed, fully-published grid |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | F_Y/F_C proposer = "Claude Code" (option menu), adopted_by = "Rafael" | Provenance | A PREREG-07 misattribution. Confirm with Rafael before the entry is committed (it becomes permanent). **Moot under D-14:** the proposer field was removed from every entry, so nothing is confirmed or recorded |
| A2 | `seed_list` entry source = `36ab0b4` (35-CONTEXT) + `5303819` | Provenance | Low; the planner can verify by git |
| A3 | Fig. 10's "3.87" uses m = r = 10000 (m not stated, p. 28) | PREREG-09 (a) | None if not pinned (recommended) |
| A4 | Proposed slot names, file names (`V6-PREREG-09.md`) and the `fill()` shape | Slot design | Discretion area; low |
| A5 | E6 subset and E1 alternative ordering stay deferred | Classification | If Rafael wants them locked now, a checkpoint is needed in this phase |

## Open Questions

1. **RESOLVED (D-15).** **Missing slots (six, listed above).** Do they enter the registry now? All six are declared as deferred slots.
   - Recommendation: declare all six as deferred slots. Declaring costs nothing, and an undeclared one becomes unfillable after Phase 35 freezes. Raise `e3_recall_threshold`'s control reading and `e1_condition_b_margin` with Rafael at a plan checkpoint.
2. **RESOLVED (`V6_RESULT_PATHS`, Plan 35-02).** **The v6.0 record names are unknown beyond the slot inputs.** Concrete paths for slot inputs plus one glob per phase.
   - Recommendation: concrete names for slot inputs, phase globs for the rest. The derived pathspecs are then complete regardless.
3. **RESOLVED (deferred to Phases 38/43; not blocking Phase 35).** **Does E4's canary pool have m ≥ 136 independently-randomizable facts?**
   - It is not answerable here (Phase 38 minting, Phase 43). It is flagged so Phase 36 does not price an E4 run that the rule would cut.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python venv | everything | ✓ | 3.11.15 (`.venv`) | — (never the system 3.14) |
| torch (CPU) | lazy imports inside tests only | ✓ | 2.7.1 | — |
| pytest | tests | ✓ | 9.0.3 | — |
| ruff | lint | ✓ | 0.15.16 | — |
| git full history + tag `v5.0` | ancestry, D-05 lock, disjointness | ✓ (local + origin) | 2.50.1 | CI `fetch-depth: 0` already set |
| scipy | — | ✗ | — | not needed (stdlib port) |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 (`pyproject.toml [tool.pytest.ini_options]`, `testpaths = ["tests"]`, `pythonpath = ["."]`) |
| Config file | `pyproject.toml` |
| Quick run command | `.venv/bin/pytest -q tests/test_phase35_prereg.py -p no:cacheprovider` (the phase29 analogue runs in ~20 s) |
| Full suite command | `make test` (≈ 40 min; launch with `nohup` + a `grep '^EXIT='` waiter; Bash caps at 600 s) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PREREG-05 | Prereg first-add precedes every `results/phase36_*`..`45_*` (honest-green now) | git/ancestry | `pytest tests/test_phase35_prereg.py -k frozen_before -q` | ❌ Wave 0 |
| PREREG-05 | `ARTIFACT_PATHSPECS` derived and equal to `results/phase3{6..9}_*`, `results/phase4{0..5}_*`; disjoint from the `v5.0` tag's results | unit | `-k pathspecs` | ❌ |
| PREREG-05 | Six pins imported (AST Import nodes, top-level or in-function), none copied (literal census) | AST | `-k pins_imported` | ❌ |
| PREREG-05 | Module imports without torch / phase19_erasure / phase26_canary / phase23_run (subprocess probe) | smoke | `-k without_torch` | ❌ |
| PREREG-05 | `seed_list() is phase23_run.SEED_LADDER`; first-add AST equals live | git+AST | `-k seed_ladder` | ❌ |
| PREREG-05 | `e1_targets()` equals the 4 names; the names appear in no module `Constant` | unit+AST | `-k e1_targets` | ❌ |
| PREREG-05 | `audit02_cut()` == min over the record (and == 3.7965357228934966); `e4_runs` strict | unit | `-k audit02` | ❌ |
| PREREG-05 | R1a: k = len(ablated_components) = 78; destroyed % re-derives; margin = noise-floor record | unit | `-k r1a` | ❌ |
| PREREG-05 | Slot registry: 4 fields + binding; input records match `V6_RESULT_PATHS`; census checks 1–4 green on the real tree and RED on planted owner files | AST/git | `-k slot` | ❌ |
| PREREG-05 | E2 rule refuses S > len(seed_list()) (D-06) | unit | `-k e2_S` | ❌ |
| PREREG-06 | Every `ENTRIES` value has 6 fields, `kind` ∈ {derived, preference}; F_Y/F_C entries `kind == "preference"` and bound by `Attribute` | unit+AST | `-k entries` | ❌ |
| PREREG-07 | `proposer` ∈ the 3 names, `adopted_by` present, `source` non-empty; the phrase "selected by THE USER, verbatim" absent from entry values (AST over dict Constants, not docstrings) | AST | `-k proposer` | ❌ |
| PREREG-08 | New test has zero skip markers (AST: no `pytest.skip`/`skipif` Call/Attribute); the ubuntu skip pin stays 72 | AST + full suite | `-k no_skips`; full `make test` | ❌ / ✅ (`test_phase25_venue.py`) |
| PREREG-09 | PIN 1 / PIN 2 within 1e-3; δ = 0 closed form within 1e-8; refusals on v > r, r > m, bool | unit | `-k one_run` | ❌ |
| PREREG-09 | Basic composition: `curve_total([1.5, 2.25, 0.25], delta=mitigation_unit.DELTA) == (4.0, 3 * 1e-5)`; `SELECTION_ACCOUNTED is False` | unit | `-k composition` | ❌ |
| PREREG-09 | Research note exists and cites `2305.08846v1`, `2110.03620v2`, "Corollary 5.4", "Theorem 2" (a structural check on a NEW file, acceptable as text since the note is about these terms) | doc | `-k research_note` | ❌ |

### Sampling Rate
- **Per task commit:** `.venv/bin/pytest -q tests/test_phase35_prereg.py tests/test_phase29_prereg.py -p no:cacheprovider`, plus `ruff check . && ruff format --check .`
- **Per wave merge:** the same, plus `scripts/phase28_report.py check` and `scripts/phase34_report.py check` (exit 0)
- **Phase gate:** full `make test` green on a committed tree with skips == the attributed count, before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_phase35_prereg.py`: covers PREREG-05..09; imports `_assert_frozen_before, _git, _module_targets, _numeric_constants, _planted` from `test_phase29_prereg`
- [ ] `.planning/research/V6-PREREG-09.md`: the D-10 note
- No framework install needed

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2/V3/V4 | no | — (offline CPU module, no auth/session) |
| V5 Input Validation | yes | `_prove`/`_prove_count` on every rule input (counts are int-not-bool; slot names ∈ `SLOTS`) |
| V6 Cryptography | no | (SHA-256 provenance belongs to Phase 44; none here) |

| Threat | STRIDE | Mitigation |
|---------|--------|------------|
| Post-hoc re-tune of a threshold after seeing a v6.0 record | Tampering | Ancestry guard over derived pathspecs; slot fills censused and ordered |
| Re-typed constant drifting from its pin | Tampering | `is` + AST binding + literal census, each watched RED on a planted copy |
| A slot filled by an undeclared rule or phase | Elevation | `fill()` single door + AST census (checks 1–3) |
| A record read at use being swapped | Tampering | It is tracked; Phase 26's ancestry guard already freezes `results/phase26_canary.json`'s provenance; the read is `json.loads` only |
| Misattributed provenance | Repudiation | D-07/D-08 fields enforced by test; forbidden phrase census |

## Sources

### Primary (HIGH confidence)
- arXiv:2305.08846v1 (PDF, 46 pp.): Algorithm 1 p. 3; Theorem 2.1 p. 4; Lemma 4.7 pp. 8–9; Proposition 5.1 p. 12; Theorem 5.2 p. 14; Corollary 5.4 pp. 15–16; Proposition 5.7 p. 19; Corollary 5.8 p. 22; §6 p. 25 (k± selection caveat); §7 p. 28 (2.675, 3.87); Appendix D pp. 45–46. https://arxiv.org/abs/2305.08846
- arXiv:2110.03620v2 (ICLR 2022): §3.3 p. 5; Definition 1, Theorem 2 p. 5; Corollaries 3–4 p. 6; Theorem 6, Lemma 7 p. 7; point-mass remark p. 8. https://arxiv.org/abs/2110.03620
- Repo sources read with file:line as cited throughout (phase29_prereg, its test, phase19_erasure, phase23_run, mitigation_gate, phase26_canary/prereg, phase25_epsilon, phase25_prereg, test_phase25_venue, CI workflow)

### Secondary
- `.planning/milestones/v4.0-phases/20-*/20-CONTEXT.md:159-185`, `20-DISCUSSION-LOG.md:189-208` (F_Y/F_C origin)
- Project memory: execute-phase gates, grep criteria, pin corrections, misnamed artifacts

### Tertiary
- None used for any threshold.

## Metadata
**Confidence breakdown:**
- Standard stack: HIGH. Everything is reused and verified in code.
- Architecture: HIGH for the precedent. MEDIUM for the slot-census design (new, but built from verified parts).
- PREREG-09: HIGH. Read at the source, reproduced numerically.
- Pitfalls: HIGH. Each census was located in the test sources.

**Research date:** 2026-10-01
**Valid until:** the first `results/phase36_*` commit (after that the prereg is frozen), or 30 days
