---
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
verified: 2026-08-29T11:03:56Z
verified_at_head: 3820c4e599800f7031cab10cf31f36420ded2eb0
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
re_verification: null
human_verification:
  - test: >-
      Decide whether `.planning/REQUIREMENTS.md`'s DPSGD-06 record gets a dated
      retract-in-place continuation, the 23-12 treatment, before Phase 24 planning reads it.
      Reproduce the staleness with:
      `git ls-files 'results/phase23_noised_*' | wc -l`  (returns 1, the row says "still empty")
      and read `.planning/REQUIREMENTS.md:455` ("Plans 23-11 through 23-14 are BLOCKED;
      zero noised sweep points may run") against the four executed SUMMARYs.
    expected: >-
      Either a dated `RETRACTED IN PLACE` / discharge continuation is appended to the DPSGD-06
      inline body (line 156-160) and traceability row (line 455) — pointing at
      `results/phase23_matched_verdict.json` and the human unblock act `746ecf6` — or the
      developer rules the ROADMAP + STATE continuations sufficient and records that choice.
    why_human: >-
      The staleness is programmatically proven, but the remedy is a convention decision. This
      project spent an entire plan (23-12) retracting a false claim in this same file under
      exactly this convention; whether a second false claim in the same file, in the same
      phase, earns the same treatment is the developer's call, not the verifier's.
  - test: >-
      Decide whether the never-taught scoring path gets a committed positive control before
      Phase 25 (frontier lower-left floor) and Phase 27 (relearning reference) consume
      `extraction_noise_floor = 0.0` twice. The verifier ran the missing control and it FIRES —
      injecting one true fact value into one completion of the real seed-1337 draw set moves the
      gated reading 0/416 -> 1/416 through the unmodified `phase18_extraction.score_records`.
    expected: >-
      Either a test lands in `tests/test_phase23_ctrl.py` that watches the scorer register a
      constructed success on the retained draws (the same watched-RED discipline CAL-03 already
      has at `test_an_n_leak_into_t_is_detected`), or the developer records that the inherited
      Phase-18 coverage plus this verification's one-off falsification is sufficient.
    why_human: >-
      The zero is proven honest (see W-02 below), so this is not a gap in the measurement. It is
      a gap in the standing guard for a number two later phases consume. Whether that guard is
      owed before those consumers exist is a scheduling decision.
---

# Phase 23: Cost Calibration, the σ=0 Diagnostic, and Budget Pre-Registration — Verification Report

**Phase Goal (ROADMAP.md:148):** *Size the sweep from a measurement instead of an assumption, and
run the one cheap run that separates the milestone's most likely honest negative from its most
likely silent bug*
**Verified:** 2026-08-29T11:03:56Z at HEAD `3820c4e5`
**Status:** human_needed — 5/5 success criteria VERIFIED, two developer decisions requested
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria — the contract)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | The σ=0 point is the DP arm's **first executed run**, and it reproduces the unmitigated control within the seed-to-seed noise floor, recorded before any noised point exists (DPSGD-06) | ✓ VERIFIED | Ordering proved by git: σ=0 record first-add `2d06989` 2026-08-27T03:53:56 ≺ matched verdict `0a275c9` 19:59:36 ≺ first noised point `ab9d246` 2026-08-28T15:00:35. Reproduction proved **independently by the verifier**: the σ=0 DP adapter and the protocol-matched non-DP adapter at seed 1337 agree to a worst **relative** elementwise difference of `2.08770180316837e-06` (worst absolute `6.51925802230835e-08`) over all **72** LoRA tensors — two separately-executed runs, distinct files, distinct sha256s. Verdict re-derived live through the byte-unedited blind rule: `proceed`, deviation `0.0` ≤ floor `0.0267857142857143`. |
| 2 | Training wall-clock measured on the DP path with the seam active, and generation throughput **re-measured on one noised adapter**; the committed 4.77 h/point recorded as a **floor**, not a mean (CAL-01, CAL-05) | ✓ VERIFIED | `results/phase23_cost.json` (sha256 recomputed live = `f3ba4d9a…b8a47637`, matches every citation). `training.dp_n64`: `dp_seam_active: true`, `sigma: 0.5`, `seconds_total = 1383.276182374917` over `timed_iterations = 200`. `generation.adapter_sha256 = 5a1b10d6…` is the same dp_n64 σ=0.5 adapter, `n_draws_measured = 768`. `h_per_point_floor = 5.7223403197590965` h > the committed 4.77, so 4.77 is below the measured floor — disclosed as such in the REQUIREMENTS.md continuation. |
| 3 | Z (sweep width, per-point K, step budget) committed in `scripts/mitigation_budget.py` with `_PROVENANCE` siblings naming the cost artifact and its sha256, in a module the gate is AST-forbidden from importing (CAL-02) | ✓ VERIFIED | AST extraction of module-level constants: `SWEEP_POINTS = 16`, `CURVE_K = 16`, `FULL_FIDELITY_K = 48`, `STEP_BUDGET = 200`, `N_CONTROL_SEEDS = 5`, `N64_LEG_WITHDRAWN = False` — all literals, **zero import nodes in the module** (AST walk). `SWEEP_POINTS_PROVENANCE` / `CURVE_K_PROVENANCE` name `results/phase23_cost.json` + sha256 `f3ba4d9a…`, verified live against the bytes. AST import guard green: `tests/test_phase20_prereg.py` (4 passed) + `tests/test_phase23_budget.py:89 _FORBIDDEN` transitive probe. |
| 4 | The n=64 premise "ε is independent of N at q=1" **confirmed by a run** at n_facts=8 vs 64 at fixed σ, before the n=64 sweep is committed (CAL-03) | ✓ VERIFIED | `results/phase23_cal03_wiring.json` (sha256 `461d1d65…`, matches `N64_LEG_WITHDRAWN_PROVENANCE`): `epsilon_n8 == epsilon_n64 == 24.38161088311366`, `t_n8 == t_n64 == 4`, at `sigma = 0.5` / `delta = 1e-05` on MPS, `verdict: true`. `epsilon_for` signature confirmed by AST as exactly `(sigma, steps, delta)` — no N. The record's own `scope` field honestly declares it tests the **wiring** (whether `n_facts` leaks into T), which is the only falsifiable half. `tests/test_phase23_cal03.py` 11 passed, including the watched N-leak positive control. |
| 5 | A never-taught fresh adapter trained once at identical budget and seed protocol and **scored** — scheduled once, consumed twice (CTRL-03) | ✓ VERIFIED | `results/phase23_never_taught_training.json`: `capacity_n_facts: 0`, five seeds `[1337, 2024, 1338, 2025, 1339]`. Adapter sha256s are **identical** between the training record and `results/phase23_never_taught.json` (sha256 `94ad8434…`) at all five seeds — scheduled once, the same weights consumed. `consumers` is `['frontier lower-left floor', 'relearning reference']` in **both** records. Reading `0 / 416 core_held_out` at every seed, scored at `mitigation_budget.CURVE_K = 16`. Verifier independently re-derived seed 1337's `0/416` from the retained raw draws, and **falsified the "silent-zero scorer" hypothesis** (see W-02). |

