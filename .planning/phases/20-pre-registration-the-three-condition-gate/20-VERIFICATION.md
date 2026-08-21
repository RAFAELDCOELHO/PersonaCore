---
phase: 20-pre-registration-the-three-condition-gate
verified: 2026-08-21T16:53:03Z
status: gaps_found
score: 5/6 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 5/6
  gaps_closed:
    - "Every phase-20 requirement ID is accounted for as complete, explicitly deferred, or genuinely unmet — all 12 IDs now carry state in REQUIREMENTS.md; 11 checked with function+guard traceability notes, RPT-02 unchecked with its Phase 25 deferral recorded"
    - "CR-01's extraction half — coverage_verdict decides the extraction axis on wilson_upper_bound(k, n), the same statistic condition (a) reads. Both reproduced directions now armed as pin-vs-correction differentials (tests/test_phase20_correction.py:174, :229), 29/29 phase-20 tests green"
    - "The four prescribed remediation artifacts all landed: results/phase20_gate_coverage_correction.json with governs/supersedes, the D-24 dated continuation .md appended via scripts/_addendum.py with an additivity guard, the armed tripwire file, and a recorded WR-09 decision (D-35 — corrected, not accepted)"
  gaps_remaining:
    - "SC3's GATE-06 clause on the Y axes — WR-09 is closed as a PARAMETER but its coverage finding is manufacturable; measured differential flips a genuinely truncated held-out axis from INCONCLUSIVE to PASS"
  regressions:
    - "None in previously-passing truths. scripts/mitigation_gate.py and scripts/erasure_gate.py byte-identical (git diff --exit-code returns 0); ancestry guard strengthened 1->3 artifacts x 9 pin commits; 874 passed / 1 skipped; ruff check + format clean"
gaps:
  - truth: "ROADMAP SC3 (as amended by D-34/D-37) — a sweep that never produced points on both sides of X (or of Y) returns INCONCLUSIVE rather than FAILURE, read through coverage_verdict / corrected_point_verdict"
    status: partial
    reason: >-
      The X half is genuinely closed and armed. The Y half is closed structurally (the missing
      sweep_heldout_recalls parameter now exists and both legs are decided in one body) but not
      behaviourally: the two Y legs are validated for LENGTH ONLY, so a coverage finding on either
      leg can be produced by the input rather than by the data. Measured differential on the same
      genuinely-truncated axis, against Y_heldout = 0.24499999999999997 — sweep (0.30, 0.28) returns
      INCONCLUSIVE with a GATE-06 reason (correct); sweep (nan, 0.28), which is STRICTLY MORE
      truncated, returns PASS with NO GATE-06 reason. `nan >= criterion` is False so the NaN is
      counted as a FAILING point, manufacturing the bracket. `42.0` and `-99.0` are likewise
      accepted as recalls. This is direction (ii)'s false-coverage defect class reappearing on the
      exact axis WR-09 exists to cover, and it reaches a spurious PASS — the direction the previous
      verification certified the frozen pin could not produce.
    artifacts:
      - path: "scripts/phase20_gate_coverage.py"
        issue: >-
          :241-247 validates sweep_taught_recalls / sweep_heldout_recalls for length only; :296-297
          consumes their values raw. The extraction axis on the same function gets three per-element
          _prove calls (:248-277) justified at :274-276 on the grounds that "a coverage finding
          attributed to the data when it was produced by the criterion" is unacceptable. The two
          axes this gap closure ADDED are held to no such standard.
    missing:
      - "A per-element range _prove on both Y legs — `all(isinstance(v, (int, float)) and 0.0 <= v <= 1.0 for v in values)`, which is False for NaN so it subsumes the NaN case — placed beside the extraction leg's own value checks in coverage_verdict"
      - "A tripwire in tests/test_phase20_correction.py asserting the measured differential: the same held-out axis returns INCONCLUSIVE at (0.30, 0.28) and must NOT return PASS at (nan, 0.28)"
      - "Enforce the count guard by type at :257 — `isinstance(k, int) and not isinstance(k, bool)` — so the module's own rate-space SUPERSEDED_SWEEP_SENTINEL (0.0, 1.0) cannot pass as counts (measured: it does, producing a spurious INCONCLUSIVE)"
  - truth: "20-SECURITY.md reaches threats_open: 0 with each closure pointing at a watched guard, never at a plan (20-12 must-have) — and GATE-02's residual is discharged by a choke point that refuses a borrowed retention floor"
    status: partial
    reason: >-
      T-20-19's named harm is "the looser cap a borrowing buys" (20-SECURITY.md:91). The guard
      refuses one bit pattern, not the cap. Measured: 0.06893 * (1 + 2**-50) = 0.06893000000000006
      passes the `retention_noise_floor != V20_RETENTION_NOISE_FLOOR` refusal, and
      retention_cap returns a BIT-IDENTICAL 4.029 — the exact borrowed cap — and
      corrected_point_verdict returns PASS. Control confirms the unperturbed 0.06893 IS refused, so
      the guard exists and computes; its coverage is one ULP wide. Separately and with no malformed
      input at all: retention_noise_floor=5.0 with a clean {"regime": "adapter", "seeds": (1337,
      2024)} provenance returns PASS at cap 13.89114 against the governing 3.9085032379884783 — a
      3.55x looser cap through the sanctioned route. Provenance is a caller assertion; nothing
      bounds magnitude. The register row, GATE-02's traceability note and the `status: verified` /
      `threats_open: 0` flip all rest on this guard.
    artifacts:
      - path: "scripts/phase20_gate_coverage.py"
        issue: >-
          :396-406 refuses the borrowed floor by float `!=` (bit-pattern inequality), and
          _prove_retention_floor (:353-406) never constrains the floor's magnitude. The measured
          adapter-regime floor is already a module constant at :339, so the property check is one
          line away.
      - path: ".planning/phases/20-pre-registration-the-three-condition-gate/20-SECURITY.md"
        issue: ":91 records T-20-19 as CLOSED and :4-5 publish status: verified / threats_open: 0 on the strength of that guard."
      - path: ".planning/REQUIREMENTS.md"
        issue: ":303 discharges GATE-02's residual naming _prove_retention_floor as a choke point that catches a caller who lies about regime 'by the number itself'. Measured: a one-ULP perturbation defeats it."
    missing:
      - "A magnitude bound in _prove_retention_floor — `retention_noise_floor <= _ADAPTER_REGIME_RETENTION_FLOOR * (1.0 + 1e-9)` — which admits any TIGHTER floor a later phase measures and refuses the whole looser class, of which V20_RETENTION_NOISE_FLOOR is one member rather than the definition. Keep the existing `!=` as the named-value refusal."
      - "Two tripwire cases in test_the_retention_floor_tripwire_is_the_only_route_to_a_verdict: the one-ULP-nudged borrowed floor, and an arbitrarily looser floor (5.0) with clean provenance — both must raise"
      - "Re-open T-20-19 in 20-SECURITY.md (threats_open: 1) until the bound lands, or re-scope the row's claim to what the guard actually proves"
      - "Census the IMPORT as well as the call in test_mitigation_point_verdict_has_no_caller_outside_this_module — the sole enforcement of the choke point is blind to `from mitigation_gate import mitigation_point_verdict as mpv` (ast.Name id='mpv') and to getattr-dispatch"
