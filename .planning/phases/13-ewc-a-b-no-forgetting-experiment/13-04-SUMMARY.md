---
phase: 13-ewc-a-b-no-forgetting-experiment
plan: 04
subsystem: evidence
tags: [ewc, continual-learning, report, honest-evidence, reconciliation, threats-to-validity]

# Dependency graph
requires:
  - phase: 13-ewc-a-b-no-forgetting-experiment
    plan: 01
    provides: pre-registration preamble + committed MARGIN/ewc_mitigates constants
  - phase: 13-ewc-a-b-no-forgetting-experiment
    plan: 02
    provides: both arm CSVs, gate inputs, D-11 cross-check result, MPS non-determinism finding
  - phase: 13-ewc-a-b-no-forgetting-experiment
    plan: 03
    provides: VIZ-01/VIZ-04 figures, D-12 retention samples + the role-token leakage finding
provides:
  - results/phase13_ab_report.md — the complete committed A/B evidence report (DEMO-04)
  - "Scoped claim for Phase 15: EWC mitigates MEASURED forgetting (teacher-forced retention PPL, 33.6x margin); NOT qualitative/generative retention"
  - D-09 reconciliation narrative (SEARCH vs DEMONSTRATION) for the writeup
affects: [phase-15-writeup]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Threats-to-validity register that LEADS with the phase's own negative result rather than appending it"

key-files:
  created: []
  modified:
    - results/phase13_ab_report.md

key-decisions:
  - "13-04: the retention/generation gap (79/70 role-token leakage) is threat #1 in the register, not a footnote — the report's claim is explicitly scoped to teacher-forced retention PPL and states in two places that qualitative retention is NOT claimed"
  - "13-04: the two reproducibility claims are stated as distinct rows in one table — weights and free-running generation are bit-identical across processes, eval PPL is NOT (~1e-8); the report explicitly disclaims bitwise eval reproducibility"
  - "13-04: the 33.6x margin ratio is framed as the REASON the borrowed floor is judged acceptable, never as proof the transferability risk is absent; the un-run honest alternative (seed pair at 4000 unmasked steps, ~75 min) is named"
  - "13-04: D-05 obligation 3 (within-run trajectory) reported as a full 16-interval table with the observation that all three downward excursions are smaller than MARGIN — corroboration, explicitly labeled not a re-measurement"

requirements-completed: [DEMO-04]

# Metrics
duration: 18min
completed: 2026-08-01
---

# Phase 13 Plan 04: A/B Evidence Report Summary

**`results/phase13_ab_report.md` completed: a 2×2 end-of-run headline (both axes, both arms), the pre-registered retention gate holding at 33.61× MARGIN, the D-11 reproduction MATCH to bit-identity in weights, and a threats register that leads with the phase's own negative result — free-running story mode does not survive in either arm, so the claim is scoped to teacher-forced retention PPL and says so.**

## Performance

- **Duration:** ~18 min
- **Tasks:** 2
- **Files modified:** 1 (7 placeholder sections filled + an evidence index)

## What the report now says

### The 2×2 (step 4000, D-08 — read verbatim from the committed arm CSVs)

| Arm | λ | Acquisition (masked dialogue val PPL) | Retention (frozen sub-bin PPL) |
| --- | --- | --- | --- |
| step-0 anchor | — | 31.903875386436905 | 2.107553076833866 |
| naive | 0 | 4.192794562524908 | 8.52417066884246 |
| EWC | 0.01 | 4.573349242745997 | 3.8911400839446597 |

Both arms learn the task to within 0.38 PPL of each other and differ by 3.6× in retention drift
(+6.416618 vs +1.783587). Both columns are in the headline — DEMO-04's "retention-only is the
classic sleight of hand" is the reason the acquisition column is not optional.

### Gate verdict

`ewc_mitigates(8.52417066884246, 3.8911400839446597)` → delta **4.633030584897801** > MARGIN
**0.137860** → **True**, at **33.61×** the margin (67.2× the raw floor). Acquisition cost
**+0.380556** PPL reported descriptively with an explicit "no pass/fail gate on acquisition
(D-06)" sentence.

### D-11 cross-check

MATCH. `ewc_penalty` is **bit-identical** to `finetune_prod.csv` (0.13435843586921692); eval PPL
differs by 1.08e-7 (retention) / 2.85e-8 (dialogue) — six orders inside MARGIN. Since
`ewc_penalty` is a pure function of the weights, bit-identity there is the stronger statement:
the weights after 4000 steps agree exactly. The same argument is recorded for the step-250 twin
check, where the plan's PPL-equality test was replaced (13-02) by `train_loss` / `ewc_penalty`
bit-identity.

### D-05 obligation 3 — naive-arm within-run trajectory

All 16 interval deltas tabulated. 13 up, 3 down; range [−0.062183, +2.915207]; excluding the
0→250 collapse step everything lies in [−0.062183, +0.505]. **All three downward excursions are
smaller than MARGIN** — monotone up to sub-margin jitter, no late-run instability. Reported as
corroboration for the floor's transferability, explicitly not a re-measurement.

## The four honesty obligations, and how each landed

1. **Retention/generation gap — threat #1, not a footnote.** The register opens with it:
   79 (naive) / 70 (EWC) mid-story role-token leakage, 0/20 and 1/20 eos termination, both arms
   dropping into PersonaChat within a few tokens of a TinyStories prefix. The report states that
   this is a measured result rather than a harness defect, explains why it does not contradict the
   gate (teacher-forced retention PPL vs free-running mode adherence are different quantities),
   and then **scopes the claim in the Gate Verdict section too**, so a reader who stops after the
   verdict still cannot carry away "EWC preserves story generation". It also names what was not
   run: a stronger λ, a replay term, or a longer anchor budget.
