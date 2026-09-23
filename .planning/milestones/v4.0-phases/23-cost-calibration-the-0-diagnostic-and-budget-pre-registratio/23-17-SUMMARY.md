---
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
plan: 17
subsystem: comparator
tags: [comparator, dp-sgd, protocol-match, one-attempt, grad-clip, d-04, incomplete-run, mps]
status: INCOMPLETE — production run harness-killed at 3 of 5 seeds; NO record written
requires:
  - scripts/phase23_matched_prereg.py (CONSUMED as a pin; asserted byte-identical to c100388)
  - scripts/phase23_prereg.py (asserted byte-identical to c7de5d4; noise_floor CALLED, never edited)
  - scripts/phase23_run.py::train_matched_control (23-16's training leg — RUN here for the first time)
  - data/persona_dp_n8_train{,_mask,_fact}.bin (INPUTS — this arm builds no bins)
  - results/phase23_sigma_zero.json (the arm the comparator controls for; BYTE-UNCHANGED)
provides:
  - phase23_run.matched() — the `matched` sub-mode, its record writer and both one-attempt refusals
  - tests/test_phase23_matched.py — nine additional record guards (18 total in the file)
  - data/phase23_run_state.json::matched — THREE scored seeds, IN HISTORY as of d99d2aa
  - results/phase23_matched_control_seed{1337,2024,1338,2025}/run.csv (committed; 2025 partial)
NOT_provides:
  - results/phase23_matched_control.json — NEVER WRITTEN. The floor was NEVER re-reduced.
affects:
  - 23-18 (the floor re-pin — CANNOT PROCEED: there is no matched floor to pin)
  - 23-19 (the verdict — CANNOT PROCEED: its comparator record does not exist)
tech-stack:
  added: []
  patterns:
    - "a one-attempt refusal that cannot distinguish a killed run from a deleted-and-re-run one,
       and is obeyed anyway rather than narrowed with readings on screen"
    - "a partial attempt committed to make it auditable, at the cost of tripping the rule that
       governs it — because the blindness it protected is genuinely spent"
decisions:
  - "DID NOT RESUME. The plan's Task 2 claims a killed run is resumable per seed; the plan's Task 1
     mandates verbatim a `_prove` that refuses exactly the state a killed run leaves once any seed
     has scored. The two clauses contradict. The refusal is a committed mechanism with no force
     flag and the resumability claim is prose, so the mechanism won."
  - "DID NOT narrow the refusal to admit the 3-of-5 case, though the refinement is arguably
     correct: a completed-and-deleted attempt leaves FIVE scored seeds (the record is only written
     after all five score), so 3-scored-2-never-trained is a distinguishable fingerprint. Making
     that distinction NOW, with three readings visible, is precisely the freedom pre-registration
     spends. It belongs in a reviewed plan."
  - "COMMITTED the four seed directories despite this permanently tripping `prove_first_attempt`
     across commits. The blindness is already spent by the readings existing; committing makes that
     true in git rather than only in this document. Leaving them untracked ALSO reddened a live
     repository-wide census (`test_production_resume_epsilon_bit_identical`)."
metrics:
  duration: ~2h05m
  completed: 2026-08-27
  tasks: 2 (Task 1 complete; Task 2 INCOMPLETE)
  files: 6
  commits: 2
---

# Phase 23 Plan 17: The Protocol-Matched Comparator's Production Run — Summary

**THE RUN DID NOT COMPLETE, AND NOTHING WAS RETRIED TO MAKE IT LOOK LIKE IT DID.** The background
process was terminated externally at ~60 minutes elapsed, during seed 2025's training leg at step
~50 of 200. Three of five seeds are trained and scored. `results/phase23_matched_control.json` was
**never written**, the floor was **never re-reduced**, and **no verdict was rendered**.

**Commits:** `cec1bd8` (Task 1 — the sub-mode, its writer and nine guards) · `d99d2aa` (the partial
run's evidence: the state file's `matched` section plus four seed directories)

## The finding, stated before the incompleteness

At seed 1337 the protocol-matched **non-DP** comparator reproduces the σ=0 DP arm **bit-for-bit on
every scored tier and every family**:

| Tier | σ=0 arm | matched comparator | identical |
|---|---|---|---|
| `primary` (taught ON) | 790/1008 = `0.7837301587301587` | 790/1008 = `0.7837301587301587` | **yes** |
| `heldout_on` | 346/648 = `0.5339506172839507` | 346/648 = `0.5339506172839507` | **yes** |
| `taught_off` | 0/1008 = `0.0` | 0/1008 = `0.0` | yes |
| `heldout_off` | 0/648 = `0.0` | 0/648 = `0.0` | yes |
| per-family, taught | F1 `0.8444…` F2 `0.8222…` F6 `0.6597…` | same three floats | **yes** |
| per-family, held-out | F3 `0.6018…` F7 `0.5138…` F8 `0.4861…` | same three floats | **yes** |
| `per_family_gain` | — | — | **yes** |
| `heldout_family_std` | — | — | **yes** |

Not close. Identical, under exact `==`, verified field by field against the committed
`results/phase23_sigma_zero.json`.

**This is REPORTED, not adjudicated.** `phase23_prereg.sigma_zero_verdict` is 23-19's to call,
against a floor 23-18 re-pins, and neither can run without the record this plan failed to produce.
The deviation between the σ=0 reading and the matched seed-1337 reading is `0.0` exactly. What that
means for D-04 is the rule's to decide and nobody else's.

## The three readings, exactly as they lie

| Seed | `primary` k/n | rate |
|---|---|---|
| 1337 | 790/1008 | `0.7837301587301587` |
| 2024 | 774/1008 | `0.7678571428571429` |
| 1338 | 778/1008 | `0.7718253968253969` |
| 2025 | — | **never trained past step ~50** |
| 1339 | — | **never started** |

**THE FLOOR WAS NOT REDUCED AND IS NOT REDUCED HERE.** `phase23_prereg.noise_floor` is a function
of the **five** readings the inherited seed set declares. Applying it to three would publish a floor
whose denominator disagrees with its own record — the exact defect `floor()`'s own guard refuses.
The three counts above are stated as counts; no spread over them is computed, named or implied.

For the record's sake, the number this run was going to be compared against: the OLD control floor
is `0.05357142857142849`, which as counts is `575/1008 − 521/1008` (**not** `float(3/56)` =
`0.05357142857142857` — the two differ in the last ULP, which is why it is written as counts).

**The held-out tell — DISCLOSURE, not a verdict.** The held-out (never-taught) reading moved in the
**same direction** as the taught one:

| | taught ON | held-out ON |
|---|---|---|
| old control (5 seeds) | `0.5169`–`0.5704` | `0.3441`–`0.3781` |
| matched comparator (3 seeds) | `0.7679`–`0.7837` | `0.4938`–`0.5340` |
| σ=0 arm (seed 1337) | `0.7837` | `0.5340` |

Both tiers rose together under the matched protocol. That is the debug record's tell, recorded here
because it is what the record was required to disclose; it is not interpreted.

## grad_clip: proven non-binding on every seed BEFORE that seed was scored

| Seed | calls | `MAX_STEPS` | bound | pre-clip norm range |
|---|---|---|---|---|
| 1337 | 200 | 200 | **0** | `[0.335902, 2.27707]` |
| 2024 | 200 | 200 | **0** | `[0.348462, 2.29014]` |
| 1338 | 200 | 200 | **0** | `[0.342368, 2.20207]` |

The call count matters as much as the bind count: `bound_count == 0` is also what a branch that was
**never taken** reports, so `calls == MAX_STEPS` is what proves the equalisation actually ran. Both
were asserted inside `train_matched_control` before any reading existed, and re-asserted in
`matched()` from the recorded block before each seed was scored.

**Against the DP arm's measured `1.538`–`2.278`:** the comparator's norms **bracket and slightly
exceed** it — top end `2.29014` (seed 2024) is `0.012` above the DP arm's recorded maximum, and the
bottom end `0.3359` sits well below `1.538`. Stated rather than smoothed. C = `1e6` clears both by
more than five orders of magnitude, so nothing here approaches binding.

## Wall clock against the budget — the budget was sound; the kill was not a budget overrun

| Seed | train s | ≤ 205.44 | score s | ≤ 1026.87 | total | ≤ 1232.31 |
|---|---|---|---|---|---|---|
| 1337 | 154.21 | ✓ | 972.79 | ✓ | 1127.00 | ✓ |
| 2024 | 165.79 | ✓ | 990.29 | ✓ | 1156.08 | ✓ |
| 1338 | 163.20 | ✓ | **1109.24** | **✗ +82.37 s (+8.0%)** | **1272.44** | **✗ +40.13 s (+3.3%)** |

**Named, not absorbed:** seed 1338's scoring leg overran the committed bound by 82.37 s. The bound
was the maximum of the five OLD control seeds' scoring times; this leg exceeded it. Training legs
came in **well under** the ≤205.44 s bound on all three (154–166 s vs the σ=0 arm's 205.44 s),
consistent with the comparator dropping `absorb_record`'s per-record clip/sum/drain and running
neither end-of-run `masked_perplexity` sweep.

**23-16's declared timing cost was carried, not rediscovered:** `float(norm)` in `captured_grad_clip`
forces a per-optimizer-step host sync the σ=0 arm did not have. It is in the 154–166 s figures above
and moves no float in the gradient path.

Three completed seeds cost **3555.52 s = 59.3 min**, mean **1185.17 s/seed**. Projected over five:
**5925.9 s ≈ 98.8 min — inside the plan's 103-minute budget.** The run was killed at ~60 min by the
execution harness, not by exceeding its own estimate.

**Elapsed run window:** started `2026-08-27T16:14:16Z`, last write `2026-08-27T17:14:19Z` — 3603 s.
**Kill → commit `d99d2aa`: ≈ 19 minutes**, same session, nothing deleted in between.

**The kill was external, not a refusal and not an exception.** The run log contains **zero**
occurrences of `Traceback`, `SystemExit` or `Error`; it simply stops mid-progress-line. Seed 2025
left a 5-row `run.csv` (steps 10–50) and a `latest.pt`, and **no adapter**.

## The six declared-absent fields

`ppl_adapter_on`, `ppl_adapter_off`, `ppl_scored_targets`, `teaching_tokens`, `replay_tokens` and
`replay_ratio` are explicit `None` on all three scored seeds, with `ppl_omitted_reason` beside them.
Reason, in one line: this comparator calls `tp.train` directly, so `train_arm`'s two end-of-run
`masked_perplexity` sweeps (`teach_persona.py:1705,1709`) never run. Declared blind in
`phase23_matched_prereg.MATCHED_DIFFERENCES`; not a truncated run.

## THE BLOCKER — three refusals now stand, and I weakened none of them

### 1. The plan contradicts itself, and the mechanism won

- **Task 2 states:** *"`data/phase23_run_state.json` makes a killed run resumable per seed."*
- **Task 1 mandates verbatim** a `_prove` that refuses when the state file records SCORED matched
  seeds while the record is absent — **which is exactly the state a killed run leaves** once any
  seed has scored.

Both cannot hold. Observed, not assumed — re-running the sub-mode after the kill:

```
[phase23_run] git ls-files results/phase23_matched_*: EMPTY — first attempt
[phase23_run] …/data/phase23_run_state.json records SCORED matched seeds ['1337', '1338', '2024']
while results/phase23_matched_control.json is absent. That is exactly the state a
deleted-and-re-run first attempt leaves behind, and there is no force flag.
EXIT=1
```

It refuses **before** `prove_matched_protocol()`, before the record path check, before any GPU
second — so observing it cost nothing and wrote nothing. The refusal is a committed mechanism with
no force flag; the resumability claim is prose. **The mechanism won.**

### 2. Seed 2025's partial artifacts are independently refusing

`train_matched_control` opens with `tp.refuse_if_exists([csv, checkpoint, adapter])`.
`results/phase23_matched_control_seed2025/run.csv` and
`checkpoints/phase23_matched_control_seed2025_latest.pt` both exist. Correct behaviour: a partial
artifact is evidence of where the kill landed, not something to silently overwrite.

### 3. `prove_first_attempt` now binds across commits

As of `d99d2aa`, `git ls-files 'results/phase23_matched_*'` returns four paths. **That is correct,
not collateral.** Three readings are on screen; the blindness the protocol was pre-registered under
is genuinely spent. Any future run of this comparator *would* be a second attempt with the first
one's readings visible — which is the freedom the rule exists to protect. Committing made that fact
true in git rather than only in this paragraph.

### What a future plan must decide — and why I did not decide it

The refusal cannot distinguish a **harness-killed** run from a **deleted-and-re-run** one. It
arguably could: a completed-and-deleted attempt leaves **five** scored seeds, because the record is
only written after all five score, so *3 scored + 2 never trained* is a fingerprint no completed
prior attempt can produce. That refinement may well be right.

**Making it now, with `0.78373`, `0.76786` and `0.77183` on screen, is precisely the freedom
pre-registration spends.** Narrowing a refusal after seeing its readings is indistinguishable from
narrowing it *because of* them, however sound the argument. It belongs in a reviewed plan written by
someone who can see this situation whole — not in an executor's mid-run edit. The plan's own
discipline is explicit: *"Adding a force flag, an override, or a warning branch to any refusal"* is
absolutely forbidden, *"regardless of how the run turns out."*

## What was committed, and why the partial evidence was committed at all

`d99d2aa` carries `data/phase23_run_state.json` **and** all four seed directories in one commit.
Verified in history, not in the working tree:

```
$ git show HEAD:data/phase23_run_state.json | keys
top keys ['control', 'cost', 'matched', 'never_taught', 'sigma_zero']
matched seeds in history: ['1337', '1338', '2024']
scored: ['1337', '1338', '2024']
```

The committed baseline at `cfa2c87` carried **no** `matched` section. It does now. **A later
deletion of it is a visible diff against `d99d2aa`** — the residual is auditable from this commit
onward, exactly as the four-clause scope describes, and not one second earlier: tracking is not
retroactive, and between the kill and this commit a `git checkout --` would have left no history at
all. That 19-minute window was the whole exposure, and it is closed.

## Deviations from Plan

### 1. [Rule 4 → STOP] The five-seed run did not complete and was NOT resumed

Documented in full above. No seed re-run, no seed re-seeded, no band widened, no constant tuned, no
artifact deleted, no refusal weakened. `results/phase23_matched_control.json` does not exist.

### 2. [Rule 3 - Blocking] The untracked run output reddened a live repository-wide census

- **Found during:** Task 2, the post-run full suite.
- **Issue:** `tests/test_phase23_resume.py::test_production_resume_epsilon_bit_identical` ends with
  `assert git status --porcelain results/ == ""`, to prove **its own** probe left nothing behind.
  The predicate is repository-wide, so this plan's four legitimate untracked result directories
  tripped it: `1 failed, 1517 passed, 1 skipped`.
- **Fix:** committed the four directories (`d99d2aa`). The guard wants `results/` *clean*, and clean
  means *committed*, not *absent*. Suite returned to `1518 passed, 1 skipped`.
- **This is the same defect class this repository keeps naming** — a guard measuring a global
  property to prove a local one — found in a new place. **Not** fixed by excusing this plan's paths
  in that test: the paths belong in history, and a permanent exclusion in a shared census would be
  the wrong repair. Logged here rather than patched.
- **It also forced the `prove_first_attempt` consequence in §3 above**, so the two decisions are one
  decision, and both point the same way.

### 3. [Deliberate] The four seed directories were committed knowing it trips the one-attempt rule

Reasoned in "What a future plan must decide" and §3 of the blocker. The alternative — leaving three
seeds' readings untracked — buys a theoretically resumable run at the price of the evidence being
erasable without trace, which is the exact condition the plan's auditability argument exists to
escape.

### 4. `.gitignore` carries an unrelated unstaged modification

` M .gitignore` (adding `.obsidian/`) was present **before** this plan started and is out of its
scope. Not staged, not committed, not reverted.

**No authentication gates occurred. No package was installed.**

## Verification

| Check | Command | Result |
|---|---|---|
| Sub-mode registered | `'matched' in _TABLE and in USAGE` | ✓, and `--help` lists it |
| Both one-attempt refusals present | `grep prove_first_attempt / prior_scored_seeds_at_start` | `:2145` and `:2169` |
| Visibility refusal precedes the write | read the function body | `prove_control_record_declares_visibility` **:2393**, `path.write_text` **:2395** |
| Reduction CALLED, not inlined | `test_the_matched_writer_does_not_inline_the_reduction` (AST) | PASS — no `max`/`min` Call, `noise_floor` called |
| No skip of any form in the test file | the plan's AST gate | `no skips 2204 nodes scanned` |
| New tests | `pytest tests/test_phase23_matched.py -q` | **18 passed** (9 original + 9 new) |
| Nine record guards | with the record absent | all take the vacuity branch, which **asserts** |
| **Full suite** | `.venv/bin/python -m pytest -q` | **`1518 passed, 1 skipped`** (83 warnings, 360.68 s) |
| Lint | `ruff check . && ruff format --check .` | clean, 217 files formatted |
| Closed pin | `git diff --exit-code c7de5d4 -- scripts/phase23_prereg.py` | **exit 0** |
| Blind pin | `git diff --exit-code c100388 -- scripts/phase23_matched_prereg.py` | **exit 0** |
| Frozen files | `git diff --exit-code -- mitigation_{gate,accountant,budget}, teach_persona, loop, phase23_sigma_zero.json, phase23_control_floor.json` | **exit 0** |
| No noised point | `git ls-files 'results/phase23_noised_*'` | **0**; no such directory on disk |
| σ=0 record untouched | included in the frozen check above | **exit 0** |
| The record was never written | `ls results/phase23_matched_control.json` | **No such file** |
| No accidental deletions | `git diff --diff-filter=D --name-only cec1bd8~1 HEAD` | **0** |
| `matched` section in history | `git show HEAD:data/phase23_run_state.json` | 3 seeds, all scored |

**Suite arithmetic:** `1518 = 1509` (the 23-16 baseline) `+ 9` (this plan's new guards). No
pre-existing test changed status.

## Requirements

**NO requirement is ticked, and none is claimed.** `DPSGD-06` remains open. CAL-01, CAL-02, CAL-05
and CTRL-03 remain 23-11…23-14's **BLOCKED** scope. This plan was never going to close any of them —
its own success criteria end with *"NO requirement is ticked"* — and it did not deliver even the
comparator record they would eventually depend on.

## D-04 HALT compliance

**The halt stands and was not touched.** Zero noised sweep points ran; `git ls-files
'results/phase23_noised_*'` returns **0** at the end exactly as at the start. `23-11`…`23-14` were
not touched. No σ=0 arm was re-run: `results/phase23_sigma_zero.json` is byte-unchanged. **No
verdict was rendered** — `sigma_zero_verdict` was not called, and the σ=0 comparison in this document
is a report of two numbers, not a decision about them.

## Known Stubs

None introduced. The `matched` sub-mode is complete and was executed; what is missing is data, not
code. The nine new record guards are live and currently exercise their **vacuity branch** — which
asserts that the sub-mode exists rather than passing quietly — and will assert against the real
record the moment one exists.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema at a trust boundary. No
package was installed (T-23-SC). One threat register entry needs a note for the next planner:
**T-23-68b's mitigation is stronger than intended** — `prior_scored_seeds_at_start` refuses a
harness-killed run as well as a deleted-and-re-run one, and this plan is the measured proof of that.

## Notes for whoever plans the completion

1. **Do not delete anything to restart.** `data/phase23_run_state.json`'s `matched` section, the four
   seed directories and the three adapters are committed evidence of a real partial attempt.
2. **Three refusals stand**, all of them correct as written: the scored-seed refusal, seed 2025's
   `refuse_if_exists`, and `prove_first_attempt` across commits.
3. **The blindness is spent.** Three readings and the exact σ=0 reproduction are on screen. Any
   completion is a second attempt in substance, whatever it is called, and the honest route is
   clause (4) of `prove_first_attempt`: **arrive with a NEW pre-registration**, visible rather than
   refused. `scripts/phase23_matched_prereg.py` is EDIT-ONCE and is now spent for this glob.
4. **The budget was right** (98.8 min projected vs 103 min budgeted). Whatever runs next needs an
   execution venue that does not terminate a 100-minute process at 60 minutes — that, not the
   protocol, is what failed.
5. **23-18 and 23-19 cannot proceed.** Neither the floor re-pin nor the verdict has an input.

## Self-Check: PASSED

- `scripts/phase23_run.py` — FOUND (`matched` registered, both refusals in place)
- `tests/test_phase23_matched.py` — FOUND, 18 tests passing
- `data/phase23_run_state.json` — FOUND, `matched` section with 3 scored seeds IN HISTORY
- `results/phase23_matched_control_seed{1337,2024,1338,2025}/run.csv` — all four FOUND and committed
- `results/phase23_matched_control.json` — **confirmed ABSENT**, as this document states throughout
- Commit `cec1bd8` — FOUND in `git log`
- Commit `d99d2aa` — FOUND in `git log`
- Both frozen pre-registrations — byte-unchanged
- `git ls-files 'results/phase23_noised_*'` — **0**