deferred: []
human_verification:
  - test: "Decide whether _prove_retention_floor, authored 2026-08-21 and refusing exactly one competitor to the floor measured 2026-08-20, is an acceptable D-24 dated continuation or a post-hoc rule"
    expected: "Either a recorded acceptance naming the asymmetry, or the magnitude bound (which makes the rule a property rather than a name and removes the question)"
    why_human: "This is the pre-registration policy question the previous verification escalated for the extraction leg, now instantiated on the retention leg. The evidence is unambiguous; the convention is a judgment call."
  - test: "Decide whether the NaN/out-of-range Y-sweep hole is a BLOCKER for Phase 21 or may ride to Phase 23"
    expected: "A dated decision. No sweep exists until Phase 25 and Phase 21 does not consume GATE-06, so the hole is not currently reachable by any committed caller — but Phase 23 is where sweep width is set and coverage stops being hypothetical."
    why_human: "Reachability-in-practice depends on scheduling intent that is not in the codebase."
---

# Phase 20: Pre-Registration — The Three-Condition Gate — Verification Report

**Phase Goal:** "Every rule that will judge a v4.0 number is committed to git before any v4.0 number
of any kind exists — including before the cost calibration" (ROADMAP.md:150-151)
**Verified:** 2026-08-21T16:53:03Z
**Status:** gaps_found
**Re-verification:** Yes — after the 20-08..20-12 gap closure targeting gap 1

---

## Bottom line

The gap closure did real, verifiable work and it did not achieve what its own records claim.

**Closed, and I proved it by running it rather than reading it.** CR-01's extraction half is
genuinely fixed: `coverage_verdict` decides the extraction axis on `wilson_upper_bound(k, n)`, the
same statistic condition (a) reads, and both reproduced directions are armed as *pin-vs-correction
differentials* — the test asserts the frozen pin's wrong answer AND the correction's right one in one
body, so a regression in either side reddens. WR-09's missing parameter now exists and both legs of Y
are decided in the same function against the same rule. All four remediation artifacts the previous
verification prescribed landed. The pin survived its own correction byte-identically, and the
ancestry guard got *stronger* (1 → 3 artifacts × 9 commits) rather than being loosened to accommodate
the new files. That is the hard part of a pre-registration correction and it was done correctly.

**Not closed.** Every guard the closure added on the three axes it introduced — both Y legs and the
retention floor — is weaker than the record that cites it, and I reproduced each hole in my own
process:

| What the record claims | What I measured |
|---|---|
| REQUIREMENTS.md:303 — the retention choke point catches "a caller that lies about `regime` … by the number itself" | `0.06893 * (1 + 2**-50)` passes the refusal and `retention_cap` returns a **bit-identical `4.029`** — the exact borrowed cap. Control: unperturbed `0.06893` IS refused. |
| 20-SECURITY.md:91 — T-20-19 CLOSED; the harm is "the looser cap a borrowing buys" | `retention_noise_floor=5.0` with clean adapter provenance → **`PASS`**, cap `13.89114` vs governing `3.9085032379884783` |
| ROADMAP SC3 amendment — coverage now decided on "both Y legs included" | Held-out axis `(0.30, 0.28)` → `INCONCLUSIVE`. **Same axis, one point NaN'd — `(nan, 0.28)` → `PASS`, no GATE-06 reason.** More truncated, decisively judged. |