2. **MPS eval non-determinism — in the register, as a risk category.** ~1e-8 relative on
   `dialog_ppl`/`retention_ppl`/`val_loss`, attributed to multi-batch reduction order, 7+ orders
   below MARGIN. The report says in bold that it **does not claim bitwise eval reproducibility**,
   and frames the D-11 MATCH as evidence-based determinism, not a guarantee.
3. **Free-running generation IS bit-identical across processes** — stated as its own row in the
   same table, distinct from (2), with the mechanism (single-batch forwards, no multi-batch
   reductions) given as the reason the two claims differ.
4. **The sharper step-250 discriminator** — recorded in the D-11 section as a named substitution
   (the plan asked for PPL equality; weight-derived bit-identity was used instead and is stronger),
   not smoothed into "the twin check passed".

Also carried: the MARGIN 0.137860-vs-0.137861 note was already in the pre-registration table from
13-01 and is left byte-unchanged; the report computes everything from 0.137860.

## D-09 reconciliation

One section, a 5-row comparison table, and §8 quoted verbatim ("EWC not demonstrable at this
budget … λ\* = None, demonstrable = False") with an explicit "stands unamended". The load-bearing
explanation: §8's dual rule failed on the **dialogue** side — it demanded EWC cost nothing
measurable (Δ_dialog floor 0.001704, K=2 → 0.003408), a near-impossible bar — while **every** λ
arm beat the collapse baseline on retention. Phase 13 asks the smaller answerable question and
pays the acquisition cost as a reported number rather than gating it away. λ=0.01 is the headline
because both axes move (D-02); λ=100 is named as the half-phenomenon it is. The ROADMAP's
"λ=0 vs λ\*" wording is recorded as superseded (λ\*=None).

## Task Commits

1. **Task 1: measured sections (2×2, gate verdict, D-11, trajectory)** — `bc11455` (docs)
2. **Task 2: narrative sections (threats, reconciliation, figures, samples, index)** — `c977a32` (docs)

## Decisions Made

- **Threats register ordered by load, not by plan order.** The plan listed the floor regime first;
  the leakage finding is the limitation that most changes how the headline may be read, so it
  leads. The D-05 obligations are all present, just not first.
- **Claim scoping repeated in the Gate Verdict section.** Duplication is normally noise, but a
  reader who reads the verdict and skips the register is exactly the failure mode 13-03 warned
  about, so the scope sentence sits at both locations.
- **Added an `## Evidence Index` beyond the seven planned sections.** Eight rows mapping every
  artifact to its role, with the λ=0 provenance exception called out — makes T-13-10 (numbers
  provenance) checkable at a glance instead of by grep.
- **The un-run alternative is named.** The threats section states that the honest fix for the
  borrowed floor is a 1337/2024 seed pair at 4000 unmasked steps (~75 min) and that it was not
  run — a limitation with its remedy stated is checkable; one without is a hedge.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Line-wrap broke the Task 1 verification grep**

- **Found during:** Task 1 verification
- **Issue:** The naive-arm footnote wrapped as `**measured,\nnot applied**`, so the plan's literal
  `'measured, not applied' in t` check failed on a purely cosmetic line break.
- **Fix:** Reflowed the sentence so the phrase sits on one line.
- **Files modified:** `results/phase13_ab_report.md`
- **Verification:** Task 1 automated check passes.
- **Committed in:** `bc11455`

---

**Total deviations:** 1 auto-fixed (1 blocking). No scope change; all seven placeholder sections
filled as specified plus the evidence index.

## Verification

- Both plan-specified automated greps pass.
- `git diff -U0` on the report at Task 1 removed exactly three lines — the three `_Pending_`
  placeholders — so the **pre-registration table is byte-unchanged** from `8fa2aa1` (T-13-11).
- `.venv/bin/python -m pytest tests/ -x -q` → **284 passed, 1 skipped**.
- `git status --porcelain results/` empty after the Task 2 commit.
- `2.1066` appears exactly **once** in the report (the figures section) — Pitfall 3 held.
- `Pending` appears **zero** times — no placeholder survived.
- Every 2×2 / gate / D-11 figure re-derived from the committed CSVs in this session rather than
  transcribed from 13-02's SUMMARY; all matched.

## Requirement Closure

**DEMO-04 is marked complete by this plan** — and only now. Plans 13-01/02/03 each declined the
mark (13-01 actively reverted an automatic one), because DEMO-04 requires both retention AND
acquisition to be *reported*, not merely measured. The 2×2 table reports both; the report
additionally scopes what "retention" means here, which is what makes the mark honest rather than
green.

VIZ-01 and VIZ-04 artifacts shipped in 13-03 and are referenced by path from the report.

## Next Phase Readiness

Phase 15 consumes this narrative verbatim. The three things it must not soften:

- The claim is **measured (teacher-forced) retention**, 33.6× margin. Not generative retention.
- Eval PPL is not bitwise reproducible on MPS; weights and generation are.
- §8's λ\*=None stands; the reconciliation is the explanation, not a retraction.

## Self-Check: PASSED

`results/phase13_ab_report.md` exists and is tracked; both task commits (`bc11455`, `c977a32`)
present in git log; all four referenced evidence artifacts
(`results/phase13_forgetting_curve.png`, `results/phase13_frontier.png`,
`results/phase13_retention_samples.md`, both arm CSVs) exist on disk and are tracked.

---
*Phase: 13-ewc-a-b-no-forgetting-experiment*
*Completed: 2026-08-01*
