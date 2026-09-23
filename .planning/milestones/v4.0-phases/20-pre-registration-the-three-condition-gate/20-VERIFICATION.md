---
phase: 20-pre-registration-the-three-condition-gate
verified: 2026-08-21T21:31:19Z
status: passed
score: 7/7 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 5/6
  gaps_closed:
    - "ROADMAP SC3's GATE-06 Y clause — both Y sweep legs now carry a per-element `[0.0, 1.0]` `_prove` placed before the `x_uppers` comprehension. RE-MEASURED IN MY OWN PROCESS: `(nan, 0.28)` now raises SystemExit naming the leg and its `[0.0, 1.0]` requirement where it previously returned PASS with `coverage_verdict (True, (), None)`; the honest `(0.30, 0.28)` still reaches an INCONCLUSIVE finding naming `heldout_recall`. 42.0 / -99.0 refused on BOTH legs; bools still admitted on the recall legs by design."
    - "20-12's `threats_open: 0` must-have — `_prove_retention_floor` gained a FIFTH `_prove`, the D-38 magnitude bound `retention_noise_floor <= _MAX_ADMISSIBLE_RETENTION_FLOOR` (derived, never typed). RE-MEASURED: the one-ULP nudge `0.06893*(1+2**-50)` now raises by MAGNITUDE, `5.0` under clean adapter provenance raises by MAGNITUDE, the unperturbed `0.06893` still raises by IDENTITY first, and the governing floor `0.008681618994239138` read from `results/phase20_retention_floor.json` is still ADMITTED — so the bound is not vacuous."
    - "T-20-19 re-opened at `72ef455` (`status: blocked` / `threats_open: 1`) and re-closed at `7ffeee3` — distinct commits four plans apart, per D-39. The row is APPEND-ONLY: the HEAD row starts with the 20-13 body verbatim, which itself contains the 20-12 body verbatim."
  gaps_remaining: []
  regressions:
    - "None. `git diff --exit-code cc99321 -- scripts/mitigation_gate.py scripts/erasure_gate.py` returns 0, and so does the same diff against the original pin commit `7e6de4b` — the pin is byte-identical across two full correction waves. Full suite `877 passed, 1 skipped` on a clean tree; `ruff check` + `ruff format --check` clean. Test-count arithmetic reconciles exactly: 874 -> 876 (20-14, +2) -> 876 (20-15, +0) -> 877 (20-16, +1), and `git diff` shows exactly three new `def test_` functions."
deferred:
  - truth: "RPT-02's second half — the prose-search helper is USED for correction sweeps, not merely committed"
    addressed_in: "Phase 25"
    evidence: "REQUIREMENTS.md:313 records the deferral explicitly and leaves the box `[ ]` unchecked: 'routing doc-consistency checks through `normalized` belongs to the phase that runs the first correction sweep.' Phase 25 is 'Frontier Sweep and the Existence-Gate Verdict'; Phase 28's SC also consumes `_prose.normalized` (RPT-01). The first half IS shipped (`scripts/_prose.py::normalized`, `ac4d781`)."
  - truth: "GC-05, GC-07, GC-08, GC-09, GC-10, GC-11, GC-12 — review-grade residuals from the gap-closure code review"
    addressed_in: "Not scheduled — published as open rather than absorbed"
    evidence: "results/phase20_gate_coverage_correction.md:377-381 names every one of them as NOT closed by this wave-set, and 20-SECURITY.md T-20-82 exists specifically to refuse 'a continuation implying a completeness it did not achieve'. I read all seven: none touches a must-have or a verdict. GC-10's `z`-default concern cannot affect any verdict — `wilson_lower_bound` is defined but read by nothing in `coverage_verdict` (measured: 0 occurrences in the axis loop)."
human_verification: []
---

# Phase 20: Pre-Registration — The Three-Condition Gate — Verification Report

**Phase Goal:** "Every rule that will judge a v4.0 number is committed to git before any v4.0 number
of any kind exists — including before the cost calibration" (ROADMAP.md)
**Verified:** 2026-08-21T21:31:19Z
**Status:** passed
**Re-verification:** Yes — third pass, after gap-closure wave 2 (plans 20-13 … 20-17)