The third row is the one that matters most and it is sharper than the code review recorded. The
review showed garbage input reaching a PASS. What I measured is a **verdict flip on the identical
truncated axis**: NaN-ing one of two points makes a sweep that never crossed Y read as bracketed. The
review's `(-99.0, 42.0)` demonstration invites the answer "that is garbage in, garbage out". A
differential does not: the honest reading is `INCONCLUSIVE`, and one NaN buys the maximally
favourable verdict instead. `nan >= criterion` is `False`, so the NaN is *counted as a failing point*
— it does not merely pass through, it actively manufactures the bracket. A NaN recall is what `0/0`
produces from an empty held-out question set.

**The pattern across all three is the same and it is worth naming, because the fix for all three is
the same six lines the review already wrote.** Each guard refuses a *name* where the harm is a
*property*: the borrowed floor by its bit pattern rather than by being loose; the regime by a
caller-asserted string; the Y sweeps by length rather than by being recalls. The module knows the
difference — it spends three `_prove` calls and a fourteen-line message enforcing exactly this
distinction on the extraction axis, at `:248-277`, justified on the grounds that "a coverage finding
attributed to the data when it was produced by the criterion" is unacceptable. The four axes this gap
closure added are held to a length check.

**Proportion, stated so this is not read as bigger than it is.** No committed caller can reach any of
these holes today — `corrected_point_verdict` has exactly zero non-test callers, which the AST census
measures and I confirmed. The extraction leg, the leg CR-01 was actually about, is validated three
ways. Nothing here inflates a published v4.0 number, because no v4.0 sweep exists. The defects are in
a rule that will be consumed at Phase 23/25, and closing them costs roughly ten lines plus two test
cases. This is a phase that is one small commit from done, not a phase that failed.

---

## Goal Achievement

### Observable Truths

Must-haves carried forward from the previous verification. Truths 0-2 and 4-5 receive a regression
check (they passed before and nothing in the closure touched the pin); truth 3 receives full
three-level re-verification.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 0 | **The goal sentence** — every rule committed before any v4.0 number of any kind exists, including before the cost calibration | ✓ VERIFIED (scope narrowed — see below) | Regression check green and *strengthened*. `git diff --exit-code -- scripts/mitigation_gate.py` returns 0 and `git diff 7e6de4b HEAD` on the pin and on `erasure_gate.py` is empty — the pin is byte-identical across its own correction. The ancestry guard's `V4_ARTIFACT_GLOBS = ("results/phase20_*",)` now matches **three** artifacts (`phase20_retention_floor.json` 2026-08-20 19:37:56, `phase20_gate_coverage_correction.md` 12:18:24, `.json` 12:22:25) against nine pin commits `95b3c8a`..`abf9072` (16:27:23→17:43:17), all first-adds after the last pin commit. Phase 23 has not run. |
| 1 | **SC1** — three conditions, keyword-only with no defaults, reason strings; (c)'s caps computed from imported constants, never retyped | ✓ VERIFIED | Regression: 18/18 `test_phase20_prereg.py` green; pin unchanged. The D-06 amendment is intact and I re-derived it: `retention_cap(retention_noise_floor=0.008681618994239138)` = `3.9085032379884783`. The gap closure's `_GOVERNING_CAP` recomputes the same value by calling the frozen function rather than retyping it. |
| 2 | **SC2** — Y is a pair, a locked fraction of the retrained control, never v2.0's 0.4921 / 0.3483 | ✓ VERIFIED | Regression: pin unchanged, exact-equality import assertion still green. The correction reads `F_Y` by import identity and computes both legs from their own controls (`:521-522`). |
| 3 | **SC3 (as amended by D-34/D-37)** — every branch watched firing; GATE-05 precedence; a sweep that never crossed X **or Y** returns INCONCLUSIVE not FAILURE; arm identity; provisional until replicated | ✗ **FAILED (partial — X half closed, Y half falsifiable)** | **X: CLOSED.** `coverage_verdict:279-282` computes `wilson_upper_bound(k, n)` per point; `:294-297` compares each axis on its criterion's own direction. Both directions armed as pin-differentials at `tests/test_phase20_correction.py:196-226` and `:254-302`, plus the third case (`FIXTURE_CLEARING_POINT` at `(3,11)`, a pin `PASS` → corrected `INCONCLUSIVE`). **Y: FALSIFIED.** Measured differential against `Y_heldout = 0.24499999999999997`: `(0.30, 0.28)` → `INCONCLUSIVE` + GATE-06 reason; `(nan, 0.28)` → `PASS`, no GATE-06 reason. See the crux table above. |
| 4 | **SC4** — the n=8-vs-n=64 capacity rule committed before either run, both branches publishable | ✓ VERIFIED | Regression: `_CAPACITY_DISPATCH` totality proved at import, pin unchanged, guard green. |
| 5 | **SC5** — per-point K, full-fidelity K, promotion rule committed before the first v4.0 artifact; CPU-only ancestry test; `_prose.normalized` differential | ✓ VERIFIED | Regression: ancestry test green and now covering three artifacts rather than one. `_prose.py` untouched by the closure. |

