---
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
plan: 19
subsystem: privacy/verdict
tags: [d-04, verdict, protocol-matched-comparator, read-the-denominator, blind-rule, gap-closure, interrupted-execution]
status: COMPLETE
requires:
  - "results/phase23_matched_control.json (23-17 begun, 23-20 completed) — the five protocol-matched readings and their per-seed k/n"
  - "results/phase23_sigma_zero.json (23-10) — the σ=0 arm's reading, READ BACK and never re-run"
  - "scripts/phase23_prereg.py::sigma_zero_verdict / noise_floor (23-03, c7de5d4, EDIT-ONCE, byte-unchanged) — the rule that renders the verdict"
  - "scripts/phase23_matched_prereg.py::VERDICT_REQUIRED_KEYS / prove_verdict_record_declares_visibility / MATCHED_DIFFERENCES (23-15, c100388, one commit, frozen)"
  - "scripts/mitigation_budget.py::MATCHED_CONTROL_NOISE_FLOOR + _PROVENANCE (23-18)"
provides:
  - "results/phase23_matched_verdict.json — verdict 'proceed', deviation 0.0, floor 0.0267857142857143, all 14 VERDICT_REQUIRED_KEYS, both arms' four scored tiers with their own denominators"
  - "scripts/phase23_run.py::matched_verdict — the sub-mode that CALLS the rule and READS every denominator; renders no comparison of its own"
  - "tests/test_phase23_matched.py — 6 new guards, each denominator checked against its own source record"
NOT_provides:
  - "any unblocking of 23-11 / 23-12 / 23-13 / 23-14 — they remain BLOCKED; the record says so in its own `governs` field"
  - "any noised point — `git ls-files 'results/phase23_noised_*'` is 0, held there by a committed guard regardless of the verdict"
  - "any requirement closure — CAL-01, CAL-02, CAL-05, CTRL-03 stay OPEN; DPSGD-06 (23-10) and CAL-03 (23-04) were already closed and were NOT re-ticked"
  - "any completion of 23-17 — it remains INCOMPLETE and UNTICKED"
affects:
  - "23-11 / 23-12 / 23-13 / 23-14 — now unblockABLE, still BLOCKED, pending a human act"
  - ".planning/debug/sigma-zero-beats-control.md — status root-caused -> resolved"
tech-stack:
  added: []
  patterns:
    - "THE READ-THE-DENOMINATOR RULE: every k and n in a committed evidence artifact is a subscript read of its source record's own tier block, never a literal — AST-enforced (no 1008/648 constant in the function body) and per-tier tested against the source"
    - "the record is written on BOTH branches before the SystemExit, so a HALT is recorded evidence rather than a lost exit code"
    - "the driver renders no comparison: one call to the blind rule, zero `deviation <=/</>=/>` comparisons anywhere in scripts/phase23_run.py"
decisions:
  - "23-17 was deliberately left UNTICKED against the plan's own stale acceptance criterion. Task 3 demanded `grep -c '^- \\[ \\] 23-1[5-9]-PLAN.md' == 0`, which would have ticked 23-17 — but 23-17's run was harness-killed at 3/5 and wrote no record, and 23-20 completed it under a SEPARATE continuation pre-registration. The plan's criterion was written before that was known. Truth beat the criterion."
  - "NO gsd-sdk state.*/roadmap.* mutation handler was used. All three planning files were hand-edited with Edit, per the plan's own Task-3 prohibition; `roadmap.update-plan-progress` keys on SUMMARY EXISTENCE and falsely ticked 23-17 during 23-18."
  - "The verdict was NOT re-rendered during close-out. `sigma_zero_verdict` was called exactly once, at 0a275c9, while its output was still blind; re-invoking it to regenerate the record would have destroyed the property this phase exists to protect. The record was READ, and the committed guards that read it were run."
requirements: []
metrics:
  duration: ~55 min (interrupted execution + close-out)
  completed: 2026-08-27
  tasks: 4
  files: 6
  commits: 5
---

# Phase 23 Plan 19: The D-04 Re-Test — the Blind Rule Returns `proceed` — Summary

`phase23_prereg.sigma_zero_verdict`, **byte-identical to its blind birth commit `c7de5d4`**, was
called **exactly once** against the protocol-matched comparator and returned **`"proceed"`** with a
deviation of **exactly `0.0`** against the floor `0.0267857142857143`. The D-04 halt is **resolved
by comparator correction** — not by a DP-mechanism change, not by widening a band, and not by
re-running anything.

**Commits:** `c86a224` (the sub-mode) · `0a275c9` (the run + record) · `beb2e53` (six guards) ·
`d5c80a0` (debug record + STATE + ROADMAP) · plus this document's metadata commit.

## The verdict, with every denominator the record carries

