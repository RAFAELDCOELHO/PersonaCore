---
phase: 19-selective-memory-erasure
plan: 16
subsystem: the-close
tags: [erase-01, erase-02, d3-dated-continuation, ship-decision, do-not-ship, append-only, closed-pin, cliff, rank-vs-nll, naming-failure-nine, phase-close]

requires:
  - phase: 19-selective-memory-erasure
    provides: "19-15's rendered `results/phase19_erasure_report.md` — 353 lines, sha256 `21624251…`, one `## Verdict` section carrying the committed `FAILURE`, ship marker PENDING"
  - phase: 19-selective-memory-erasure
    provides: "`scripts/_addendum.py` `append_addendum(path, addendum, *, pending, recorded)` — the ONE append-only writer with BOTH marker halves as required keywords (committed `f8441ec`, RED→GREEN over three mutations)"
  - phase: 19-selective-memory-erasure
    provides: "the CLOSED 15-commit pin — `append_ship_decision`, `ERASURE_SHIP_PENDING_LINE`, `ERASURE_SHIP_RECORDED_LINE`, `ERASURE_SHIP_DECISIONS`, `ERASURE_SHIP_DECISION_PREFIX`, `D8_PUBLICATION_POSTURE`, `assert_erasure_report_not_clobbered`"
  - phase: 19-selective-memory-erasure
    provides: "`scripts/erasure_gate.py` at `23a830c` — ONE commit, unamended, committed 2026-08-12 before Phase 16 ran"
  - phase: 14-teach-then-recall-demo
    provides: "`results/phase14_recall_report.md:462,585` — the adapter-PRESENT dialogue baseline 5.8154 (+27.16% over 270,203 scored targets), `COLLAPSE_PPL_TRIGGER` tripped and kept DESCRIPTIVE"
provides:
  - "`results/phase19_erasure_report.md` — 549 lines, sha256 `0f30b573…`, carrying the committed verdict, the dated (c) diagnosis BESIDE it, and the RECORDED ship decision"
  - "THE SHIP DECISION: **DO NOT SHIP**, dated 2026-08-19, recorded by the operator; marker flipped PENDING→RECORDED on a decision that actually exists"
  - "the withheld claim, named in one place and in plain words: the verdict is NOT mechanically reproducible by the pin alone"
  - "Phase 19 CLOSED — 16 of 16 plans, v3.0's fourth and final phase complete"
affects: []

tech-stack:
  added: []
  patterns:
    - "a correction to a published verdict is a DATED CONTINUATION BESIDE it, proved append-only on the DIFF (insertions only, apart from the one marker line the writer is defined to replace) rather than asserted in prose"
    - "a ship-decision marker flips ONLY on a continuation carrying a decision line from a CLOSED set plus a date — the conditionality is the whole mechanism, and it is Phase 18's W2 closed rather than repeated"
    - "a withheld claim is stated as ONE named claim with its mechanism, never as a vague reservation — a reader must not have to infer which claim was withheld or why"
    - "DO NOT SHIP on one claim is a FINAL verdict, not a blocker: the state file reads CLOSED, and the repair that would flip it is named as forbidden rather than left as an implied TODO"
    - "a state file with multi-line fields is repaired BY HAND when the SDK writer has corrupted it twice on the same single-line assumption"

key-files:
  created:
    - .planning/phases/19-selective-memory-erasure/19-16-SUMMARY.md
  modified:
    - results/phase19_erasure_report.md
    - docs/REPORT.md
    - .planning/REQUIREMENTS.md
    - .planning/STATE.md
    - .planning/ROADMAP.md