**Score: 5/6 truths verified**

### Gap-closure plan must-haves (20-08..20-12), verified individually

The gap-closure plans declared their own must-haves. These are additive to the roadmap SCs and are
verified here rather than taken from SUMMARY.md.

| Plan | Declared truth | Status | Evidence |
|---|---|---|---|
| 20-08 | Extraction coverage decided on `wilson_upper_bound(k, n)` | ✓ VERIFIED | `:279-282`, `:294-295`; armed differential |
| 20-08 | Coverage decided on **both** legs of Y | ✓ VERIFIED (structurally) | `sweep_heldout_recalls` exists, is length-checked at `:241-247`, decided at `:286`/`:296-297` in the same body. The *finding* it produces is not trustworthy — see gap 1. |
| 20-08 | A floor with no provenance / wrong regime / <2 seeds / **or the borrowed 0.06893** cannot reach a verdict | ⚠️ VERIFIED LITERALLY, DEFEATED IN CLASS | The literal value `0.06893` is refused (I ran the control). `0.06893 * (1 + 2**-50)` is not, and buys the bit-identical `4.029`. |
| 20-08 | Raw-rate space unreachable: the parameter is gone AND a smuggled rate is refused by name | ⚠️ PARTIAL | The parameter is genuinely absent (`SystemExit` on `sweep_extraction_rates=`, guarded at `:305`). The value refusal accepts integral floats: the module's own `SUPERSEDED_SWEEP_SENTINEL = (0.0, 1.0)` passes as counts (measured → spurious `INCONCLUSIVE`). Demotion-only, so warning-grade. |
| 20-08 | The bound-direction resolution written down with reason and cost | ✓ VERIFIED | Module docstring + `bound_direction.cost` in the artifact, naming the Y legs' inherited lack of a confidence bound |
| 20-09 | Every requirement ID carries a traceability note naming function + guard | ✓ VERIFIED | REQUIREMENTS.md:302-313; both names resolve for all eleven checked IDs |
| 20-09 | A reader who greps `4.029000` lands on a dated amendment | ✓ VERIFIED | REQUIREMENTS.md:55 D-36 amendment beneath the GATE-02 bullet |
| 20-10 | Machine-readable artifact naming what it governs and supersedes | ✓ VERIFIED | `governs`, `supersedes`, `governing_module`, `governing_entry_point`, `defects`, `evidence`, `heldout_coverage`, `proof` all present |
| 20-10 | The pin's published reading preserved unedited, correction added beside it | ✓ VERIFIED | Two commits (`4e4d5ef` then `2a32394`); the append is a diff against existing bytes, not a rewrite |
| 20-10 | key_link pattern `Addendum — 2026-08-20` | ℹ️ DEVIATED, CORRECTLY | The committed heading is `## Addendum — 2026-08-21`, the real write date. The deviation is recorded in ROADMAP.md:279 and is the honest choice. |
| 20-11 | Both directions watched RED-then-GREEN, not merely written | ✓ VERIFIED | Pin-vs-correction differentials, four watched-RED breaks recorded and restored byte-identically |
| 20-11 | A future caller reaching a verdict without the correction turns a test red | ⚠️ PARTIAL | The census (`:925-936`) keys on `node.func.id or node.func.attr` against the literal name. `from mitigation_gate import mitigation_point_verdict as mpv; mpv(...)` is `ast.Name(id='mpv')` — invisible. Scope is `scripts/` + `src/` only. |
| 20-11 | A hand-edited number in the artifact turns a test red | ✓ VERIFIED | `test_every_published_number_re_derives_from_the_modules` (`:575`); one-digit `cap` edit watched red |
| 20-11 | The artifact→`retention_cap` coupling watched on both sides (WR-02) | ✓ VERIFIED | `test_v4_retention_cap_reads_the_measured_adapter_regime_floor` (`:850`) — the previous verification's WR-02 PARTIAL is closed |
| 20-12 | GATE-06 marked complete only after the correction exists, is watched, and is enforced | ⚠️ PARTIAL | Exists ✓, watched ✓, *enforced* only against the call form the census can see, and the Y-leg enforcement is a length check |
| 20-12 | SC3 carries a dated amendment so a re-verifier cannot re-file the identical gap | ✓ VERIFIED | ROADMAP.md SC3 blockquote; original text byte-preserved (40 insertions, 0 deletions). I did not re-file the identical gap — the X half is closed and I recorded it as closed. |
| 20-12 | `threats_open: 0` with each closure pointing at a watched guard | ✗ **FAILED** | The file reaches `threats_open: 0` and each row names a guard. T-20-19's guard does not cover T-20-19's named harm — measured, twice. |
| 20-12 | Published total substantiated by the file's own rows | ✓ VERIFIED | 66 rows, 8 transcribed with citations |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/mitigation_gate.py` | The frozen pin, unedited | ✓ VERIFIED FROZEN | Byte-identical across the entire gap closure. `git diff 7e6de4b HEAD` empty; worktree clean. The pre-registration survived its own correction — this is the load-bearing fact and it holds. |
| `scripts/phase20_gate_coverage.py` | The governing correction — `coverage_verdict`, `wilson_lower_bound`, `_prove_retention_floor`, `corrected_point_verdict` | ⚠️ SUBSTANTIVE, WIRED, **defects on the three axes it adds** | 602 lines. Every named surface exists and computes. Wilson mirror verified sound by the review and consistent with `erasure_gate:139-158`. Imports `wilson_upper_bound` / `F_Y` / `MARGIN_K` by identity, calls the pin rather than reimplementing it. Holes: `:241-247` (Y length-only), `:257` (integral floats as counts), `:396-406` (bit-pattern refusal), `:353-406` (no magnitude bound). |
| `tests/test_phase20_correction.py` | The armed tripwires | ✓ VERIFIED (with a named blind spot) | 957 lines, 11 tests, 11 passed. Genuinely armed on the extraction axis: differentials assert the pin's RED and the correction's GREEN in one body. Blind spot: the census's alias hole (GC-06). |
| `results/phase20_gate_coverage_correction.json` | `governs` / `supersedes` / defects / evidence / proof | ✓ VERIFIED | 234 lines. `governs` names `coverage_verdict` as the computation and `corrected_point_verdict` as the route. Every number in it is re-derived by a committed test. Records `heldout_coverage` with a worked demonstration. |
| `results/phase20_gate_coverage_correction.md` | The D-24 dated continuation | ✓ VERIFIED | `## Addendum — 2026-08-21` appended via `scripts/_addendum.py::append_addendum`; additivity guarded by `test_correction_addendum_is_additive_on_the_published_artifact` at a synthetic tmp location. |
| `.planning/REQUIREMENTS.md` | All 12 IDs accounted for | ✓ VERIFIED | Previous gap 2 closed — see Requirements Coverage below. |
| `20-SECURITY.md` | `threats_open: 0`, each closure evidenced | ⚠️ **BOOKKEEPING COMPLETE, ONE CLOSURE UNSUPPORTED** | 66 rows, totals reconcile by transcription. T-20-19's closure is contradicted by measurement. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `phase20_gate_coverage.py` | `erasure_gate.wilson_upper_bound` | import by object identity | ✓ WIRED | Imported, not redefined; `wilson_lower_bound` is a mirror with the clamp flipped, not a second copy of the upper bound |
| `corrected_point_verdict` | `mitigation_gate.mitigation_point_verdict` | one call, with the neutralising sentinel | ✓ WIRED | Called once at `:556`; GATE-05, GATE-08, arm identity and all three conditions come back unaltered. Sentinel provably neutralises `:798-812` given the preconditions proved at `:536-552`. |
| `corrected_point_verdict` | `_prove_retention_floor` | called FIRST, before any compute — the choke point | ⚠️ WIRED, **INSUFFICIENT** | The call *is* first (`:498`) and unavoidable on this route. What it proves is one bit pattern and one caller-asserted string. Measured: `5.0` passes. |
| `coverage_verdict` | both Y legs | one body, one rule (D-35 / WR-09) | ⚠️ WIRED, **HOLLOW FINDING** | Both legs read; the finding is manufacturable from unvalidated values |
| AST caller census | every `mitigation_point_verdict` call site | `ast.walk` over `scripts/` + `src/` | ⚠️ PARTIAL | Blind to aliased imports and getattr-dispatch; blind outside `scripts/`+`src/`. This is the **sole** enforcement of the choke point per both modules' docstrings. |
| ancestry guard | `results/phase20_*` | `git log --diff-filter=A` | ✓ WIRED, STRENGTHENED | 3 artifacts × 9 commits = 27 checks (was 9) |
| `scripts/phase20_gate_coverage.py` | any ancestry guard | — | ℹ️ **ABSENT** | `PHASE20_PREREG_ARTIFACT` is `scripts/mitigation_gate.py` alone. The module the amendment makes GOVERNING has no ordering guard and postdates the phase's one v4.0 artifact by ~17h. Legitimate under D-24 and dated — but see Human Decision 1. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `coverage_verdict` extraction axis | `x_uppers` | `wilson_upper_bound(k, n)` over validated counts | Yes — three per-element `_prove`s upstream | ✓ FLOWING |
| `coverage_verdict` taught axis | `sweep_taught_recalls` | caller, **unvalidated** | No — any value at all is accepted | ⚠️ HOLLOW |
| `coverage_verdict` held-out axis | `sweep_heldout_recalls` | caller, **unvalidated** | No — NaN manufactures a bracket (measured) | ⚠️ HOLLOW |
| `_prove_retention_floor` | `retention_noise_floor` | caller + caller-asserted provenance | No — magnitude unconstrained; `5.0` reaches a PASS | ⚠️ HOLLOW |
| `_GOVERNING_CAP` / `_BORROWED_CAP` | derived caps in the refusal messages | computed by calling the frozen `retention_cap` | Yes — never retyped | ✓ FLOWING |
| correction artifact `evidence` | all verdicts and bounds | re-derived by a committed test | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