**Score: 5/5 truths verified.**

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `results/phase23_sigma_zero.json` | DPSGD-06's σ=0 diagnostic record | ✓ VERIFIED | `verdict: HALT`, `reading = 0.7837301587301587` (790/1008), `clip_norm = 1000000.0`, `clip_bind_count = 0` over 200 steps. Verdict re-derives live through `phase23_prereg.sigma_zero_verdict` and raises the stored `halt_message` verbatim. |
| `results/phase23_matched_control.json` | the protocol-matched comparator | ✓ VERIFIED | Five independently-trained seeds (distinct adapter sha256s, distinct training/scoring seconds), readings `[0.7837301587301587, 0.7678571428571429, 0.7718253968253969, 0.7569444444444444, 0.7668650793650794]`, floor `= max − min = 0.0267857142857143`. Discloses `sigma_zero_was_visible: true` and `attempt: "continuation"` rather than hiding either. |
| `results/phase23_matched_verdict.json` | the D-04 re-test | ✓ VERIFIED | `verdict: 'proceed'`, `deviation: 0.0`, `deviation_over_floor: 0.0`. Verifier re-derived `'proceed'` live from the record's own inputs. |
| `results/phase23_cost.json` | CAL-01 + CAL-05 measured figures | ✓ VERIFIED | All 11 `published_figure_paths` resolve; file sha256 recomputed = every cited digest. |
| `results/phase23_noised_dp_n64_sigma0p500000.json` | the first noised sweep point | ✓ VERIFIED | sha256 `99d70adb…` matches `training.dp_n64.source_record_sha256`. ε `519.6981942303134`. |
| `results/phase23_cal03_wiring.json` | CAL-03's confirming run | ✓ VERIFIED | sha256 `461d1d65…` matches its `_PROVENANCE` citation. |
| `results/phase23_never_taught{,_training}.json` | CTRL-03's floor + its scheduling | ✓ VERIFIED | sha256s `94ad8434…` / `b4ee3fc3…` match every citation, including `N_CONTROL_SEEDS_PROVENANCE`. |
| `scripts/mitigation_budget.py` | the Z pin | ✓ VERIFIED | Literal-only, zero imports, six Z constants + six `_PROVENANCE` siblings. `CURVE_K_PROVENANCE.selected_reply_verbatim` carries the user's own reply, persisted. |
| `scripts/phase23_prereg.py` | the blind rule | ✓ VERIFIED | `git diff c7de5d4 HEAD` is **empty** — byte-identical to the blind commit. The verdict function was never edited. |
| `.planning/REQUIREMENTS.md` DPSGD-06 record | current traceability | ⚠️ STALE | Two statements false at HEAD. See W-01. |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| σ=0 arm | matched control arm | numerically equivalent weights at σ=0 with non-binding clip | ✓ WIRED | Verifier-measured: worst rel. elementwise diff `2.08770180316837e-06` over 72 tensors. |
| `phase23_matched_verdict.json` | `phase23_prereg.sigma_zero_verdict` | live call, byte-unedited rule | ✓ WIRED | Re-derived `'proceed'` in-process. |
| `mitigation_budget` Z constants | `results/phase23_cost.json` | `_PROVENANCE.record_sha256`, checked live | ✓ WIRED | `tests/test_phase23_budget.py` hashes the file on every suite run. |
| `mitigation_gate` | `mitigation_budget` | AST import guard (must NOT exist) | ✓ WIRED (correctly absent) | `tests/test_phase20_prereg.py:1180` + transitive out-of-process probe. |
| never-taught training | never-taught scoring | adapter sha256 identity across both records | ✓ WIRED | All five seeds match exactly. |
| never-taught draws | `phase18_extraction.score_records` | imported predicate + `{fact_id: value}` mapping | ✓ WIRED | Verifier re-derived 0/416 and proved the path fires on injection. |
| `generation.cross_validation_vs_phase18` | any assertion | — | ✗ NOT_WIRED | Computed, printed, stored; asserted nowhere. See W-03. |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Produces Real Data | Status |
|---|---|---|---|---|
| `results/phase23_never_taught.json` | `readings = [0.0]×5` | 69,120 dispatched draws → `score_records` | **Yes** — 13,824 real completions/seed, mean 47.3 chars, 27 empty of 13,824; 4,320 committed per-question rows | ✓ FLOWING (zero is honest, not hollow) |
| `results/phase23_cost.json` `generation.*` | h/point bracket | 768 timed draws on the real σ=0.5 adapter | Yes — `stop_terminated_n_floor = 232` vs `ceiling = 0`, `token_multiplier = 1.6456408196062675` | ✓ FLOWING |
| `results/phase23_cost.json` `training.dp_n64` | 1383.28 s | real `train_arm` run, `run.csv` committed | Yes | ✓ FLOWING |
| `mitigation_budget.CURVE_K` | 16 | `sizing["16"]` at `h_per_point_ceiling` | Yes — `total_hours_ceiling_with_never_taught_floor = 66.09021780091668` reproduces from the record's own table | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Full suite green | `.venv/bin/python -m pytest tests/ -q` | `1589 passed, 1 skipped` in 371.96s | ✓ PASS |
| Lint clean | `.venv/bin/ruff check . && ruff format --check .` | `All checks passed!` / `219 files already formatted` | ✓ PASS |
| Blind rule re-derives both verdicts | live `sigma_zero_verdict(...)` on each record's own inputs | matched → `'proceed'`; original → raises the stored HALT verbatim | ✓ PASS |
| σ=0 vs matched adapter equivalence | `torch.load` both, elementwise max rel. diff over 72 tensors | `2.08770180316837e-06` | ✓ PASS |
| Never-taught reading re-derives from raw draws | `score_records(draws, values)` on `data/phase23_never_taught_seed1337_draws.json` | `0 / 416` gated | ✓ PASS |
| **Scorer positive control** (the one WR-07 says is missing) | inject `'quillon'` into one completion of one gated question, re-score | `0/416` → **`1/416`** | ✓ PASS |
| Cited digests match bytes | sha256 over 6 result artifacts | all 6 match every `_PROVENANCE` / continuation citation | ✓ PASS |
| Phase-18 stop counts reproduce | cross-check vs `results/phase18_preflight_report.md:25-28` | `56/45/56/51` of 64 — exact | ✓ PASS |
| Ordering guard live | `pytest tests/test_phase23_prereg.py -k precedes` | 6 passed | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` exist in this repository and no PLAN declares one. **Step 7c: SKIPPED
(no probe convention in this project).** The equivalent runnable evidence is the pytest suite and the
seven in-process re-derivations above, all executed by the verifier.

### Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
|---|---|---|---|
| **CAL-01** | 23-05, 23-10, 23-11, 23-12 | ✓ SATISFIED | Four training legs in `results/phase23_cost.json`, each naming its own `protocol` and citing `source_record` + `source_record_sha256`. The research `~17 s/arm` estimate is retracted in place, not confirmed. |
| **CAL-02** | 23-02, 23-09, 23-13 | ✓ SATISFIED | Six Z constants + six `_PROVENANCE` siblings in a literal-only, zero-import module; AST import guard green; `CURVE_K` rung selected by the user at a blocking checkpoint, reply persisted verbatim. |
| **CAL-03** | 23-04, 23-13 | ✓ SATISFIED | `verdict: true`, ε and T equal across capacities under exact `==`; `epsilon_for` AST-proved to take no N; watched N-leak positive control present. ⚠️ Its checkbox at `REQUIREMENTS.md:298` carries **no inline `*SATISFIED …*` note** unlike its four siblings — the traceability row at `:453` is complete. Cosmetic. |
| **CAL-05** | 23-05, 23-11, 23-12 | ✓ SATISFIED | 768 timed draws on the real noised adapter; floor `5.7223403197590965` h exceeds the committed `4.77`, and the table's floor status is disclosed rather than left implicit. |
| **DPSGD-06** | 23-01, 23-03, 23-06, 23-07, 23-08, 23-10, 23-15…23-20 | ✓ SATISFIED (record stale) | Ordering + reproduction both proved; see truth 1. The **record** of it in REQUIREMENTS.md is out of date — see W-01. |
| **CTRL-03** | 23-08, 23-14 | ✓ SATISFIED | Trained once at `capacity_n_facts: 0`, scored once, adapter digests identical across both records, `consumers` identical in both. |

**Orphaned requirements:** none. `grep -E "Phase 23" .planning/REQUIREMENTS.md` maps exactly these six
IDs, and all six appear in plan frontmatter. **CAL-04** appears in the Phase-23 section of
REQUIREMENTS.md but is ROADMAP-assigned to Phase 20 and already ticked there — not orphaned.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|---|---|---|---|
| all phase-23 sources + tests | `TBD` / `FIXME` / `XXX` | — | **Zero found.** Debt-marker gate clean. |
| all phase-23 sources + tests | `TODO` / `HACK` / `PLACEHOLDER` | — | **Zero found.** |
| `scripts/phase23_run.py:3191-3213` | docstring names a guard the function does not have (WR-02) | ⚠️ Warning | The ordering claim is real but checked in the suite, not in-process. Verified true by git + `test_sigma_zero_precedes_every_noised_point`. Docstring accuracy only. |
| `scripts/phase23_run.py:3811-3835` | `training.non_dp.arm/.seed` are lists from **two independent sorts** while sibling blocks are scalars (WR-03) | ⚠️ Warning | Latent. Confirmed in the committed record; in *this* record both sorts happen to align (`[1337,1338,1339,2024,2025]`), so no published figure is wrong. `training_seconds_mean` is order-independent. |
| `results/phase23_cost.json` `generation` | no corpus digest recorded (WR-05) | ⚠️ Warning | Confirmed: `[k for k in generation if 'corpus' in k]` is empty, while `never_taught.per_seed[]` carries `corpus_sha256`. The h/point figures are not corpus-pinned. Does not change a number; weakens re-derivability. |
| `scripts/phase23_run.py` `throughput()` / crash-recovery writers (CR-01, CR-02) | work-destroying failure paths | ℹ️ Info (forward-looking) | Both legs already completed successfully; no Phase-23 must-have is affected. The never-taught leg already carries the per-shape-persistence fix (installed after a measured 2.3 h loss, documented in code at `:4460`). |
| `scripts/phase23_run.py` `noised()` state keyed by seed with no σ (CR-03) | mis-attribution risk | ℹ️ Info (forward-looking) | Exactly **one** noised point exists, so nothing is mis-attributed today. Becomes live the moment Phase 25 runs a second σ at the same seed. Not covered by any Phase 24/25/27 success criterion — recommend closing before Phase 25. |

---

## Findings the review raised, ruled on

### W-01 (WARNING, decision requested) — `.planning/REQUIREMENTS.md`'s DPSGD-06 record is stale at HEAD

Two statements in the DPSGD-06 traceability row (`:455`) are **false at HEAD**:

1. *"`git ls-files 'results/phase23_noised_*'` was asserted EMPTY … **and is still empty**"* —
   it returns **1** file, `results/phase23_noised_dp_n64_sigma0p500000.json`, added at `ab9d246`.
2. *"**Plans 23-11 through 23-14 are BLOCKED; zero noised sweep points may run**"* — all four
   executed; one noised point ran.

The inline body at `:156-160` likewise stops at *"D-04 HALTED the sweep"* with no discharge pointer.
`ROADMAP.md` and `STATE.md` both carry full dated discharge continuations; `REQUIREMENTS.md` does not.
This phase spent an entire plan (23-12) retracting a falsified claim in this same file under a dated
`RETRACTED IN PLACE` convention. Escalated as a decision, not fixed by the verifier.

### W-02 (WARNING, decision requested) — the CTRL-03 zero is HONEST; the standing guard is what is missing

The review's WR-07 claims the `0.0` floor "cannot be distinguished from a broken scorer". **The
structural half of that claim is accurate and the conclusion is false.** Ruled as follows:

*Accurate:* `_never_taught_evidence` (`phase23_run.py:4722`) re-scores through the **same**
`x18.score_records` with the **same** `{fact.id: fact.value}` mapping, so it is a re-derivation, not
an independent check. And the taught legs use a **different** scorer entirely (`tp.score_arm` via
`score_adapter`), so no non-zero Phase-23 reading comes off `score_records`. No committed positive
control exists in `tests/test_phase23_ctrl.py`.

*False conclusion — the verifier ran the missing control:*

```
BASELINE gated successes: 0 / 416
injecting value 'quillon' into fact cand_person_quillon family A1-mild
AFTER INJECTION gated successes: 1 / 416
```

Injecting one true fact value into one completion of the real seed-1337 draw set, re-scored through
the unmodified `phase18_extraction.score_records`, moves the gated reading `0/416 → 1/416`. The
scorer fires. Additionally: the retained draws are **real generated text** (13,824 completions per
seed, mean 47.3 chars, only 27 empty), and `score_records` `_prove`s both `fact_id in values` and
non-empty `completions`, so the two silent-zero paths are structurally closed.

**The zero is a measurement, not a bug.** What is missing is a *standing* guard for a number two
later phases consume twice — hence the decision request rather than a gap.

### W-03 (WARNING, no impact on any must-have) — `agreement_percent` is asserted nowhere

WR-01 verified exactly: `grep -rn "cross_validation\|agreement_percent" tests/` returns **nothing**.
The figure is computed at `phase23_run.py:3680`, printed at `:3689`, stored at `:3773`. The
`throughput()` docstring calls it a gate — *"A large divergence means the hardware or the stack moved
and the committed cost artifact needs revisiting BEFORE Z is sized on it"* — and no threshold, no
refusal and no test implements it.

**It does not undermine CAL-02.** Z is sized against `h_per_point_ceiling = 9.013691285839306` h,
which comes from **this phase's own** noised-adapter ceiling measurement (`sized_against` field on
`SWEEP_POINTS_PROVENANCE` and `CURVE_K_PROVENANCE`), not from the Phase-18 committed rates the
cross-validation compares against. Nothing load-bearing depends on it. The measured values would have
cleared any sane threshold anyway — `95.05660023069217%`, `96.18192392550253%`, `96.71578126506255%`,
`106.32486511219514%` — and the base-condition stop counts reproduce
`results/phase18_preflight_report.md:25-28` exactly (`56/45/56/51` of 64).

### 23-17's own account, checked against disk

**Consistent, and honestly so.** `23-17-SUMMARY.md` carries `status: INCOMPLETE` and
`NOT_provides: results/phase23_matched_control.json — NEVER WRITTEN`. Git confirms the sequence:
`d99d2aa` *"3 of 5 seeds — HARNESS-KILLED mid-seed-4, NO record written"* → `a629d93`
*"revert(23-20): discard seed 2025's partial training bytes"* → `04cdb21` the five-seed completion.
The final record's `prior_scored_seeds_at_start = ["1337","1338","2024"]` is exactly the three seeds
23-17 scored, and `attempt: "continuation"`. The ROADMAP box is `[ ]` with the reason stated. Nothing
in that SUMMARY over-claims.

---

## Gaps Summary

**There are no gaps against the phase goal.** All five ROADMAP success criteria are verified against
the codebase, not against SUMMARY narration — and the two load-bearing ones were re-derived
independently by the verifier rather than read out of a record:

- The *"one cheap run that separates an honest negative from a silent bug"* ran, fired `HALT`, was
  root-caused to an **invalid comparator** rather than a code defect, and the corrected comparator
  returned `proceed` through a **byte-unedited** rule (`git diff c7de5d4 HEAD -- scripts/phase23_prereg.py`
  is empty). The decisive evidence is not in any SUMMARY: the σ=0 DP adapter and the protocol-matched
  non-DP adapter agree to `2.08770180316837e-06` worst relative elementwise difference across all 72
  LoRA tensors. The DP seam is correct at σ=0. That is the phase's stated purpose, met.
- The sweep is *"sized from a measurement"*: `CURVE_K = 16` / `SWEEP_POINTS = 16` against
  `h_per_point_ceiling = 9.013691285839306` h, measured on the real noised adapter, with the rung
  chosen by the user at a blocking checkpoint and the reply persisted verbatim.

Two decisions are escalated rather than waved through: a stale traceability record for this phase's
own headline requirement (W-01), and a missing standing guard for a zero that two later phases
consume twice (W-02). Neither falsifies a success criterion. Both are the kind of thing this
project's own discipline closes rather than carries.

---

_Verified: 2026-08-29T11:03:56Z at HEAD `3820c4e5`_
_Verifier: Claude (gsd-verifier) — goal-backward, adversarial stance_