|  | σ=0 arm | protocol-matched comparator |
|---|---|---|
| taught ON (primary) | **790/1008 = 0.7837301587301587** | **790/1008 = 0.7837301587301587** |
| held-out ON | 346/648 = 0.5339506172839507 | 346/648 = 0.5339506172839507 |
| taught OFF | 0/1008 | 0/1008 |
| held-out OFF | 0/648 | 0/648 |

Not "inside the floor" — **IDENTICAL**, on all four scored tiers, at the same seed 1337. The
taught-OFF denominator is **1008**, the TAUGHT question set's, **not** the held-out set's 648: that
is the exact figure this plan's first draft got wrong, and it is now read from each record's own
block and checked by a named test.

| | central reading | floor | deviation | ratio | direction |
|---|---|---|---|---|---|
| **NEW (protocol-matched)** | `0.7837301587301587` @ seed 1337 | `0.0267857142857143` | **`0.0`** | **`0.0000`** | — |
| SUPERSEDED (old control) | `0.5615079365079365` @ seed 1337 | `0.05357142857142849` | `0.2222222222222222` | `4.1481x` | **BEATS** |

**What moved: the comparator, not the arithmetic.** The σ=0 arm was not re-run — same bins, same 200
composed steps, same `clip_bind_count == 0`, same `790/1008`. The old control differed from it along
three *measured* mechanisms (lot volume 8.125x/step, teaching loss weight 2.30x, and a `grad_clip`
binding on 19 of its first 25 steps); equalising all three collapses the deviation to zero. The
first verdict **was not wrong** — it correctly measured this arm against a different training
protocol — and `results/phase23_sigma_zero.json` and `results/phase23_control_floor.json` are left
byte-unchanged beside the new record so a reader sees both.

## What `proceed` does NOT do

- **23-11 / 23-12 / 23-13 / 23-14 REMAIN BLOCKED.** They are now *unblockABLE* — the precondition
  they waited on exists — and unblocking them is a separate, later act by a human who has read
  `results/phase23_matched_verdict.json`. The record says so in its own `governs` field:
  *"THIS RECORD DOES NOT UNBLOCK ANYTHING."* `test_no_noised_point_exists` holds
  `git ls-files 'results/phase23_noised_*'` at **0** unconditionally on the verdict. Verified: 0.
- **23-17 REMAINS INCOMPLETE and UNTICKED** (`- [ ]` at `ROADMAP.md:664`). Its run was harness-killed
  at 3/5 and wrote no record; 23-20 completed the run under a separate continuation
  pre-registration. `roadmap.update-plan-progress` falsely ticked it during 23-18 and was reverted
  by hand; it was **not** re-ticked here.
- **NO requirement was ticked.** Stated plainly, all six the brief named:

  | Req | State | Why |
  |---|---|---|
  | CAL-01 | **OPEN** `- [ ]` | belongs to BLOCKED 23-11 |
  | CAL-02 | **OPEN** `- [ ]` | belongs to BLOCKED 23-13 |
  | CAL-03 | already `[x]` | closed by **23-04**, untouched here |
  | CAL-05 | **OPEN** `- [ ]` | belongs to BLOCKED 23-11 |
  | DPSGD-06 | already `[x]` | closed by **23-10** (records that the diagnostic FIRED); this plan's frontmatter lists it, but the plan's own success criteria forbid re-closing it |
  | CTRL-03 | **OPEN** `- [ ]` | belongs to BLOCKED 23-14 |

  `.planning/REQUIREMENTS.md` is **byte-unchanged** — `git status --short` on it is empty. Making a
  valid comparator exist is a precondition, not a delivery.

## Verification performed during close-out

Every claim inherited from the interrupted execution was re-measured, not trusted:

| Check | Result |
|---|---|
| `git diff c7de5d4 -- scripts/phase23_prereg.py` | **empty** — the rule was never edited |
| `git diff c100388 -- scripts/phase23_matched_prereg.py` | **empty**; `git log` = **1 commit** |
| `scripts/phase23_resume_prereg.py` commit count | **1** |
| `git ls-files 'results/phase23_noised_*'` | **0** |
| `git diff --exit-code` on the three σ=0/floor/matched records | **clean** |
| `scripts/teach_persona.py`, `src/personacore/training/loop.py` | **byte-unchanged**; `grep -c DP_ARMS` = **9** |
| `loop.py:512` / `loop.py:683` | exact: `_fact = {"fact_bin": fact_bin, "n_facts": n_facts}` / `if replay_windows is not None:` |
| per-seed table in the debug record vs `results/phase23_matched_control.json` | all 5 seeds, both tiers, **exact** |
| AST: `1008`/`648` literals in `matched_verdict` body | **NONE** (T-23-77b) |
| AST: `sigma_zero_verdict` calls in `matched_verdict` | **1** |
| `grep -c "deviation <= \|deviation > \|deviation >= \|deviation < " scripts/phase23_run.py` | **0** — no driver-side comparison (T-23-76) |
| debug record deletion count (`--numstat`) | **1**, and it is the frontmatter `status:` line |
| `23-MECHANISM-ASSESSMENT.md` | **untouched** |
| ROADMAP: one line per plan 23-11…23-20 | **1 each**, no duplicates; 15 ticked of 20 |
| STATE `completed_plans: 62` / `total_plans: 67` | matches ROADMAP tick counts **exactly** (62 / 67) |
| **Full suite** | **`1549 passed, 1 skipped`**, 83 warnings, 373.72s |
| `ruff check .` / `ruff format --check .` | **All checks passed** / **219 files already formatted** |