All run in my own process against the committed tree with `.venv/bin/python`, not read off a SUMMARY.

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full suite | `.venv/bin/python -m pytest -q` | `874 passed, 1 skipped in 198.52s` | ✓ PASS |
| Phase-20 guards | `pytest tests/test_phase20_correction.py tests/test_phase20_prereg.py -q` | `29 passed in 1.86s` | ✓ PASS |
| Lint | `ruff check .` / `ruff format --check .` | `All checks passed!` / `176 files already formatted` | ✓ PASS |
| Pin frozen across the correction | `git diff 7e6de4b HEAD -- scripts/mitigation_gate.py scripts/erasure_gate.py` | empty | ✓ PASS |
| Ancestry still holds, now over 3 artifacts | `git log --diff-filter=A -- results/phase20_*` vs 9 pin commits | all first-adds ≥ 2026-08-20 19:37, last pin commit 17:43 | ✓ PASS |
| **GC-01** — borrowed-floor refusal | `retention_cap(0.06893*(1+2**-50))` through `corrected_point_verdict` | `PASS`; cap `4.029` **bit-identical** to `retention_cap(0.06893)`. Control: `0.06893` refused. | ✗ **FAIL** |
| **GC-02** — looser floor, clean provenance | `corrected_point_verdict(retention_noise_floor=5.0, provenance={"regime":"adapter","seeds":(1337,2024)})` | `PASS`; cap `13.89114` vs governing `3.9085032379884783` | ✗ **FAIL** |
| **GC-03 differential (sharper than the review)** | held-out `(0.30, 0.28)` vs `(nan, 0.28)`, `Y_heldout = 0.24499999999999997` | `INCONCLUSIVE` + GATE-06 reason → **`PASS`, no GATE-06 reason** | ✗ **FAIL** |
| **GC-04** — module's own rate-space sentinel as counts | `sweep_extraction_successes=(0.0, 1.0)` | accepted as counts → spurious `INCONCLUSIVE` | ⚠️ WARN |
| **GC-05** — contradictory reason payload | corrected route on `FIXTURE_CLEARING_POINT` at `(3,11)` | `INCONCLUSIVE` carrying 4 decisive *clearing* reason lines verbatim | ⚠️ WARN |
| **GC-06** — census blind spot | read `tests/test_phase20_correction.py:925-936` | keys on `node.func.id or .attr` vs the literal name; alias/getattr invisible | ⚠️ WARN |