---

## Bottom line

**Both gaps are closed, and I closed the question by running the code rather than by reading it or
the SUMMARYs.** Seventeen direct probes against the two defect classes returned 17/17 as required.
Six guard-neutering breaks, applied and observed in my own process, each reddened exactly the guard
the record names — and every one restored byte-identically under `shasum -a 256`.

The previous verification's two findings were sharp and specific. Both are now refused by
**property** where they were previously refused by **name** or not at all:

| What the previous verification measured | What I measure at HEAD |
|---|---|
| `(nan, 0.28)` on a strictly-more-truncated held-out axis returned **`PASS`** with no GATE-06 reason, while the honest `(0.30, 0.28)` returned `INCONCLUSIVE` | `(nan, 0.28)` raises `SystemExit` naming the held-out leg and its `[0.0, 1.0]` requirement. `(0.30, 0.28)` still returns `INCONCLUSIVE` naming `heldout_recall`. The flip is gone. |
| `0.06893 * (1 + 2**-50)` passed the `!=` and bought a **bit-identical `4.029`** | Refused by MAGNITUDE. The message names the admissible ceiling. The unperturbed `0.06893` still hits the IDENTITY refusal FIRST, so the three published numbers still appear. |
| `retention_noise_floor=5.0` with clean provenance reached **`PASS`** at cap `13.89114` | Refused by MAGNITUDE, with no malformed input anywhere. |
| — | **And the bound is not vacuous:** the governing floor `0.008681618994239138`, read from `results/phase20_retention_floor.json`, is still ADMITTED. So is a floor half that size. `governing * (1+1e-6)` is refused. |

**The thing I was most prepared to find, and did not.** A one-sided magnitude bound is the easiest
place in this phase to buy a green by making the bound vacuous in the other direction — refuse
everything, admit nothing, and every tripwire passes. That is not what happened. I probed the
admissible side explicitly (governing floor, half the governing floor, `governing*(1+1e-9)`) and all
three are admitted; the refusal boundary sits between `1e-9` and `1e-6` relative, exactly where the
named constant puts it. The tolerance is additionally **pinned** by a committed assertion that the
ceiling must stay *below* the fabricated fixture floor `0.009` — so the one widening D-41 forbids
is now a test failure, not a judgment call. I broke that pin and watched it redden.