## The debug record: a dated continuation, one deletion, named

`.planning/debug/sigma-zero-beats-control.md` gained **146 insertions** and **1 deletion**. The
single deletion is the frontmatter line `status: root-caused` → `status: resolved`, which the plan
**mandates** on a `proceed` verdict (23-19-PLAN.md:452) and which T-23-79 bounds to "the one or two
named frontmatter lines". **Within bounds, not a violation.** `updated:` needed no change — it
already read `2026-08-27`. Every pre-existing section of the body is byte-unchanged; the
`## Current Focus` correction was **inserted as a dated line** beside the original, not written over
it, and the original still reads *"Await user decision."* as it was recorded.

## Deviations from Plan

### Found in the interrupted work (all correct as-executed; recorded, not changed)

**1. [Rule 1 — stale plan criterion] 23-17 was correctly left UNTICKED.**
- **Found during:** close-out review of Task 3's ROADMAP edit.
- **Issue:** Task 3's acceptance criteria demand `grep -c "^- \[ \] 23-1[5-9]-PLAN.md"` return **0**
  — which would require ticking 23-17. 23-17 is genuinely incomplete: its run was harness-killed at
  3/5, it wrote no record, and 23-20 completed the run under a separate pre-registration. The
  criterion was authored before that was known.
- **Resolution:** criterion knowingly **not met**. `ROADMAP.md:664` stays `- [ ]`. The truthful
  state beats the stale checkbox, and this is exactly the false tick `roadmap.update-plan-progress`
  produced during 23-18.

**2. [Rule 1 — stale plan criterion] Suite count is `1549`, not the plan's `1529`.**
- **Issue:** the plan predicted `1529 passed` from "23-18's 1523 plus the 6 new guards". 23-18's
  actual post-count was **1543**, not 1523.
- **Cause:** arithmetic on a stale baseline in the plan's prose. `1543 + 6 = 1549`, measured.
  The plan itself sanctions this: *"a different count is recorded with its cause in the SUMMARY."*

**3. [observation] The plan's own verification command is wrong.**
- Task 3 says to verify the commit with `git diff HEAD~1 --stat`. That compares `HEAD~1` against the
  **working tree**, not against `HEAD` — it reported a 4th file (`.gitignore`, a pre-existing
  unrelated modification) that is **not** in the commit. `git show --stat HEAD` confirms the commit
  holds exactly the three intended planning files. Noted so the next plan does not inherit the bug.

### Made during close-out

**4. [Rule 1 — truthfulness] STATE.md: "23-17 remains INCOMPLETE ON PURPOSE" re-attached.**
- **Issue:** "ON PURPOSE" attached to *INCOMPLETE* claims 23-17 was deliberately left unfinished. It
  was **harness-killed**. What is deliberate is that its box stays **UNTICKED**. The disambiguating
  clause followed immediately, so this was imprecise rather than false — but a reader skimming bold
  text takes the wrong claim.
- **Fix:** the sentence now says 23-17 "was not left unfinished by choice; what IS deliberate is
  that its box stays UNTICKED".
- **Commit:** `d5c80a0`.

### Execution interruption

Tasks 1–3 were executed and committed by a prior executor (`c86a224`, `0a275c9`, `beb2e53`). Task
3's file edits existed **uncommitted** in the working tree when execution was interrupted. This
close-out verified them, made deviation 4, and committed them as `d5c80a0`. **The verdict was not
re-rendered** — `sigma_zero_verdict` was called once, blind, at `0a275c9`; the record was read, and
the committed guards that read it were run.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or trust-boundary schema change; the
sub-mode is CPU-only arithmetic over two committed JSON records, and `T-23-SC` holds — no package
was installed, the existing `.venv` only.

## Self-Check: PASSED

- `results/phase23_matched_verdict.json` — FOUND
- `.planning/phases/23-.../23-19-SUMMARY.md` — FOUND
- `scripts/phase23_run.py::matched_verdict` — FOUND (AST)
- `tests/test_phase23_matched.py` 6 new guards — FOUND, all passing
- Commits `c86a224`, `0a275c9`, `beb2e53`, `d5c80a0` — all FOUND in `git log`
</content>
</invoke>