### Probe Execution

No `scripts/*/tests/probe-*.sh` exists in this repository and no PLAN declares one. The runnable
equivalents are the module self-check and the pytest twins, executed above in my own process.

| Probe | Command | Result | Status |
|-------|---------|--------|--------|
| Phase-20 behavioural twins | `pytest tests/test_phase20_correction.py tests/test_phase20_prereg.py -q` | `29 passed` | PASS |
| Whole-repo regression | `pytest -q` | `874 passed, 1 skipped` | PASS |

### Requirements Coverage

**Previous gap 2 is CLOSED.** All twelve IDs now carry state, and the eight that were silently
unchecked are checked with traceability notes naming the discharging function and its guard. I
spot-checked that the named functions and guards resolve.

| Requirement | Source Plan(s) | Code state | REQUIREMENTS.md | Evidence |
|-------------|----------------|-----------|-----------------|----------|
| GATE-01 | 20-01, 20-02, 20-04, 20-06 | ✓ SATISFIED | `[x]` + note (:302) | Three-name domain, AST-proved keyword-only, four reason strings |
| GATE-02 | 20-01, 20-04, 20-06, 20-07, 20-08..20-12 | ⚠️ MECHANISM SATISFIED, RESIDUAL **RE-OPENS** | `[x]` + D-36 amendment + residual-closed note (:303) | The supersession is honest and tighter (verified arithmetically, unchanged from the previous verification). The residual's *closure* — the retention choke point — is defeated by a one-ULP nudge and by any looser floor. See gap 2. |
| GATE-03 | 20-04, 20-06 | ✓ SATISFIED | `[x]` + note (:304) | `y_taught` / `y_heldout` pair at `:765-766` |
| GATE-04 | 20-04, 20-06 | ✓ SATISFIED | `[x]` + note (:305) | Each leg `F_Y ×` its own control; 0.4921/0.3483 AST-absent |
| GATE-05 | 20-04, 20-06 | ✓ SATISFIED | `[x]` + note (:306) | Early return before any reason appended; watched differentially |
| GATE-06 | 20-04, 20-06, 20-08, 20-10, 20-11, 20-12 | ⚠️ **PARTIAL** — X closed, Y falsifiable | `[x]` + long note (:307) | The note is accurate about what was built and about the pin being unedited. It over-claims on the Y axis: "closing WR-09 in the same function" is true of the parameter and not of the finding. See gap 1. |
| GATE-07 | 20-01, 20-05, 20-06 | ✓ SATISFIED | `[x]` + note (:308) | 3-tuple carries `arm`; mixed-arm list aborts |
| GATE-08 | 20-04, 20-05, 20-06 | ✓ SATISFIED | `[x]` + note (:309) | INCONCLUSIVE over a would-be PASS; one `REPLICATION_PENDING_MARKER` constant |
| GATE-09 | 20-05, 20-06 | ✓ SATISFIED | `[x]` + note (:310) | Six outcomes fired; fixture asserted against the parsed Phase 19 artifact |
| GATE-10 | 20-05, 20-06 | ✓ SATISFIED | `[x]` + note (:311) | `_CAPACITY_DISPATCH` totality proved at import |
| CAL-04 | 20-01, 20-05, 20-06, 20-07 | ✓ SATISFIED | `[x]` (:312) | `K_RUNGS` + `ratchet_k` + `promote_to_full_fidelity` precede the first artifact. ℹ️ Its traceability note is a five-word stub — the only one of the twelve that does not name a function and a guard. Cosmetic; the underlying discharge is verified. |
| RPT-02 | 20-03, 20-06 | ⚠️ PARTIAL BY DESIGN | `[ ]` + explicit deferral (:313) | Correctly unchecked. The previous verification's complaint — that the deferral lived only in a SUMMARY — is closed: the Phase 25 deferral is now recorded in REQUIREMENTS.md with the four in-phase instances of the defect class it exists to close. |