key-decisions:
  - "THE SHIP DECISION IS **DO NOT SHIP**, recorded by the operator and dated 2026-08-19. The marker flipped `ERASURE_SHIP_PENDING_LINE` → `ERASURE_SHIP_RECORDED_LINE` through the pin's `append_ship_decision`, which refuses unless the addendum carries a line from the closed `ERASURE_SHIP_DECISIONS` set AND a `YYYY-MM-DD` date. Measured after the append: PENDING ×0, RECORDED ×1"
  - "THE WITHHELD CLAIM IS EXACTLY ONE, AND IT IS NAMED AS THE SOLE REASON: that the verdict is MECHANICALLY REPRODUCIBLE BY THE PIN ALONE. It is not. The verdict was reached on a hand-driven path through the UNPINNED `scripts/phase19_run.py`, routing around four published defects in the CLOSED `scripts/phase19_erasure.py`. The pin's own `_cmd_report` cannot produce this verdict in four independent ways: C SystemExits on the committed per-fact rows, the fourth defect raises `TypeError` handing `retention_perplexity`'s `[ppl, n]` pair to the gate's scalar `retention_ppl=`, A short-circuits to INCONCLUSIVE on a key-order-only flag read, and B reads the superseded 0.2 floor rather than the governing `TARGET_FLOOR` 0.09107873950450847"
  - "NOTHING IS WITHDRAWN, AND THE CONTINUATION SAYS SO BEFORE IT SAYS ANYTHING ELSE. The `FAILURE` verdict, k = 78 of 288, the 77.6370113463966% destruction of the dialogue adaptation, the rank-vs-NLL disagreement AS CO-HEADLINE with its retroactive Phase 18 scope limit, the M1/M2 bit-identical-rank comparison, and all four defects with their dated corrections all stand exactly as published. DO NOT SHIP withholds a claim about reproducibility, not a measurement"
  - "DO NOT SHIP IS A FINAL VERDICT, NOT A PAUSE. STATE.md reads CLOSED and not BLOCKED. The continuation and STATE both name the forbidden repair explicitly — nobody should fix the pin to flip this decision, because editing a CLOSED 15-commit pin after the numbers exist is precisely what would void the pre-registration ordering `tests/test_phase16_prereg.py` enforces against git's object graph, and with it every number in section 1"
  - "THE REPORT WAS EXTENDED, NEVER RE-RENDERED, AND THE APPEND-ONLY PROPERTY WAS PROVED ON THE DIFF. `git diff --numstat` returns 84 insertions and exactly ONE deletion, and that deletion is the pending marker line the writer is defined to replace. The `## Verdict` body read by `_verdict.recorded_verdict` is byte-identical across the append, and the entire prior text reproduces verbatim modulo that one line"
  - "ERASE-01 IS DISCHARGED BY ARTIFACT REFERENCE AND NO CHECKBOX WAS MANUFACTURED. It is a scoped BULLET at `.planning/REQUIREMENTS.md:165`, and `requirements mark-complete ERASE-01` returns `not_found` because there is no `- [ ]` to tick. 19-09 and the 19-16 tasks-1-2 agent both declined to invent one; this agent declined for the third time. Both requirements are discharged in the Traceability table against RUNS, never against the written explanation the ROADMAP allowed as ERASE-02's alternative"
  - "`gsd-sdk query state.update` WAS NOT USED ON STATE.md. It corrupted that file twice in this phase on the same defect — it assumes single-line `Status:`/`last_activity:` fields where this project's are multi-line, mirrored a stale `stopped_at`, and flipped `status` wrongly. The repair was made by hand and verified line by line: frontmatter re-parsed with zero orphaned continuation lines"

metrics:
  duration: "26min (Task 3 and close; the plan spans a blocking human checkpoint between 7ddead8 and cf8a09a)"
  completed: 2026-08-19
  tasks: 3
  files: 5
---

# Phase 19 Plan 16: The Dated (c) Diagnosis, the Ship Decision, and the Phase Close — Summary

Phase 19 closes with its verdict published unsoftened, its root-cause diagnosis beside it, and one
claim withheld: **DO NOT SHIP**, because the verdict is not mechanically reproducible by the pin
alone.

## What happened

Tasks 1 and 2 landed before the checkpoint (`cd54535`, `7ddead8`): the dated condition-(c)
diagnosis appended BESIDE the literal verdict, and `docs/REPORT.md` continued with the cliff and the
rank-vs-NLL co-headline, with ERASE-01/02 discharged. Task 3 was a `checkpoint:human-verify` with
`gate="blocking"` — the executor stopped, the operator decided, and this continuation agent recorded
the decision.

## The ship decision

**`Phase 19 ship decision: DO NOT SHIP`**, dated 2026-08-19, written as a standalone literal line in
a dated continuation and appended through the pin's `append_ship_decision`.

