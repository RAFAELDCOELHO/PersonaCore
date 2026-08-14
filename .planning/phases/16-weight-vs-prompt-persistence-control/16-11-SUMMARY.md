---
phase: 16-weight-vs-prompt-persistence-control
plan: 11
subsystem: evaluation
tags: [PERS-02, PERS-03, PERS-04, STAT-01, STAT-02, STAT-03, STAT-05, STAT-06, four-arm, real-weights]
key-files:
  created:
    - results/phase16_persistence_report.md
    - results/phase16_persistence_raw.log
    - results/phase16_arm_adapter-only.json
    - results/phase16_arm_base-neither.json
    - results/phase16_arm_embedding-cosine.json
    - results/phase16_arm_prompt-stuffed.json
  modified:
    - scripts/phase16_persistence.py
    - tests/test_phase16_stats.py
    - tests/test_phase16_driver.py
    - .planning/phases/16-weight-vs-prompt-persistence-control/16-CONTEXT.md
metrics:
  wall_clock_min: 137.2
  arms: 4
  questions_per_arm: 270
  draws_per_question: 9
  holm_pairs_cleared: 3
  holm_family_size: 6
  sweep_cells: 7
---

# 16-11: The four-arm persistence comparison on the real weights

## What was done

Four arms in four fresh processes, 270 questions x 9 draws each, **137.2 min** on MPS.

| arm | pid | wall clock | pooled (gated `held-out`) | two-stage cluster bootstrap 95% |
|---|---|---|---|---|
| `adapter-only` | 16115 | 10.6 min | **90/104 = 0.865385** | (0.721154, 0.971154) |
| `base-neither` | 23448 | 13.8 min | 0/104 (RoT ≤ 0.028846) | (0.0, 0.0) |
| `embedding-cosine` | 26135 | 0.2 min | 0/104 (RoT ≤ 0.028846) | (0.0, 0.0) |
| `prompt-stuffed` | 26193 | 112.6 min | 0/104 (RoT ≤ 0.028846) | (0.0, 0.0) |

Four distinct pids and one shared `git_sha` — D-01's process split is evidenced by the artifacts
rather than asserted, and `assert_arms_are_pairable` passed.

## The gate

**3 of 6 Holm pairs cleared.** All three adapter pairs reached 8/8 unanimity at
`p = 0.0078125` against a first-step alpha of `0.0083333` — the pre-registered 6.7% relative
margin, unchanged. The three floor pairs tied 0/8 and returned `p = 1.0`.

**That last row is D-29 earning its keep on real data.** Under a pure two-sided test those three
all-tied pairs would each have returned `0.0078125` and entered the Holm family as SIGNIFICANT —
three false positives in the over-claiming direction. D-08 originally claimed 0/8 gives `p = 1.0`
and was wrong; D-29's direction filter is what actually delivers it. The defect fix was written
before any number existed, and the real data exercised exactly the case it was written for.

## Three pre-registered qualifications, emitted structurally

All three are module-level constants rendered into the report and pinned by tests, so none depends
on a reader or a future editor remembering them:

1. **D-30 (recorded before the run).** The 8/8 result is consistent with BOTH "personalization
   lives in the weights" and "prompt-stuffing is structurally incapable at this span length", and
   this experiment cannot separate them. Measured basis: gate-cleared synthetic span-5 ladder cells
   scored 0/216 each and the real-value top rung scored 0/216, against real value token lengths
   `[4,4,4,5,5,6,8,8]` (median 5). Licensed: **at this scale**, weight-based memory achieves what
   prompting cannot. Not licensed: a general mechanism win.
2. **The ladder's `proxy_consistent` is declined as validation** — both compared cells scored zero,
   so they agree trivially.
3. **D-25's closed-set floor** (0.05, derived as `1/len(candidate_pool())`) qualifies any result
   favourable to arm D.

## PERS-03: seven cells, all zero, and uninformative

