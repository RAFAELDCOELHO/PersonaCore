---
phase: 20-pre-registration-the-three-condition-gate
verified: 2026-08-20T23:14:01Z
status: gaps_found
score: 5/6 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: null
  previous_score: null
  note: "Initial verification — no prior 20-VERIFICATION.md existed."
gaps:
  - truth: "ROADMAP SC3 — a sweep that never produced points on both sides of X (or of Y) returns INCONCLUSIVE rather than FAILURE"
    status: partial
    reason: >-
      Five of SC3's six clauses are verified by running the module. The GATE-06 clause is
      implemented against a DIFFERENT STATISTIC than the criterion it claims to bracket, on BOTH
      axes, and the verifier reproduced the failure in both directions — including a direction the
      code review did not record. The pin is frozen, so the only legal remediation is a dated
      continuation plus an armed tripwire in an unpinned file.
    artifacts:
      - path: "scripts/mitigation_gate.py"
        issue: >-
          :755-756 decides condition (a) on wilson_upper_bound(successes, questions) <= ceiling,
          while :798-799 decides GATE-06's coverage on RAW RATES against the SAME ceiling (CR-01).
          Reproduced at n=104, X=0.04535522866494124: (1) sweep (1/104, 3/104) genuinely brackets
          the criterion — wilson_upper(1,104)=0.041950 clears, wilson_upper(3,104)=0.069999 fails —
          yet returns INCONCLUSIVE "the sweep never produced points on both sides", demoting a
          would-be PASS and blocking promote_to_full_fidelity. (2) NOT IN THE REVIEW: sweep
          (3/104, 11/104), where NO point's Wilson bound clears X, is NOT flagged because the raw
          rates straddle X, and the gate returns a decisive FAIL — publishing "it did not work"
          where the honest finding is "we could not tell", which is the exact collapse GATE-06
          exists to prevent.
      - path: "scripts/mitigation_gate.py"
        issue: >-
          :800-801 checks sweep coverage on the taught leg only (sweep_taught_recalls against
          y_taught). There is no sweep_heldout_recalls parameter anywhere in the 21-kwarg
          signature, so the held-out leg of Y — which SC2 / GATE-03 / GATE-04 make load-bearing —
          has NO coverage check at all and cannot acquire one without editing a frozen file
          (WR-09).
    missing:
      - "results/phase20_gate_coverage_correction.json with a `governs` field stating that `sweep_extraction_rates` MUST be supplied in Wilson-bound space, in the shape results/phase19_calibration_correction.json already uses"
      - "append_addendum(...) dated continuation recording the correction beside the published text (D-24 — NEVER an edit to scripts/mitigation_gate.py)"
      - "An armed tripwire in an UNPINNED test file that fires when a Phase 23/25 caller passes raw rates, and a second asserting the direction-(ii) case returns INCONCLUSIVE not FAIL"
      - "A recorded decision on the un-coverable held-out Y leg (WR-09): either accept the hole in writing with its cost named, or route the held-out coverage check through the same correction artifact"
  - truth: "Every phase-20 requirement ID is accounted for as complete, explicitly deferred, or genuinely unmet"
    status: partial
    reason: >-
      The over-claim-avoidance discipline held for plans 20-01..20-06 (twelve recorded
      applications, each declining to mark a requirement claimed by a later plan). It then failed
      at the hand-off: 20-06 explicitly deferred GATE-01 through GATE-10 and RPT-02 to 20-07, but
      20-07's frontmatter claims only [GATE-02, CAL-04] and its "Requirements assessed" table
      assesses only those two. Eight IDs that ARE genuinely discharged in the committed code were
      never marked and carry no deferral note.
    artifacts:
      - path: ".planning/REQUIREMENTS.md"
        issue: >-
          GATE-01 (:27), GATE-03 (:36), GATE-04 (:38), GATE-05 (:40), GATE-07 (:46), GATE-08 (:48),
          GATE-09 (:50), GATE-10 (:53) are all `[ ]` unchecked, and their traceability rows
          (:271-280) carry empty notes — despite each being verified discharged in
          scripts/mitigation_gate.py and guarded in tests/test_phase20_prereg.py.
    missing:
      - "Mark GATE-01, GATE-03, GATE-04, GATE-05, GATE-07, GATE-08, GATE-09, GATE-10 complete with a traceability note naming the discharging function and its guard"
      - "Leave GATE-06 unchecked and add a traceability note naming CR-01 + WR-09 and the correction artifact that will close them"
      - "Leave RPT-02 unchecked and record the deferral explicitly: the helper and its differential ship here, but 'used for correction sweeps' is report-time work (Phase 25/28), which 20-03-SUMMARY.md already reasons out and REQUIREMENTS.md does not record"