**The divergence 20-17 published is honest, and I reproduced both halves of it.** Widening the
tolerance `1e-9 → 0.05` reddens **two** tests at HEAD where 20-15 recorded one. 20-17 attributed the
extra failure to a guard 20-16 added afterwards. That attribution holds under measurement: the
`relative_tolerance` / `admissible_ceiling` assertions inside
`test_every_published_number_re_derives_from_the_modules` are absent at `a132292` (20-15's last
commit) and present at `001138d` (20-16's first). A phase that publishes a count that disagrees with
its own prior record, then correctly explains why, is doing the thing this phase exists to do.

**Proportion.** The residuals this phase did not close (GC-05, GC-07, GC-08…GC-12) are published in
the correction artifact under a heading that says so, and `20-SECURITY.md`'s T-20-82 exists to refuse
exactly the alternative. I read all seven; none touches a verdict or a must-have. The record is, if
anything, now *conservative*: T-20-78 still describes the GC-07 drift catch as one-directional, and I
measured that 20-16's payload coupling has since made it bidirectional.

---

## Goal Achievement

### Observable Truths

Must-haves carried forward from the previous verification: the six ROADMAP Success Criteria, plus the
20-12 plan must-have that the previous gap 2 was filed against. Truths 3 and 6 receive full
re-verification; the rest receive a regression check.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 0 | **The goal sentence** — every rule committed before any v4.0 number of any kind exists | ✓ VERIFIED | `git diff --exit-code cc99321 -- scripts/mitigation_gate.py scripts/erasure_gate.py` → 0, and the same against the original pin `7e6de4b` → 0. The pin is byte-identical across **two** correction waves. Ancestry re-measured: three `results/phase20_*` first-adds (`9bb34ad` 2026-08-20 19:37:56, `4e4d5ef` 12:18:24, `2a32394` 12:22:25) all follow the last pin commit `abf9072` (2026-08-20 17:43:17). Scope note carried forward at truth 5. |
| 1 | **SC1** — three conditions, keyword-only no defaults, reason strings; (c)'s caps computed from imported constants | ✓ VERIFIED | Regression: 18/18 `test_phase20_prereg.py` green, pin unchanged. D-06 amendment intact; `_GOVERNING_CAP` re-derived by calling the frozen `retention_cap`, measured `3.9085032379884783`. |
| 2 | **SC2** — Y is a pair, a locked fraction of the retrained control, never v2.0's 0.4921 / 0.3483 | ✓ VERIFIED | Regression: exact-equality import assertion green. Measured `F_Y = 0.7`; both legs computed from their own controls. |
| 3 | **SC3 (as amended by D-34/D-37)** — every branch watched firing; GATE-05 precedence; a sweep that never crossed X **or Y** returns INCONCLUSIVE not FAILURE; arm identity; provisional until replicated | ✓ **VERIFIED (was FAILED)** | **X: closed, unchanged.** `coverage_verdict` computes `wilson_upper_bound(k,n)` per point and compares each axis on its criterion's own direction. **Y: now closed behaviourally.** Per-element `_prove` at `:248-268` on BOTH legs, placed before the `x_uppers` comprehension. Measured 8 ways (G1-a…G1-h below). BREAK A watched RED. |
| 4 | **SC4** — the n=8-vs-n=64 capacity rule committed before either run, both branches publishable | ✓ VERIFIED | Regression: `_CAPACITY_DISPATCH` totality proved at import; guard green. |
| 5 | **SC5** — per-point K, full-fidelity K, promotion rule committed before the first v4.0 artifact; CPU-only ancestry test; `_prose.normalized` differential | ✓ VERIFIED | Regression: `test_phase20_prereg_is_frozen_before_every_phase20_result` green over three artifacts × nine pin commits. `_prose.py` untouched by wave 2. |
| 6 | **20-12 plan must-have** — `20-SECURITY.md` reaches `threats_open: 0` with each closure pointing at a **watched guard**, never at a plan; GATE-02's residual discharged by a choke point that refuses a borrowed retention floor | ✓ **VERIFIED (was FAILED)** | The magnitude bound makes the refusal a property. Measured 9 ways (G2-a…G2-i). BREAK B and BREAK C watched RED. Register re-counted from its own tables: **84 distinct `T-20-NN` ids, 57 row-starts, 0 rows at Status `open`**, `### Open` reads `None.` |

**Score: 7/7 truths verified**

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | RPT-02's second half — `normalized` *used for* correction sweeps | Phase 25 | REQUIREMENTS.md:313 records the deferral and leaves `[ ]` unchecked; Phase 25 is the first sweep phase. First half shipped at `ac4d781`. |
| 2 | GC-05, GC-07, GC-08…GC-12 | Not scheduled — published as open | `results/phase20_gate_coverage_correction.md:377-381`; T-20-82 refuses absorbing them silently. None touches a verdict or a must-have. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/mitigation_gate.py` | The frozen pin, unedited | ✓ VERIFIED FROZEN | `git diff --exit-code` 0 against both `cc99321` and `7e6de4b`. Two correction waves, zero bytes moved. |
| `scripts/erasure_gate.py` | v3.0's closed pin, unedited | ✓ VERIFIED FROZEN | Same diff, same result. |
| `scripts/phase20_gate_coverage.py` | The governing correction — with both wave-2 guards | ✓ VERIFIED | 699 lines. Y-leg range `_prove` at `:248-268`; count guard by type at `:278`; `_MAX_ADMISSIBLE_RETENTION_FLOOR` at `:396-398`; the fifth `_prove` at `:481-502`, placed AFTER the `!=` so the identity message still fires first (measured: G2-c returns the IDENTITY message, G2-a the MAGNITUDE one). No stub shapes; no `return None`/`{}`/`[]` placeholder anywhere. |
| `tests/test_phase20_correction.py` | The armed tripwires | ✓ VERIFIED | 1473 lines, 14 tests. Three new functions this wave. Every guard I broke reddened exactly the named test. |
| `tests/test_phase20_prereg.py` | The pin's own suite + ancestry guard | ✓ VERIFIED | 1368 lines, 18 tests, untouched by wave 2, all green. |
| `results/phase20_gate_coverage_correction.json` | Second correction, additively | ✓ VERIFIED | `value_guards` block added; `defects` grew CR-01/T-20-19/WR-08/WR-09 → +GC-01/02/03/04/06. **Measured strictly additive:** no pre-existing defect entry changed or removed. |
| `results/phase20_gate_coverage_correction.md` | The second D-24 dated continuation | ✓ VERIFIED | `git diff --numstat 2a32394 HEAD` → **152 insertions, 0 deletions**. Two dated `## Addendum` headings. |
| `.planning/.../20-SECURITY.md` | `threats_open: 0`, each closure evidenced, T-20-19 arc intact | ✓ VERIFIED | 84 distinct ids / 57 row-starts / 0 open. T-20-67…T-20-84 each present as its own row-start (18/18). Append-only proved by prefix match, not by eye. |
| `.planning/REQUIREMENTS.md` | All 12 IDs accounted for | ✓ VERIFIED | See Requirements Coverage. GATE-02's falsified clause corrected **in place** (the right call — a superseded *number* stays visible, a falsified *claim* does not). |
| `.planning/ROADMAP.md` | Wave-2 plan list, amendments byte-preserved | ✓ VERIFIED | Diff is +24/-2, the −2 being only the `**Plans**:` count line. Both amendment blockquotes untouched. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `coverage_verdict` | both Y legs | one body, one rule, **and one per-element value guard** | ✓ WIRED | The previous "HOLLOW FINDING" is closed. Measured: the guard fires on NaN, 42.0 and −99.0, on BOTH legs, and does not move the honest finding. |
| `corrected_point_verdict` | `_prove_retention_floor` | called FIRST, before any compute | ✓ WIRED, **SUFFICIENT** | The previous "INSUFFICIENT" is closed. `5.0` no longer passes. All ten refusals are driven *through the route*, so the claim proved is reachability, not helper existence. |
| `_MAX_ADMISSIBLE_RETENTION_FLOOR` | `_ADAPTER_REGIME_RETENTION_FLOOR` | derived, never typed | ✓ WIRED | `0.008681619002920757 = 0.008681618994239138 × (1 + 1e-9)`, re-derived in my process. |
| module bound | published payload | `test_every_published_number_re_derives_from_the_modules` | ✓ WIRED | Payload `admissible_ceiling` / `relative_tolerance` asserted equal to the module's. This is also what now catches a GC-07 drift. |
| AST caller census | aliased imports | `ast.ImportFrom` walk + synthetic non-vacuity control | ✓ WIRED | The previous GC-06 blind spot is closed for the import form. **Measured by planting a real bypass** (BREAK E): the census went RED naming `scripts/_verifier_bypass_probe.py:1 (imported as mpv)`. Residual `getattr`-dispatch and out-of-scope-dir forms are recorded as open in the test's own docstring. |
| `phase20_gate_coverage.py` | `erasure_gate.wilson_upper_bound` | import by object identity | ✓ WIRED | Imported, not redefined. |
| ancestry guard | `results/phase20_*` | `git log --diff-filter=A` | ✓ WIRED | 3 artifacts × 9 pin commits, all first-adds after the last pin commit. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `coverage_verdict` extraction axis | `x_uppers` | `wilson_upper_bound(k,n)` over type-validated counts | Yes — count guard now enforced by type | ✓ FLOWING |
| `coverage_verdict` taught axis | `sweep_taught_recalls` | caller, **now range-validated** | Yes — NaN/out-of-range refused | ✓ FLOWING |
| `coverage_verdict` held-out axis | `sweep_heldout_recalls` | caller, **now range-validated** | Yes — the manufactured bracket is refused | ✓ FLOWING |
| `_prove_retention_floor` | `retention_noise_floor` | caller + provenance **+ magnitude bound** | Yes — looser class refused, governing floor admitted | ✓ FLOWING |
| test harness | `DEFAULT_RETENTION_FLOOR` | **read** from `results/phase20_retention_floor.json` | Yes — not retyped | ✓ FLOWING |
| `_ADAPTER_REGIME_RETENTION_FLOOR` | module constant | **retyped** from the same artifact (GC-07) | Yes at HEAD; drift now caught in both directions via the payload coupling | ✓ FLOWING (see INFO-3) |

### Behavioral Spot-Checks

All run in my own process with `.venv/bin/python` against the committed tree. `coverage_verdict`
returns a **3-tuple** `(bool, tuple, str|None)` — confirmed, not assumed.

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full suite, clean tree | `.venv/bin/python -m pytest -q` | `877 passed, 1 skipped in 193.79s` | ✓ PASS |
| Phase-20 twins | `pytest tests/test_phase20_correction.py tests/test_phase20_prereg.py -q` | `32 passed in 1.92s` | ✓ PASS |
| Lint | `ruff check .` / `ruff format --check .` | `All checks passed!` / `176 files already formatted` | ✓ PASS |
| Pins frozen | `git diff --exit-code cc99321 -- mitigation_gate.py erasure_gate.py` | exit 0 | ✓ PASS |
| Pins frozen since origin | `git diff --exit-code 7e6de4b -- …` | exit 0 | ✓ PASS |
| **G2-a** nudged borrowed floor | `_prove_retention_floor(0.06893*(1+2**-50), clean)` | `SystemExit` — "is LOOSER than the governing adapter-regime floor" | ✓ PASS |
| **G2-b** looser floor, clean provenance | `_prove_retention_floor(5.0, clean)` | `SystemExit` — MAGNITUDE | ✓ PASS |
| **G2-c** unperturbed borrowed | `_prove_retention_floor(0.06893, clean)` | `SystemExit` — "IS 0.06893" (IDENTITY fires first, ordering preserved) | ✓ PASS |
| **G2-d** governing floor from the artifact | `_prove_retention_floor(0.008681618994239138, clean)` | `None` — **ADMITTED**, bound not vacuous | ✓ PASS |
| **G2-e** a tighter floor (half governing) | same, `/2` | `None` — admitted | ✓ PASS |
| **G2-f** `governing*(1+1e-9)` | round-trip edge | `None` — admitted | ✓ PASS |
| **G2-g** `governing*(1+1e-6)` | clearly looser | `SystemExit` — MAGNITUDE | ✓ PASS |
| **G2-h / G2-i** wrong regime / single seed | provenance cases | `SystemExit` each, correct message | ✓ PASS |
| **G1-a** honest truncated held-out | `coverage_verdict(heldout=(0.30,0.28))` | `(False, ('taught_recall','heldout_recall'), '…')` — a finding | ✓ PASS |
| **G1-b** the flip | `heldout=(nan, 0.28)` | `SystemExit` naming the leg + `[0.0, 1.0]` | ✓ PASS |
| **G1-c / G1-d** out of range | `42.0` / `-99.0` | `SystemExit` each | ✓ PASS |
| **G1-e** taught leg NaN | `taught=(nan, 0.30)` | `SystemExit` naming the taught leg | ✓ PASS |
| **G1-f** genuinely bracketed held-out | `heldout=(0.30, 0.20)` | `(False, ('taught_recall',), …)` — held-out no longer truncated | ✓ PASS |
| **G1-g** rate-space sentinel as counts | `successes=(0.0, 1.0)` | `SystemExit` naming RATE and COUNT | ✓ PASS |
| **G1-h** bools as recalls | `heldout=(True, False)` | admitted **on purpose**, per the documented asymmetry | ✓ PASS |

**17/17 as required, 0 deviations.**

### Probe Execution

No `scripts/*/tests/probe-*.sh` exists in this repository and no PLAN declares one. The runnable
equivalents are the pytest twins and the guard-neutering breaks, all executed in my own process.

| Probe | Command | Result | Status |
|-------|---------|--------|--------|
| Gap re-measurement suite (17 cases) | `.venv/bin/python probe_gaps.py` | 17/17 as required | PASS |
| Phase-20 behavioural twins | `pytest tests/test_phase20_{correction,prereg}.py -q` | `32 passed` | PASS |
| Whole-repo regression | `pytest -q` | `877 passed, 1 skipped` | PASS |

### Watched-RED Re-Application (my own process, not transcribed)

Every break was applied by me, run by me, and restored with `shasum -a 256` equality asserted.
Worktree verified clean afterwards (`git diff --exit-code` → 0).

| # | Break | Expected to redden | Observed | Restored |
|---|-------|--------------------|----------|----------|
| A | Y-leg range `_prove` → `True` | `test_a_recall_outside_the_unit_interval_cannot_manufacture_y_coverage` | `E Failed: DID NOT RAISE <class 'SystemExit'>` at `:486`. **`1 failed, 31 passed`** | ✓ sha256 equal |
| B | fifth `_prove` neutered | `test_the_retention_floor_tripwire_is_the_only_route_to_a_verdict` | `DID NOT RAISE` at `:1191`, reached from `:1252`, frame carrying `{'retention_noise_floor': 0.06893000000000006}`. **`1 failed, 31 passed`** | ✓ sha256 equal |
| C | tolerance `1e-9 → 0.05` | the tolerance pin **and** the payload coupling | `E assert 0.009115699943951094 < 0.009` at `:1270`, **plus** `test_every_published_number_re_derives_from_the_modules`. **`2 failed, 30 passed`** — reproduces 20-17's published divergence | ✓ sha256 equal |
| D | count guard → old integral-float acceptance | `test_the_modules_own_rate_space_sentinel_cannot_pass_as_counts` | `DID NOT RAISE` at `:546`. **`1 failed, 31 passed`** | ✓ sha256 equal |
| E | aliased-import bypass planted in `scripts/` | the AST caller census | `AssertionError: 1 call site(s) or import(s) … ['scripts/_verifier_bypass_probe.py:1 (imported as mpv)']` | ✓ probe file removed |
| F | `_ADAPTER_REGIME_RETENTION_FLOOR` drift (simulated **in memory**, repo untouched) | GC-07's stated blind spot | Under the drift `0.04` becomes admitted — but the payload coupling at `:968` reddens, so the drift IS caught. See INFO-3. | ✓ no files modified |

**On break C — the divergence, independently attributed.** 20-17 published `2 failed` where 20-15
recorded `1 failed`, attributing the difference to a guard 20-16 added afterwards. I checked the
attribution rather than accepting it: `relative_tolerance` and `admissible_ceiling` appear **0 times**
in `tests/test_phase20_correction.py` at `f163b1c`, `763fc36`, `9b010c8` and `a132292` (all of
20-15), and **1 / 2 times** from `001138d` (20-16) onward. The attribution holds exactly.

### Requirements Coverage

Plan-declared IDs across all 17 plans == REQUIREMENTS.md's Phase-20 mapping == the twelve IDs in the
task brief. **Zero orphans, zero unclaimed.**

| Requirement | Source Plan(s) | Status | Evidence |
|-------------|----------------|--------|----------|
| GATE-01 | 20-01/02/04/06 | ✓ SATISFIED | `[x]` + note. Three-name domain proved at import; AST-proved keyword-only across all public functions. |
| GATE-02 | 20-01/04/06/07/08–12, **20-13/15/16/17** | ✓ **SATISFIED (residual now genuinely closed)** | `[x]` + D-36 amendment + the D-38 amendment added at 20-16. The falsified "caught by the number itself" clause was corrected **in place** and the stale refusal count re-counted at runtime (`eight` → **ten**). I measured the discharge: NAME by identity, CLASS by magnitude, governing floor admitted. |
| GATE-03 | 20-04, 20-06 | ✓ SATISFIED | `y_taught` / `y_heldout` pair; both read by condition (b). |
| GATE-04 | 20-04, 20-06 | ✓ SATISFIED | Each leg `F_Y ×` its own control; `0.4921`/`0.3483` AST-absent; import list asserted by exact equality. |
| GATE-05 | 20-04, 20-06 | ✓ SATISFIED | Early return before any reason appended; watched differentially. |
| GATE-06 | 20-04/06/08/10/11/12, **20-13/14/16/17** | ✓ **SATISFIED (Y half now behavioural)** | `[x]` + the D-40 amendment, which states plainly that the Y half was STRUCTURAL and not yet BEHAVIOURAL when the row was first written, publishes the measured `(nan, 0.28) → PASS` defect at `576b57d`, and names its closure at 20-14 with both guards. I re-measured the closure 8 ways. |
| GATE-07 | 20-01, 20-05, 20-06 | ✓ SATISFIED | 3-tuple carries `arm`; mixed-arm list aborts. |
| GATE-08 | 20-04, 20-05, 20-06 | ✓ SATISFIED | INCONCLUSIVE over a would-be PASS; one `REPLICATION_PENDING_MARKER`. |
| GATE-09 | 20-05, 20-06 | ✓ SATISFIED | Six outcomes fired; fixture asserted against the parsed Phase 19 artifact. |
| GATE-10 | 20-05, 20-06 | ✓ SATISFIED | `_CAPACITY_DISPATCH` totality proved at import; D-26 fallback raises. |
| CAL-04 | 20-01/05/06/07 | ✓ SATISFIED | `K_RUNGS` + `ratchet_k` + `promote_to_full_fidelity` precede the first artifact. ℹ️ Its traceability note is still a five-word stub (INFO-1). |
| RPT-02 | 20-03, 20-06 | ⚠️ **DEFERRED BY DESIGN** | Correctly `[ ]`. First half shipped; second half recorded as Phase 25 work in REQUIREMENTS.md rather than only in a SUMMARY. See Deferred Items. |

### Anti-Patterns Found

**Debt-marker gate: CLEAN.** Zero `TBD` / `FIXME` / `XXX` in any file wave 2 touched.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | `TBD` / `FIXME` / `XXX` | — | **None** |
| `results/…correction.md`, `tests/test_phase20_correction.py` | various | the word "placeholder" | ℹ️ Info | Prose about the *document's* pointer marker in the addendum mechanism, not a code stub. Verified by reading each of the 6 hits. |
| `.planning/REQUIREMENTS.md` | 312 | CAL-04's traceability note is a five-word stub — the only one of twelve that names neither a function nor a guard | ℹ️ **INFO-1** | Cosmetic; carried forward unfixed from the previous verification. The underlying discharge is verified. |
| `scripts/phase20_gate_coverage.py` | 493-495 | "any TIGHTER floor a later phase measures is admitted unchanged, **so a real re-measurement is never blocked**" | ℹ️ **INFO-2** | The inference holds only if re-measurements are always tighter. A legitimately *looser* re-measurement IS blocked and would need an edit to this (unpinned, editable) module. One word of over-claim in an otherwise scrupulous message. The mechanism is correct and conservative; only the sentence overstates. |
| `20-SECURITY.md` | 236 (T-20-78) | "the catch is ONE-DIRECTIONAL — a drift making the module constant LOOSER is not caught" | ℹ️ **INFO-3** | **Now conservative rather than wrong.** True when written at 20-15; 20-16's payload coupling has since made the catch bidirectional. Measured: under a looser drift the module computes `0.05000000005000001` against the payload's `0.008681619002920757`, so `test_every_published_number_re_derives_from_the_modules` reddens. Understating one's own coverage is against interest and harmless. |
| `scripts/phase20_gate_coverage.py` | 124 | GC-10 — `z` default captured by value, docstring says "BY REFERENCE" | ℹ️ Info | Cannot affect any verdict: `wilson_lower_bound` is defined but read **zero** times by `coverage_verdict` (measured). Published as open. |
| — | — | GC-05, GC-07, GC-08…GC-12 | ℹ️ Info | All published as NOT closed in the correction artifact. I read all seven; none touches a must-have. |

No stub patterns. Every `return` computes. No empty handler, no hardcoded-empty prop, no `return
null` shape in either file.

---

## Did wave 2 close the two gaps?

**Gap 1 — the Y-leg value guard. YES.** The previous verification prescribed a per-element range
`_prove` "which is False for NaN so it subsumes the NaN case", a tripwire asserting the measured
differential, and a count guard enforced by type. All three landed, and all three bite. The range
check is written exactly as prescribed and its refusal message explains the *mechanism* (`nan >=
criterion` is False → counted as a failing point → manufactures the bracket) rather than merely
asserting a rule. The tripwire is a differential in one body: the honest reading must still reach
INCONCLUSIVE **and** the NaN must raise, so neither half can go stale alone. The one deliberate
asymmetry — bools admitted on the recall legs, refused on the count leg — is argued at both sites and
measured correct in both directions.

**Gap 2 — the retention floor's magnitude bound. YES, and it is the stronger of the two closures.**
The previous verification offered a choice: accept the asymmetry in writing, or take the one-line
property bound. Wave 2 took the bound — the option that, in the previous verifier's own words,
"makes the ordering question moot, because a property bound authored after the measurement still
cannot be tuned toward a favourable answer." That reasoning is now backed by a mechanism rather than
resting on an argument: the *only* direction a tuner could move this ceiling is up, D-41 rejected
exactly that widening in writing, and the tolerance pin at `:1270` turns the rejection into a test
failure. I broke the pin and watched it redden. The ordering is also load-bearing and preserved: the
`!=` still fires first on the named value, so the three published numbers that make the refusal an
*argument* still appear.

**The register's arc is honest.** T-20-19 went OPEN at `72ef455` before the fix existed, and RE-CLOSED
at `7ffeee3` after — distinct commits four plans apart, per D-39. The row is append-only, and I
proved that by prefix match rather than by eye: the HEAD row *starts with* the 20-13 body verbatim,
which itself *contains* the 20-12 body verbatim. Nothing was rewritten over anything.

**What I checked hardest and could not falsify.** The obvious way to fake this closure is a vacuous
bound. It is not vacuous — the governing floor is admitted, tighter floors are admitted, and the
refusal boundary sits exactly where the named constant puts it. The second obvious fake is a tripwire
that raises for the wrong reason. It does not — the tests assert *which* refusal fired (`assert f"IS
{V20_RETENTION_NOISE_FLOOR}" not in message`), so merging the two guards into one would redden. The
third is a census that returns empty because its matcher is broken. It is not — there is a synthetic
non-vacuity control, and I planted a real bypass and watched it caught.

---

## Gaps Summary

**None.** Both previously-failing must-haves are closed by mechanism, verified by execution in this
verifier's own process rather than by reading SUMMARY.md or the code. The pre-registration survived
two correction waves byte-identically. The register reconciles to its own rows under its own binding
counting method. The published artifacts are provably additive. Every requirement ID carries state,
with the single unchecked one (RPT-02) correctly unchecked and its deferral recorded in
REQUIREMENTS.md rather than only in a SUMMARY.

Three INFO-grade observations are recorded above; none fails a must-have and none blocks Phase 21.
INFO-3 is a case of the record *understating* its own coverage, which is the safe direction.

The phase's own trust boundary — *"a plan that says a thing will be done ↔ a guard that proves it
was"* — is satisfied on both legs, and it is satisfied because the guards were re-run and re-broken,
not because a SUMMARY said so.

---

_Verified: 2026-08-21T21:31:19Z_
_Verifier: Claude (gsd-verifier) — goal-backward, FORCE stance, re-verification (third pass)_