All seven sweep cells scored **0/270**. The report states plainly that this is uninformative about
context-pressure degradation, because there was no baseline signal to degrade: the arm entered the
sweep at the capability floor the ladder had already measured. It supports only *"no measurable
effect was observable given zero baseline recall"*, never *"context pressure had no effect"*.

Cells 46-224 carry the fact inside the window and still score zero (capability floor); cells
320/448 push it outside the 256-token window entirely, so their zero is expected by construction.

## Deviations

**1. A real defect was found in the first assembly and fixed before approval.** The report
published `adapter-only` at rate `0.865385` beside a 95% interval of `(0.208333, 0.489316)` — the
point estimate outside its own bounds. Root cause: `cluster_bootstrap` returned `sum(k)/sum(n)`,
the DRAW-level rate (~0.33 on this tier), while the pooled column publishes the QUESTION-level
answerable rate (~0.87). Two different statistics printed as though one described the other, and a
STAT-01 violation in the one place STAT-01 is most explicit.

Fixed to the question unit (`1 if k > 0 else 0` per resampled question). Guarded generically by
`test_cluster_bootstrap_interval_brackets_its_own_point_estimate`, observed RED against the shipped
code — interval `(0.259615, 0.304487)` vs point estimate `0.846154` — and GREEN after.

Two things worth recording about that test. The FIRST fixture written for it PASSED against the
defect, because a small fixture yields an interval wide enough to swallow both units; it was
replaced with one mirroring the real gated tier (8 facts x 13 questions). And
`test_cluster_bootstrap_is_deterministic_under_its_seed` then needed WITHIN-fact variation, because
`_balanced_fixture` gives every question in a fact the same `k` and the question-level statistic
collapses to "fraction of facts with k>0" — nine possible values, two seeds landing on identical
percentiles. That made its seed-sensitivity assertion unexercisable rather than false. Fixed in
that test only; the shared helper and its three other users are untouched.

**The gate verdict is unaffected** — the sign test reads per-fact ordering, not the interval.

**2. Provenance split, stated rather than hidden.** The four arms were recorded at
`git_sha dc9d6c1`. The report was assembled at a later HEAD, after the bootstrap unit fix
(`1b8e04a`) and the sweep caveat (`8401515`). **No arm was re-run**; `results/phase16_arm_*.json`
are byte-unchanged, and only report-generation code advanced.

**3. D-30 and the D-28 reading qualification were added mid-plan**, both before the arms they
qualify were scored. D-28's permission is UNCHANGED (`monotone_claim_allowed("span_2")` still
returns `True`); it gained the same contextual discipline already applied to `proxy_consistent`.

**4. Arm A was launched once, completed, and discarded** because a commit landed between its run
and the others, which would have broken `assert_arms_are_pairable`. Re-run at the shared SHA; ~10
min lost, no data reused.

## Operational practice, carried forward to Phases 17 and 18

1. **Launch detached and VERIFY it** — `nohup <cmd> > log 2>&1 &` then `disown`, confirm
   `ps -o ppid= -p <pid>` returns **1**. `setsid` does not exist on macOS; naming it in a plan is
   not applying it.
2. **Wrap in `caffeinate -ims`, inside the run tree** so the assertion lives and dies with the run.
   Verified here: caffeinate ran as a CHILD of the run process, sharing its process group.
3. **The repository is commit-frozen for the duration of a multi-arm run** —
   `assert_arms_are_pairable` requires one `git_sha` across all arms, so any commit between the
   first and last arm makes `--report` refuse. Land commits before launching, or after the last arm
   writes.

## Verification

- four arm JSONs, 270 records each, one shared `git_sha dc9d6c1`, four distinct pids
- `assert_arm_parity` executed (not merely defined) — 16-10 wired it and this run exercised it
- every rate carries a denominator and a bound; every zero carries `rule_of_three`
- `grep -cE '\b0(\.0+)?%'` over the report returns **0** — no bare zero percent
- the bootstrap interval brackets its own point estimate for every arm
- full suite: **577 passed, 1 skipped**

## Self-Check: PASSED