deferred: []
---

# Phase 20: Pre-Registration — The Three-Condition Gate — Verification Report

**Phase Goal:** "Every rule that will judge a v4.0 number is committed to git before any v4.0 number
of any kind exists — including before the cost calibration" (ROADMAP.md:150-151)
**Verified:** 2026-08-20T23:14:01Z
**Status:** gaps_found
**Re-verification:** No — initial verification

---

## The crux: does CR-01 mean the phase goal is unmet?

The brief asks for an explicit answer to a question the two halves of which are genuinely different.
Here it is, with the reasoning stated rather than asserted.

**Decompose the goal sentence.** It makes four claims, and every one of them is about the
*provenance* of the rules, not about their *soundness*:

1. **Completeness** — "every rule that will judge a v4.0 number"
2. **Existence** — "is committed to git"
3. **Ordering** — "before any v4.0 number of any kind exists"
4. **Ordering bound** — "including before the cost calibration" (Phase 23, not merely Phase 25)

CR-01 is a correctness defect *inside* the content of one committed rule. It does not touch (2),
(3) or (4), all three of which I verified independently against the object graph rather than against
any SUMMARY. It touches (1) only under a reading of "rule" as "correct rule" — and that reading
would make pre-registration incoherent, because the entire evidentiary value of a pre-registration
comes from the rule staying frozen *precisely when it turns out to be suboptimal*. A pre-registration
you may repair after seeing the data is not a pre-registration. This repository has already written
that argument down twice, at `MITIGATION_DECISION_RULE` clause 2 and at
`results/phase19_erasure_report.md:453-457`, about `erasure_gate.py`.

**So: the goal is ACHIEVED, and CR-01 is a real defect in a correctly pre-registered rule.** Those
are the two findings and they coexist. The pin was committed nine times between 16:27:23 and
17:43:17; the first v4.0 number was committed at 19:37:56; the cost calibration has not run. Nothing
about CR-01 moves any of those facts.

**What I will not hand-wave in the other direction.** Two things make the defect materially worse
than the code review and the orchestrator's brief record it:

**(a) The bias is NOT one-directional.** The brief states the defect "produces SPURIOUS
INCONCLUSIVE, never a spurious PASS", and REVIEW.md lists only that direction. I reproduced the
opposite direction as well. Because `{raw > X} ⊆ {wilson > X}` and `{wilson ≤ X} ⊆ {raw ≤ X}`, the
raw-rate test can also spuriously satisfy `x_at_or_below` — so a sweep in which **no** point's Wilson
bound clears X, i.e. a genuinely truncated extraction axis, escapes the GATE-06 branch entirely and
receives a decisive **FAIL**. I ran it: `sweep_extraction_rates=(3/104, 11/104)` at X=0.045355,
where `wilson_upper(3,104)=0.070` and `wilson_upper(11,104)=0.166` both exceed X, returns `FAIL`
with no GATE-06 reason. That is "it did not work" published where the honest finding is "we could
not tell" — the exact collapse GATE-06 was built to prevent, produced by GATE-06.

The narrower claim *does* survive: the defect cannot manufacture a spurious **PASS** under
self-consistent inputs, because a point that clears (a) has `wilson ≤ X`, which forces
`x_at_or_below` true under both readings. So the milestone's headline claim cannot be inflated by
this. But "conservative only" is the wrong description of a defect that can suppress an
INCONCLUSIVE.

**(b) GATE-06 has a second, independent hole in the same block.** `:800-801` reads only
`sweep_taught_recalls` against `y_taught`. There is no `sweep_heldout_recalls` parameter in the
21-kwarg signature at all. SC2 and GATE-03/GATE-04 make the held-out leg load-bearing precisely so
that "gating taught-only cannot reward memorization over generalization" — and the coverage check
that is supposed to protect the Y axis reads half of Y. Unlike CR-01, this one cannot be corrected by
a caller convention: the parameter does not exist and the file is frozen.

**Net effect on SC3.** SC3 is a roadmap success criterion and it is **demonstrably false as
written** for its GATE-06 clause, in a form I reproduced rather than inferred. That is a FAILED
must-have. It is *not* a failure of the goal sentence, and I have marked the two separately below so
neither reading can borrow credit from the other.