**Orphaned requirements:** none. `grep -E "Phase 20" .planning/REQUIREMENTS.md` maps exactly the
twelve IDs the plans claim.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | `TBD` / `FIXME` / `XXX` | — | **None** in any file the gap closure touched. Debt-marker gate clean. |
| — | — | `TODO` / `HACK` / `PLACEHOLDER` | — | None |
| `scripts/phase20_gate_coverage.py` | 241-247, 296-297 | A pair-valued criterion validated for length while its values are consumed raw | 🛑 Blocker (against SC3) | Gap 1 — NaN manufactures coverage |
| `scripts/phase20_gate_coverage.py` | 396-406 | Float `!=` standing in for a magnitude property | 🛑 Blocker (against 20-12's `threats_open: 0`) | Gap 2 — one ULP defeats T-20-19's named refusal |
| `scripts/phase20_gate_coverage.py` | 353-406 | Provenance validated, magnitude unconstrained | 🛑 Blocker (against 20-12's `threats_open: 0`) | Gap 2 — `5.0` reaches a PASS at a 3.55× looser cap |
| `scripts/phase20_gate_coverage.py` | 257 | `isinstance(k, float) and k.is_integer()` admits rates | ⚠️ Warning | The module's own `SUPERSEDED_SWEEP_SENTINEL` passes as counts. Demotion-only. |
| `scripts/phase20_gate_coverage.py` | 588-602 | Decisive clearing reasons returned verbatim under a contradicting INCONCLUSIVE | ⚠️ Warning | A reader scanning reasons rather than the verdict reads a cleared point. Reason-scanning is an established pattern here (`REPLICATION_PENDING_MARKER`, `_names_gate06`). |
| `tests/test_phase20_correction.py` | 925-936 | The sole choke-point enforcement is blind to aliased imports | ⚠️ Warning | `mpv(...)` after `import … as mpv` bypasses every correction silently |
| `scripts/phase20_gate_coverage.py` | 339 | `_ADAPTER_REGIME_RETENTION_FLOOR` retyped from a committed JSON artifact | ⚠️ Warning | Against the module's own stated "never retyped" discipline; drift caught only incidentally by a substring assertion |
| `scripts/phase20_gate_coverage.py` | 248-255 | Refusal message argues about a failure mode its predicate cannot detect | ℹ️ Info | A draw-denominated `n` is positive and passes; `n = 104.5` computes without complaint |
| `scripts/phase20_gate_coverage.py` | 386-387 | Unhashable `seeds` raises `TypeError` instead of a refusal | ℹ️ Info | Leaks a traceback from a function whose "whole output is the refusal" |

No stub patterns. Every `return` computes; no empty handler, no hardcoded-empty prop, no
`return null` shape anywhere in either new file.

---

## Did the gap closure close gap 1?

The previous verification listed four missing items. **All four landed.** Judged individually:

1. **`results/phase20_gate_coverage_correction.json` with a `governs` field, in the
   `phase19_calibration_correction.json` shape** — ✓ landed, and exceeded: it also carries
   `supersedes`, `defects`, `evidence` for all three cases, `heldout_coverage`, `bound_direction`
   with its cost, and `recorded_not_corrected` for the items deliberately left. Every number in it is
   re-derived by a committed test, and a one-digit edit was watched turning that test red.
2. **`append_addendum(...)` dated continuation, never an edit to the pin** — ✓ landed. The `.md`
   carries `## Addendum — 2026-08-21` written through `scripts/_addendum.py`, in two commits so the
   append is provably additive, with a tmp-location additivity guard. The pin is byte-identical.
3. **An armed tripwire in an unpinned test file, both directions** — ✓ landed and genuinely armed.
   The arming is structural, which is the right kind: each test asserts the *frozen pin's* wrong
   answer and the *correction's* right answer in one body, so neither side can regress silently.
   Four watched-RED breaks were performed and restored byte-identically.
4. **A recorded decision on the un-coverable held-out Y leg (WR-09)** — ✓ landed, and the *stronger*
   of the two options the previous verification offered: corrected rather than accepted-in-writing.
   `sweep_heldout_recalls` exists and both legs are decided in one body.

**So the prescription was followed.** What the closure then did beyond the prescription is where it
went wrong: it flipped `GATE-06` to `[x]`, `20-SECURITY.md` to `status: verified` / `threats_open: 0`,
and T-20-19 to closed — three assertions of completeness resting on guards that are one length check
and one float `!=` wide. The previous verification's own instruction was "leave GATE-06 unchecked and
add a traceability note naming CR-01 + WR-09 and the correction artifact that will close them." The
artifact now exists, so checking it is defensible in principle. It is not defensible on the Y axis,
where the coverage finding the checkbox certifies can be produced by the input.

**A gate cannot be green over guards with measured holes when the guards are the entire basis for the
green.** That is not a stylistic objection — it is the trust boundary this file's own register names
at 20-SECURITY.md:39: *"a plan that says a thing will be done ↔ a guard that proves it was."* The
closure honoured that boundary against SUMMARY claims (it re-ran guards rather than citing
summaries — genuinely good practice, and I confirmed the re-runs happened). It did not extend the
same scepticism to whether the guards prove what their messages say. GC-01 is the same defect class as
T-20-19 itself: a borrowed floor reaching the cap with no refusal, now one ULP away from the value the
guard names.

---

## Human Decision Requested (Escalation Gate)

### 1. Is `_prove_retention_floor` a dated continuation or a post-hoc rule?

**Test:** `results/phase20_retention_floor.json` was committed 2026-08-20 19:37:56. The rule that
judges that floor's provenance was committed 2026-08-21, and refuses exactly one competitor to it
while admitting every looser value. Decide whether that ordering is acceptable under D-24.
**Expected:** Either a recorded acceptance naming the asymmetry, or the one-line magnitude bound —
which converts the rule from a name to a property and makes the ordering question moot, because a
property bound authored after the measurement still cannot be tuned toward a favourable answer.
**Why human:** This is the pre-registration policy question the previous verification escalated for
the extraction leg (item 2), now instantiated on the retention leg. My recommendation: take the
bound. It is one line, it is strictly conservative, the review already wrote it, and it removes both
gap 2 and the policy question in the same commit.

### 2. Does the Y-sweep hole block Phase 21, or may it ride to Phase 23?

**Test:** No committed caller reaches `corrected_point_verdict` today (the census measures zero
non-test callers and I confirmed it). Phase 21 does not consume GATE-06. Phase 23 sets sweep width,
which is where coverage stops being hypothetical.
**Expected:** A dated decision either way.
**Why human:** Reachability-in-practice depends on scheduling intent that is not in the codebase. My
reading: it does not block Phase 21, and it absolutely must close before Phase 23.

### 3. Should `20-SECURITY.md` be re-opened, or its T-20-19 row re-scoped?

**Test:** Read 20-SECURITY.md:91 against the two measurements in gap 2.
**Expected:** Either `threats_open: 1` until the bound lands, or a rewritten row scoping the closure
to what the guard proves (one named value, one asserted string) with the residual named.
**Why human:** Whether a security gate may publish `verified` with a known-narrow guard is a policy
call about this project's own standard, and this file has an unusually strict one.

---

## Gaps Summary

**The phase goal remains achieved and the pre-registration is intact.** The pin is byte-identical
across its own correction, the ancestry guard is stronger than before (3 artifacts × 9 commits, all
first-adds after the last pin commit), the correction landed as an unpinned module plus a dated
continuation rather than as an edit, and the whole repository is green at 874 passed / 1 skipped with
lint clean. That is the hard part of correcting a frozen pre-registration and it was done right.

**Gap 1 (the previous FAILED must-have) is half closed.** CR-01's extraction half — the half the gap
was filed about — is genuinely fixed and genuinely armed, with pin-vs-correction differentials that
redden on either side. WR-09's missing parameter now exists. But the two Y legs the closure added are
validated for length only, and I measured a differential the code review did not: the *same*
genuinely-truncated held-out axis returns `INCONCLUSIVE` at `(0.30, 0.28)` and `PASS` at
`(nan, 0.28)`. A NaN does not merely pass through — `nan >= criterion` is `False`, so it is *counted
as a failing point* and actively manufactures the bracket. That is direction (ii)'s false-coverage
defect reappearing on the exact axis WR-09 exists to cover, reaching a spurious `PASS` — the one
direction the previous verification certified the frozen pin could not produce.

**Gap 2 is new to this verification and is arguably the more serious of the two,** because it needs
no malformed input at all: a well-formed call with `retention_noise_floor=5.0` and clean
adapter-regime provenance returns `PASS` at a cap of `13.89114` against the governing
`3.9085032379884783`. And the guard that is supposed to refuse the borrowed Phase 12 floor is
defeated by a one-ULP nudge that buys a *bit-identical* `4.029` — the exact borrowed cap. The
unperturbed value IS refused, so the mechanism exists, computes, and is watched. Its coverage is one
bit wide, and `GATE-06`'s checkbox, GATE-02's residual discharge, T-20-19's closed row and
`threats_open: 0` all rest on it.

**The previous verification's gap 2 (requirement bookkeeping) is fully closed** — all twelve IDs
carry state, eleven checked with function-and-guard traceability notes, RPT-02 correctly unchecked
with its Phase 25 deferral now recorded in REQUIREMENTS.md rather than only in a SUMMARY.

**Neither gap blocks Phase 21**, which does not consume GATE-06 and cannot reach either hole — no
committed caller reaches `corrected_point_verdict` at all. Both must close before **Phase 23**. The
total remediation is roughly ten lines of `_prove` across two functions plus four test cases, all of
which the code review has already written out. This is a phase one small commit from done.

---

_Verified: 2026-08-21T16:53:03Z_
_Verifier: Claude (gsd-verifier) — goal-backward, FORCE stance, re-verification_