That function is conditional by construction, and the conditionality is the point: it refuses unless
the addendum carries a line built from `ERASURE_SHIP_DECISION_PREFIX` plus one member of the closed
`ERASURE_SHIP_DECISIONS = ("SHIP", "DO NOT SHIP")` set, AND a `YYYY-MM-DD` date. Phase 18's W2 was a
rewrite that ran unconditionally and converted "not yet recorded" into "recorded" with nothing behind
it. Here the marker flipped because a decision was actually written.

### The three things the continuation states explicitly

**1. Nothing is withdrawn.** The continuation opens by enumerating what stands: the `FAILURE`
verdict with its three reasons; **k = 78 of 288** rank-1 components dispersed across every layer and
projection; the **77.6370113463966%** destruction of the dialogue adaptation; the rank-vs-NLL
disagreement published at **equal weight as a CO-HEADLINE** with its retroactive Phase 18 scope
limit (readings paired with a generation number are unaffected); the M1/M2 comparison in which the
rank instrument returns bit-identical readings while generation separates the adapters completely;
and all four published defects with their dated corrections.

**2. Exactly one claim is withheld, and it is named as the sole reason.** The verdict is not
**MECHANICALLY REPRODUCIBLE BY THE PIN ALONE**. It was reached on a hand-driven path through the
UNPINNED `scripts/phase19_run.py`, routing around four published defects in the CLOSED
`scripts/phase19_erasure.py`. Run over the same committed artifacts, the pin's own `_cmd_report`
cannot produce this verdict in four independent ways:

| defect | what it does to the pinned path |
| --- | --- |
| **C** — `rows.update(per_fact_rows(...))` in the (b) position | `_nontarget_rates` refuses the collapsed rows and the pinned `report` subcommand **SystemExits** (pinned as a committed test at 19-14) |
| **the fourth** — `_cmd_report` | hands `retention_perplexity`'s `[ppl, n]` pair to the gate's scalar `retention_ppl=`, raising **`TypeError`** |
| **A** — `zero_results_have_nll` | reads `False` on key order alone, so `erasure_succeeded` short-circuits to **INCONCLUSIVE** on the only outcome that clears (a) |
| **B** — `_calibration_rate()` | returns Phase 18's candidate recall 0.8846153846153846, so the pin's internal floor is the superseded **0.2** rather than the governing `TARGET_FLOOR` 0.09107873950450847 |

Every routing is disclosed in the report and every governing number was re-derived through a PINNED
function before the gate was called — but disclosure is not mechanical reproducibility, and the
project does not ship the weaker claim under the stronger word.

**3. The phase is closed and honest, not blocked.** DO NOT SHIP is a final verdict on mechanical
reproducibility — not a pause, not a TODO, not a gap for someone to close later. The continuation
and STATE.md both name the forbidden repair: nobody should fix the pin to flip this. The pin is
CLOSED at 15 commits, D3 fixes the correction path as a dated continuation beside the original, and
editing it after the numbers exist would void the pre-registration ordering
`tests/test_phase16_prereg.py` enforces against git's object graph — and with it every number in the
report. Withholding one claim costs the phase a claim; repairing the pin to recover it would cost
the milestone all of them.

## The verdict and its three clause readings, as they ship

**FAILURE**, returned by `erasure_succeeded` called exactly once against `23a830c`:

- **(a) clears — perfectly, and exactly on its boundary.** 0 successes over the pooled 27 (0/13
  held-out, 0/14 taught), 1,296 draws. Wilson upper bound `0.09107873950450847` is EXACTLY EQUAL to
  `TARGET_FLOOR`, headroom zero, branch `reachability-min`.
- **(b) fails on all seven gated non-targets.** Deltas 0.3704 … 1.0 against margin 0.2963, four at
  total generation loss. The smallest delta is 1.25× the margin. Every one of the seven still reads
  rank 1.
- **(c) fails on the dialogue leg.** 4.851119 against cap 4.583729 (+0.267390); the retention leg
  clears at −0.358082 only because the personalization is gone. Both legs were already red on the
  untouched adapter, so pre ships beside post in every table.

The 2026-08-19 (c) diagnosis (Task 1) publishes the root cause BESIDE that verdict without amending
it: the literal (c) caps against the adapter-**OFF** `V20_MASKED_DIALOGUE_VAL_PPL` = 4.5733, while
post-erasure capability preservation would have to be measured against the adapter-**PRESENT**
baseline 5.8154 that Phase 14 already published as a named limitation. Run through the committed
gate, a perfect erasure still returns FAILURE on (c) alone. Both readings ship side by side with the
gate's row labelled, and the diagnostic row is explicitly stated NOT to be a pass — its 0.974710 of
headroom IS the destroyed adaptation.