**Does it block Phase 21?** No. Phase 21 (privacy unit, DP data path, n=64 corpus) does not consume
GATE-06. The binding deadline is **Phase 23**, where Z's sweep width is set — sweep coverage and
sweep sizing are the same decision — and absolutely Phase 25, which judges points by importing this
rule. Committing the correction now is free: `results/phase20_gate_coverage_correction.json` is a new
`results/phase20_*` file whose first add would land after all nine pin commits, so the ancestry guard
stays green. The review prescribed exactly this remediation and **it has not been done** — no
correction artifact, no `append_addendum` call, no tripwire exists in the repository.

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 0 | **The goal sentence** — every rule committed to git before any v4.0 number of any kind exists, including before the cost calibration | ✓ VERIFIED | Verified against the commit DAG, not against SUMMARY claims. Nine pin commits `95b3c8a`..`abf9072` (16:27:23→17:43:17); artifact first-add `9bb34ad` (19:37:56). I ran `git merge-base --is-ancestor` for all nine pairs — 9/9 OK. `git log --diff-filter=A -- results/` shows the phase20 artifact is the ONLY results file added after the pin; every other is Phase 19 or earlier. Phase 23 has not run. Guard live and non-vacuous: 1 artifact × 9 commits = 9 checks. |
| 1 | **SC1** — PASS/FAIL/INCONCLUSIVE against three conditions, every argument keyword-only with no defaults, every condition rendered into a reason string; (c)'s caps computed from imported constants, never retyped | ✓ VERIFIED (with the ROADMAP's own dated D-06 amendment) | `mitigation_point_verdict:637-831`, 21 keyword-only args, zero defaults — proved by AST over ALL public functions, not just the verdict one. Ran it: 4 condition reason strings. `superseded_dialogue_cap(gap_noise_floor=0.005214448168350039)` returns `4.5837288963367` **exactly** (I ran it). `retention_cap` computes from imported `V20_EWC_RETENTION_PPL` + `MARGIN_K` × required-kwarg floor → `3.9085032379884783`, bit-identical to the artifact's `cap` (I ran it). AST scan proves 4.5733 / 3.891140 / 0.068930 / 0.005214448168350039 appear as no numeric constant. |
| 2 | **SC2** — Y is a pair, a locked fraction of the retrained control, never derived from v2.0's 0.4921 / 0.3483 | ✓ VERIFIED | `:765-768` — `y_taught = F_Y * control_taught_recall`, `y_heldout = F_Y * control_heldout_recall`; both controls are required kwargs with no default. AST scan asserts `0.4921` and `0.3483` appear as no numeric constant; the `from erasure_gate import` list is asserted by **exact equality** to five names, so `V20_TAUGHT_RECALL`/`V20_HELDOUT_RECALL` cannot be present. |
| 3 | **SC3** — every verdict branch watched firing; GATE-05 precedence over FAIL; a sweep that never crossed X (or Y) returns INCONCLUSIVE not FAILURE; arm identity on the verdict; a clear is provisional until replicated | ✗ **FAILED (partial — 5 of 6 clauses)** | Five clauses verified by RUNNING the module (exit 0, all six outcomes printed): destroyed-model fixture → FAIL; GATE-05 early return with a 1-element reason list, differential against that FAIL; GATE-08 INCONCLUSIVE overriding a would-be PASS with `REPLICATION_PENDING_MARKER`; arm identity on the 3-tuple; mixed-arm list raises. **The GATE-06 clause fails on both axes** — see the crux section. Reproduced in both directions at n=104. |
| 4 | **SC4** — the n=8-vs-n=64 capacity rule committed before either run, both branches publishable, neither selectable after seeing data | ✓ VERIFIED | `_CAPACITY_DISPATCH:1039-1044` total over all four `(small_cleared, large_cleared)` combinations, proved at import by a module-scope `_prove`; `CAPACITY_BRANCHES` closed at five. Both named branches observed firing in the self-check I ran. The D-26 fallback raises with the tolerance unset and the message names D-26 — the third chosen constant is flagged, not smuggled. |
| 5 | **SC5** — per-point K, the full-fidelity K and the promotion rule all committed before the first v4.0 artifact; a CPU-only ancestry test; `_prose.normalized` finds a line-wrapped phrase `grep -c` reports absent | ✓ VERIFIED | `K_RUNGS = (48, 24, 16, 8)` closed and ordered; `ratchet_k` refuses decreases and the refusal cites ATK-03; `promote_to_full_fidelity` takes both Ks as required kwargs and reaches the ratchet through ONE implementation (proved by the abort path). Ancestry test is CPU-only and green. **I ran a real `grep -c "the three reductions"` on the wrapped bytes → `0`, and `normalized(phrase) in normalized(text)` → `True`** on the same bytes. |