## The D8 branch, as committed before the number existed

`D8_PUBLICATION_POSTURE` clause 1 — **the cliff** — with the rank-vs-NLL disagreement elevated to
**CO-HEADLINE** by the operator at 19-12. *Selective erasure is not selective at 331,776
parameters*, shipped unsoftened. Its scope limit is a real limit and is stated rather than implied:
Phase 18 conclusions resting on rank or exposure bits ALONE must be re-read, while readings paired
with a generation number are unaffected — the pairing is what makes them safe, and this phase is the
argument for why the pairing was never optional.

## The phase-level pattern worth carrying into future planning

**Nine plan-instruction naming failures across 19-08 … 19-16.** The running count reached four at
19-11, five at 19-12 (`results/phase19_arm_m1.json` cannot exist — `arm_record_path` proves
`arm in ERASURE_ARMS` and the record is `phase19_arm_erased.json`), six at 19-13 (all three
plan-named artifacts refused by the pin, and both plan verify commands fail as written), eight at
19-15 (the Task-2 verify greps `Ship decision`, matching neither the pin's `Ship Decision` heading
nor its lowercase pending line), and nine at 19-16 (the plan names `results/phase19_arm_m2.json`
and `results/phase19_m2_training.log`; both are absent — the real ones are `phase19_arm_retrain.json`
and `phase19_retrain_training.log`).

The pattern is one rule: **read the constant, never the plan's spelling.** Every failure was a
planner writing a plausible artifact name or grep string from the narrative instead of from the
committed source of truth, and every one was caught only because a pin refused it at runtime. Two
carry-forwards for future planning: name artifacts by the constant that constructs them, and write
verify commands against the literal the code emits rather than the phrase the prose uses.

## Deviations from Plan

**None.** Task 3 was a blocking human checkpoint; the decision was the operator's, and this agent
recorded it as given. Two judgement calls inside the plan's own instructions:

1. **`gsd-sdk query state.update` was deliberately not used** on STATE.md. The plan's Task 2 said to
   use it "where it applies"; it corrupted this file twice in this phase on the same defect
   (single-line field assumption against multi-line fields, a mirrored stale `stopped_at`, and a
   wrongly flipped `status`). Repairs were made by hand and verified line by line — the frontmatter
   re-parses with zero orphaned continuation lines.
2. **No ERASE-01 checkbox was manufactured.** It is a scoped bullet, `mark-complete` returns
   `not_found`, and the third consecutive agent declined to invent one to tick.

## Verification evidence

All measured fresh in this session.

| check | result |
| --- | --- |
| report sha256 BEFORE | `3818ab5384f9d493564e66bc6ccad5a87fa98e0352743f68d4396c0eb4026dac` (466 lines) |
| report sha256 AFTER | `0f30b5733947f2985e0ed39a34d69e2b58fa78ad38bbc00965c02b6eba5010f1` (549 lines) |
| marker flip | PENDING ×1 → **×0**; RECORDED ×0 → **×1** |
| diff shape | **84 insertions, 1 deletion** — the deletion is exactly the replaced pending marker line |
| `## Verdict` body | **byte-identical** across the append; `FAILURE` present and unsoftened |
| prior text | reproduces **verbatim** modulo the one marker line |
| foreign provenance | `Phase 18 ship decision` mentions: **0** |
| `scripts/erasure_gate.py` | **1 commit**, `23a830c`, unamended |
| `scripts/phase19_erasure.py` | **15 commits**, sha256 `c407246de3c470094ab0bdd868961b7b1c22529c5e00522fec67c3852cb6e303` — byte-identical |
| full suite | **845 passed, 1 skipped** in 188.81s |
| lint | `ruff check` all checks passed; `ruff format --check` 170 files already formatted |

## Self-Check: PASSED

- `results/phase19_erasure_report.md` — FOUND, 549 lines, sha256 `0f30b573…`
- `.planning/phases/19-selective-memory-erasure/19-16-SUMMARY.md` — FOUND
- commit `cd54535` (Task 1) — FOUND
- commit `7ddead8` (Task 2) — FOUND
- commit `cf8a09a` (Task 3, the ship decision) — FOUND