**Score: 5/6 truths verified**

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/mitigation_gate.py` | The complete pin — verdict domain, arms, two chosen constants, K menu + ratchet + promotion, X + tripwire + tolerance reporter, both (c) legs, three-condition verdict, per-arm existential, capacity rule, six-outcome `__main__` | ⚠️ SUBSTANTIVE, WIRED, **defect in GATE-06** | 1,431 lines, 9 commits. Every named surface exists and executes. Imported by `tests/test_phase20_prereg.py` and run as a subprocess in CI. Frozen: any further commit reddens the ancestry guard irreversibly. |
| `tests/test_phase20_prereg.py` | Ancestry guard, RPT-02 differential, D-22 four-state throwaway-repo fixture, AST register, constant audits, behavioural twin | ✓ VERIFIED | 1,368 lines, 18 tests, 18 passed in 1.07s (I ran it). The D-22 fixture drives `_assert_ordering_holds` — the SAME helper the live guard calls, parameterized on `root` — through five states in a `tmp_path` repo. |
| `scripts/_prose.py` | The one whitespace-normalizing prose read, phase-neutral, import-free | ✓ VERIFIED | 46 lines, zero imports (AST-asserted). Leading underscore verified by fnmatch against six pin globs. |
| `scripts/phase20_run.py` | The UNPINNED MPS retention-floor driver with its bit-identity control | ✓ VERIFIED | 288 lines. `retention_perplexity(model, pin.RETENTION_BIN, block_size, device, tok)` — the fourth return of `load_adapted_model` is discarded as `_forbid`, avoiding the instrument trap exactly as `phase19_run.py:803` does. Unpinned by design so the pin stays an ancestor of the artifact it produced. |
| `results/phase20_retention_floor.json` | The adapter-regime retention noise floor with embedded provenance | ✓ VERIFIED | Floor `0.008681618994239138` — I verified it equals `abs(adapter_on_1337 − adapter_on_2024)` exactly. Bit-identity control: seed 1337 reproduces the published `adapter_off 3.891139975617828` and `adapter_on 4.219759892336485` at `abs_delta 0.0`, across two distinct adapter files (both sha256s recorded). `governs` field present and correct. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `mitigation_gate.py` | `erasure_gate.py` | `from erasure_gate import (...)` after sys.path bootstrap | ✓ WIRED | Exactly five names, asserted by **equality** not subset. Runtime `is`-identity asserted for all five. |
| `mitigation_point_verdict` | `extraction_ceiling` | internal call — the single choke point for the D-14a tripwire | ✓ WIRED | Driven THROUGH the verdict function by `test_extraction_floor_tripwire_is_the_only_route_to_a_verdict`; a single-seed floor and a borrowed arm both abort, while the fixture differing only in provenance still PASSes. |
| `promote_to_full_fidelity` | `ratchet_k` | internal call — one ratchet, not two | ✓ WIRED | Proved by the abort path: `full_k < curve_k` raises through the promotion rule carrying the ratchet's own ATK-03 message. |
| `retention_cap` | `results/phase20_retention_floor.json` | the floor this artifact publishes is the required kwarg the function consumes | ⚠️ PARTIAL | The link is real and I verified it arithmetically end to end. But **no committed test reads the artifact** (REVIEW WR-02) — the coupling exists only in prose and in the artifact's `governs` field. A future edit to either side breaks nothing that CI watches. |
| `tests/test_phase20_prereg.py` | `scripts/mitigation_gate.py` | `PHASE20_PREREG_ARTIFACT` → `git log --format=%H --` | ✓ WIRED | Live and non-vacuous: `tracked_artifacts` 0→1, `checked` 0→9. |
| `mitigation_gate.py` | `mitigation_budget.py` | **must NOT exist** (D-20 / AST guard) | ✓ VERIFIED ABSENT | Import set is `{pathlib, sys, erasure_gate}`, asserted as a SUBSET of the allow-set. `scipy`/`numpy`/`torch` separately asserted absent. |
| `mitigation_point_verdict` (a) | `mitigation_point_verdict` GATE-06 | **must read ONE statistic** | ✗ **NOT WIRED** | (a) reads `wilson_upper_bound(...)`; GATE-06 reads raw rates. Different spaces, same ceiling. **This is CR-01.** |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `results/phase20_retention_floor.json` | `retention_ppl_noise_floor` | Two MPS `retention_perplexity` readings over `data/retention_val.bin`, 1,000,285 scored tokens, 3,908 windows | Yes — floor recomputes exactly from the two embedded `adapter_on` readings | ✓ FLOWING |
| `mitigation_gate.retention_cap` | `cap` | imported `V20_EWC_RETENTION_PPL` + `MARGIN_K` × required-kwarg floor | Yes — reproduces the artifact's `cap` bit-exact from the artifact's own floor | ✓ FLOWING |
| `mitigation_gate.extraction_ceiling` | `X` | required kwargs only — no v4.0 floor exists until Phase 23 (D-13) | N/A by design — the tripwire refuses an unlabelled floor | ✓ FLOWING (correctly deferred) |
| `mitigation_point_verdict` GATE-06 | `x_at_or_below` / `x_above` | `sweep_extraction_rates` kwarg, undocumented as to which space | **No** — compared against a ceiling defined in a different space | ⚠️ HOLLOW |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| The pin's six outcomes fire | `.venv/bin/python scripts/mitigation_gate.py` | exit 0; 6/6 outcomes + ratchet + promotion + both capacity branches + D-12 counterfactual printed | ✓ PASS |
| Phase 20 guards are green | `.venv/bin/python -m pytest tests/test_phase20_prereg.py -q` | `18 passed in 1.07s` | ✓ PASS |
| Lint gates | `ruff check .` / `ruff format --check .` | `All checks passed!` / `174 files already formatted` | ✓ PASS |
| Ordering holds on the object graph | `git merge-base --is-ancestor <each pin commit> <artifact first add>` | 9/9 OK | ✓ PASS |
| SC1's supersession is a computation | `superseded_dialogue_cap(gap_noise_floor=0.005214448168350039)` | `4.5837288963367` exactly | ✓ PASS |
| D-06's cap is TIGHTER, not looser | `retention_cap(floor=0.008681618994239138)` vs `borrowed_cap` | `3.9085032379884783 < 4.029` | ✓ PASS |
| SC5's differential against a REAL grep | `grep -c "the three reductions"` on wrapped bytes | `0`, while `normalized` finds it → `True` | ✓ PASS |
| **CR-01 direction (i)** | verdict with `sweep_extraction_rates=(1/104, 3/104)` | `INCONCLUSIVE` where the bracket is genuine and all three conditions cleared | ✗ **FAIL** |
| **CR-01 direction (ii)** | verdict with `sweep_extraction_rates=(3/104, 11/104)`, no Wilson bound clearing X | `FAIL` with **no GATE-06 reason** — a truncated axis judged decisively | ✗ **FAIL** |

### Probe Execution

No `scripts/*/tests/probe-*.sh` exists in this repository and no PLAN declares one. The equivalent
runnable checks for this phase are the module `__main__` self-check and the pytest twin, both
executed above in my own process rather than read off a SUMMARY.

| Probe | Command | Result | Status |
|-------|---------|--------|--------|
| `scripts/mitigation_gate.py` `__main__` | `.venv/bin/python scripts/mitigation_gate.py` | exit 0, 11 lines of observed branch output | PASS |
| Behavioural twin | `pytest tests/test_phase20_prereg.py::test_gate_self_check_runs_clean_in_a_fresh_interpreter` | included in 18/18 | PASS |

### Requirements Coverage

Every ID from every PLAN frontmatter, cross-referenced against `.planning/REQUIREMENTS.md`.
**Bookkeeping state is reported separately from code state, because they disagree.**

| Requirement | Source Plan(s) | Code state | REQUIREMENTS.md | Evidence |
|-------------|----------------|-----------|-----------------|----------|
| GATE-01 | 20-01, 20-02, 20-04, 20-06 | ✓ SATISFIED | ✗ `[ ]` unchecked | `mitigation_point_verdict` returns the three-name domain; AST proves every public function keyword-only with zero defaults; 4 reason strings observed |
| GATE-02 | 20-01, 20-04, 20-06, 20-07 | ⚠️ SATISFIED-WITH-SUPERSESSION | `[x]` + note | Mechanism discharged and AST-audited. Stated yield `retention_cap 4.029000` **not produced** — see the honesty assessment below |
| GATE-03 | 20-04, 20-06 | ✓ SATISFIED | ✗ `[ ]` unchecked | Y is the pair `(y_taught, y_heldout)` at `:765-766` |
| GATE-04 | 20-04, 20-06 | ✓ SATISFIED | ✗ `[ ]` unchecked | Each leg is `F_Y ×` its OWN control; 0.4921/0.3483 absent as numeric constants; recall constants absent from the exact-equality import list |
| GATE-05 | 20-04, 20-06 | ✓ SATISFIED | ✗ `[ ]` unchecked | Early return before any reason is appended; watched firing differentially against the FAIL it overrides |
| GATE-06 | 20-04, 20-06 | ✗ **PARTIAL** | `[ ]` unchecked (**correctly**) | Branch exists and fires, but reads raw rates against a Wilson-space ceiling (CR-01) and only the taught leg of a pair-valued Y (WR-09). Both reproduced. |
| GATE-07 | 20-01, 20-05, 20-06 | ✓ SATISFIED | ✗ `[ ]` unchecked | 3-tuple carries `arm`; `exists_clearing_point` aborts on a mixed-arm list; `ARM_CLAIMS` proved equal to `ARMS` at import |
| GATE-08 | 20-04, 20-05, 20-06 | ✓ SATISFIED | ✗ `[ ]` unchecked | INCONCLUSIVE over a would-be PASS; `REPLICATION_PENDING_MARKER` is one constant read by both the branch and the promotion rule; no `provisional` identifier, string or comment anywhere (AST + normalized-source scan) |
| GATE-09 | 20-05, 20-06 | ✓ SATISFIED | ✗ `[ ]` unchecked | Six outcomes observed firing; destroyed-model fixture built from Phase 19's real published M1 readings, four fields asserted against the parsed artifact; subprocess twin re-runs it in CI |
| GATE-10 | 20-05, 20-06 | ✓ SATISFIED | ✗ `[ ]` unchecked | Total dispatch proved at import; both named branches fired; unset fallback tolerance raises naming D-26 |
| CAL-04 | 20-01, 20-05, 20-06, 20-07 | ✓ SATISFIED | `[x]` | `K_RUNGS` + `ratchet_k` + `promote_to_full_fidelity` all committed at 20-05, all preceding the first artifact |
| RPT-02 | 20-03, 20-06 | ⚠️ PARTIAL BY DESIGN | `[ ]` unchecked | Helper exists with its differential proof (SC5's literal requirement — VERIFIED). The requirement's second clause, "**is used for correction sweeps**", has exactly one non-self-referential call site (`test_phase20_prereg.py:957`, scanning the pin's comments). Correction sweeps are report-time work. **Legitimately deferred, but the deferral is recorded only in 20-03-SUMMARY.md, not in REQUIREMENTS.md.** |

**Orphaned requirements:** none. `grep -E "Phase 20" .planning/REQUIREMENTS.md` maps exactly the
twelve IDs the plans claim; no ID is expected of this phase that no plan claimed.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | `TBD` / `FIXME` / `XXX` | — | **None.** All five phase-modified files scanned; zero debt markers. The debt-marker gate is clean. |
| — | — | `TODO` / `HACK` / `PLACEHOLDER` | — | None |
| `scripts/mitigation_gate.py` | 798-812 | Two statistics compared against one ceiling | 🛑 Blocker (against SC3) | CR-01 — see crux |
| `scripts/mitigation_gate.py` | 800-801 | Pair-valued criterion checked on one leg | ⚠️ Warning | WR-09 — the held-out Y axis has no coverage check and no parameter to give it one |
| `scripts/mitigation_gate.py` | 595-634 | `retention_cap` validates only the sign of its floor | ⚠️ Warning | WR-01 — `extraction_ceiling` gets three provenance `_prove`s; the retention floor gets none, so a borrowed floor reaches (c) silently. The asymmetry is undocumented. |
| `results/phase20_retention_floor.json` | — | No committed test reads it | ⚠️ Warning | WR-02 — the artifact→`retention_cap` coupling is prose-only; CI watches neither side |
| `scripts/mitigation_gate.py` | 320-329 | `MITIGATION_GOAL_FRAMING` referenced nowhere | ℹ️ Info | IN-09 — module data with no reader; harmless, and frozen |
| `scripts/mitigation_gate.py` | 1283+ | `__main__` uses bare `assert`, strippable under `-O` | ℹ️ Info | IN-06 — contradicts `_prove`'s own stated rationale, but the pytest twin re-asserts every outcome in CI, so the self-check is not the only witness |

No stub patterns. Every `return` in the pin is a computed value; `FIXTURE_*` dicts are labelled
inputs to a demonstration, and four of their fields are asserted against a parsed published artifact.

---

## The GATE-02 supersession: is marking it complete honest?

The brief asks this directly, so here is a direct answer with the arithmetic I ran rather than the
arithmetic the SUMMARY quotes.

**What GATE-02 literally says** (REQUIREMENTS.md:31-35): condition (c) is computed from four
constants imported from `erasure_gate.py` — including `V20_RETENTION_NOISE_FLOOR` 0.068930 —
"yielding `dialogue_cap` 4.5837288963367 and `retention_cap` 4.029000."

**What the pin does.** It deliberately does NOT import `V20_RETENTION_NOISE_FLOOR` (a test asserts
its absence from a five-name import list checked by equality), and it does NOT produce 4.029000. The
governing v4.0 cap is 3.9085032379884783. So GATE-02 as written is **not** satisfied on one of its
four named constants and one of its two stated yields.

**Verdict: marking it `[x]` with the recorded supersession is HONEST, and is the better of the two
available options.** Three reasons, in order of weight:

1. **The supersession cannot buy an easier result.** I computed both caps from the committed code:
   3.9085032379884783 against 4.029, from a measured floor 7.94× smaller than the borrowed one. The
   amendment makes condition (c) **harder** to clear. A self-serving amendment moves a threshold the
   other way. This is the single strongest piece of evidence and it is arithmetic, not narrative.
2. **The borrowed value was measurably wrong for the regime it would have governed.** 0.068930 is a
   Phase 12 **full-fine-tune** seed pair; v4.0 verdicts are **adapter-regime**. The artifact's
   `governs` field states the mirror of what `results/phase19_noise_floors.json` already says about
   the full-fine-tune *dialogue* floor — Phase 19 caught that defect on one leg and left it
   unremarked on the other. Correcting it is closing a known defect, not inventing a licence.
3. **Nothing is hidden.** The supersession is recorded in three places — the REQUIREMENTS.md
   traceability row, a dated inline amendment in ROADMAP SC1, and the artifact's machine-readable
   `governs` field (the shape `results/phase19_calibration_correction.json` already established).
   The requirement text was deliberately NOT edited, which is the correct treatment of a
   pre-registration record. `erasure_gate.py:246` still computes 4.029 for Phase 19 and is
   explicitly not corrected.

**Why reverting to unchecked would be worse.** An unchecked box carries no note into a milestone
rollup. It would read as "Phase 20 failed to do this", which is false about the mechanism, and it
would make the supersession *less* visible, not more.

**The residual risk, stated rather than glossed.** A `[x]` is machine-readable; the supersession note
beside it is not. An automated audit that counts checkboxes will report GATE-02 satisfied *as
written*, and a reader who greps `4.029000` in REQUIREMENTS.md finds an unamended requirement. That
is a WARNING, not a BLOCKER — the substance is recorded in three places including a machine-readable
artifact — but it is a real gap between what the checkbox asserts and what the code does.

## Over-claim-avoidance discipline: did it hold?

**Yes for 20-01 through 20-06, and then it broke at the hand-off.** Twelve applications are recorded,
one per plan-summary, each declining to mark a requirement also claimed by a later plan. That is
genuine discipline and I found no instance of a plan marking a requirement it had not discharged.

But the twelfth application (20-06) deferred **GATE-01 through GATE-10 and RPT-02** to 20-07 — and
20-07's frontmatter claims only `[GATE-02, CAL-04]`, so its "Requirements assessed" table assesses
only those two. Eight IDs that ARE genuinely discharged in the committed code fell through the gap
and were never marked. Over-claim-avoidance ran one application past its useful life and became a
terminal under-claim.

**Nothing is marked complete that is not genuinely discharged.** I checked the two that are marked:
CAL-04 is fully discharged (the rules landed at 20-05 and 20-07 is where the "before any v4.0
artifact exists" clause becomes provable rather than vacuous — `checked` went 0→9). GATE-02 is
assessed above. **The failure is under-claiming, not over-claiming**, which is the safer direction
but is still a traceability gap the milestone audit will trip over.

---

## Human Decision Requested (Escalation Gate)

Three items where automated verification has taken the question as far as evidence can and a human
owns the call.

### 1. Accept or reject the GATE-02 `[x]`-with-supersession treatment

**Test:** Read REQUIREMENTS.md:31-35 and its traceability note at :272, then decide whether a
checked box on a requirement whose stated yield the phase deliberately does not produce is the
record you want carried into the milestone audit.
**Expected:** Either confirm the current treatment (my assessment: defensible, and the amendment is
tighter — verified arithmetically), or amend the requirement text with a dated in-place amendment in
the same style ROADMAP SC1 already uses.
**Why human:** This is a policy question about how a pre-registration record is amended, not a
question about code. The evidence is unambiguous; the convention is a judgment call.

### 2. Decide the CR-01 remediation route before Phase 23

**Test:** Decide whether `sweep_extraction_rates` will be supplied in Wilson-bound space (a caller
convention, no new code in the pin) or whether the coverage rule is corrected by a dated continuation
artifact — and record the decision NOW.
**Expected:** A committed `results/phase20_gate_coverage_correction.json` with a `governs` field, plus
an armed tripwire in an unpinned test.
**Why human:** The parameter's space is **undocumented** in the pin, which means a Phase 25 caller
could pass Wilson bounds and the comparison would become consistent *without any edit*. That is the
cheap fix — and it is also a researcher degree of freedom, because choosing it *after* seeing that
raw rates return INCONCLUSIVE would be exactly the post-hoc latitude pre-registration exists to
remove. Whichever route is chosen, it must be chosen and dated **before** Phase 23 measures anything.

### 3. Accept or close the un-coverable held-out Y leg (WR-09)

**Test:** Decide whether GATE-06's Y-axis coverage checking only `sweep_taught_recalls` is an
accepted, written-down hole or is corrected through the same continuation artifact.
**Expected:** Either a recorded acceptance naming the cost, or a correction.
**Why human:** Unlike CR-01 this cannot be fixed by a caller convention — the `sweep_heldout_recalls`
parameter does not exist and the file is frozen. Someone has to decide whether the pair-valued Y that
SC2 makes load-bearing is allowed to have half its coverage check missing.

---

## Gaps Summary

**The phase goal is achieved.** Every rule that will judge a v4.0 number is committed, and the
ordering was verified against the commit DAG in my own process: nine pin commits, then the first
v4.0 number two hours later, with the cost calibration still unrun. The ancestry guard is live and no
longer vacuous, the file is genuinely frozen (`git rm` + re-add cannot launder it, proven across five
states in a throwaway repo that CI re-executes), and the pin is stdlib-plus-one-sibling with every
instrument imported by object identity rather than copied. That is a real pre-registration and it
does what a pre-registration is for.

**It ships one real defect and one bookkeeping gap.**

The defect is CR-01, in GATE-06, and it is worse than recorded: the coverage test reads raw rates
against a Wilson-space ceiling, which I reproduced producing **both** a spurious INCONCLUSIVE on a
genuinely bracketing sweep **and** a suppressed INCONCLUSIVE — a decisive FAIL — on a genuinely
truncated one. The second direction is not in REVIEW.md and contradicts the "conservative only"
framing. The narrower and more important claim survives: it cannot manufacture a spurious PASS under
self-consistent inputs, so no v4.0 headline can be inflated by it. A second hole in the same block
(WR-09) leaves the held-out leg of a pair-valued Y with no coverage check and no parameter to give it
one. Neither is fixable in place. The review prescribed the dated-continuation remediation and **none
of it has been committed** — no correction artifact, no `append_addendum` call, no tripwire.

The bookkeeping gap is that eight of twelve requirement IDs are genuinely discharged in code and
still sit unchecked, because the over-claim-avoidance pattern was applied one plan past its useful
life: 20-06 deferred them to 20-07, and 20-07 assessed only the two IDs in its own frontmatter.
GATE-06 is correctly unchecked. RPT-02 is correctly unchecked but its deferral is recorded only in a
SUMMARY, not in REQUIREMENTS.md.

**Neither gap blocks Phase 21**, which does not consume GATE-06. Both must close before Phase 23,
which is where Z's sweep width is set and where sweep coverage stops being hypothetical.

---

_Verified: 2026-08-20T23:14:01Z_
_Verifier: Claude (gsd-verifier) — goal-backward, FORCE stance_
