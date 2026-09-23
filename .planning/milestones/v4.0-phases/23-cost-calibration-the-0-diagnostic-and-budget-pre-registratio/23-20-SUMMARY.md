---
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
plan: 20
subsystem: comparator
tags: [comparator, one-attempt, continuation, pre-registration, detached-run, mps, d-04, gap-closure]
status: COMPLETE
requires:
  - scripts/phase23_matched_prereg.py (CONSUMED as a frozen pin; byte-identical to c100388, still ONE commit)
  - scripts/phase23_prereg.py (byte-identical to c7de5d4; noise_floor CALLED over FIVE readings, never edited)
  - scripts/phase23_run.py::matched (23-17's sub-mode — the call site this plan rewired)
  - data/phase23_run_state.json::matched (23-17's THREE scored seeds, in history at d99d2aa)
  - results/phase23_matched_control_seed{1337,2024,1338}/run.csv (the killed run's committed evidence)
provides:
  - scripts/phase23_resume_prereg.py — prove_killed_run_continuation, seed_status, seed_run_csv, CONTINUATION_SCOPE
  - tests/test_phase23_resume_prereg.py — 19 tests; every refusal watched, the whole-block invariance proof, three AST tripwires
  - results/phase23_matched_control.json — FIVE per-seed readings and the RE-REDUCED floor 0.0267857142857143
  - results/phase23_matched_control_seed{2025,1339}/run.csv — the two owed seeds' training curves
  - results/phase23_resume_run.log — the detached run's stdout, first line the measured pid/pgid/sid
  - data/phase23_run_state.json::matched — FIVE scored seeds, committed SAME SESSION as the record
NOT_provides:
  - results/phase23_matched_verdict.json — NOT written. 23-19 renders the verdict.
  - a re-pinned MATCHED_CONTROL_NOISE_FLOOR — 23-18's.
affects:
  - 23-18 (the floor re-pin — UNBLOCKED: the matched floor now exists)
  - 23-19 (the σ=0 verdict — UNBLOCKED: its comparator record now exists)
tech-stack:
  added: []
  patterns:
    - "a second pre-registration arriving in a NEW file beside a frozen one, because the ancestry
       guard makes editing the frozen one permanently unrecoverable — clause (4)'s REMEDY SHAPE,
       stated explicitly as not its CASE"
    - "a narrowing argued from the record writer's WRITE-ORDERING, with independence from the
       visible readings made STRUCTURAL: no reading in the signature, key-presence-only derivation,
       and a whole-block value substitution proving verdict AND refusal text bit-identical"
    - "a long GPU run detached with os.setsid() + os.execv under nohup, PROBED with os.getsid()
       because setsid(1) does not exist on macOS and BSD ps has no sid keyword"
    - "a recorded rule fingerprint that IS the argument dict, so the published record is literally
       what the predicate saw and re-admits under its own rule on every suite run"
decisions:
  - "NEW FILE, not an edit to the frozen pin. MEASURED: `git merge-base --is-ancestor HEAD d99d2aa`
     exits NON-ZERO, so any second commit touching `scripts/phase23_matched_prereg.py` fails
     `_assert_ordering_holds`' ancestry conjunct against `d99d2aa` PERMANENTLY, and `adds[-1]` takes
     the EARLIEST add so delete-and-re-add cannot launder it."
  - "The branch predicate is `not scored` ALONE, never `not tracked and not scored`. The filtered
     form makes `prove_first_attempt`'s refusal UNREACHABLE while the call site still reads
     correctly. A test watches the frozen refusal fire on a non-empty glob with an empty state."
  - "Seed 2025 was RETRAINED FROM SCRATCH, not mid-train resumed. `prove_matched_protocol`
     (`scripts/phase23_run.py:1181-1187`) refuses `resume_from`, and two DP_FN_BRANCH_DISPOSITIONS
     items are dispositioned `unreached` precisely because this scheduling resumes nothing."
  - "The retained (2b) `_prove` is UNFIREABLE on its branch and is recorded as such. Claiming it
     still refuses would be claiming a guard the code does not have."
metrics:
  duration: ~1h05m (18:22 first commit → 19:27 final; the detached run itself 37.8 min)
  completed: 2026-08-27
  tasks: 3 (all complete)
  files: 8
  commits: 5
---

# Phase 23 Plan 20: The Killed Run's Continuation — Summary

**THE RUN COMPLETED. FIVE SEEDS, ONE FLOOR, NOTHING RETRIED AND NOTHING TUNED.**
`results/phase23_matched_control.json` exists. The floor is `0.0267857142857143`, which as counts is
`790/1008 − 763/1008 = 27/1008`. It was obtained by CALLING `phase23_prereg.noise_floor` over FIVE
readings; no spread is typed anywhere in the writer (the committed AST gate re-checked green).

**Commits:** `e70a035` (the continuation pin) · `a629d93` (seed 2025's partial bytes, discarded
visibly) · `d8f4263` (the call site + the record's disclosure) · `04cdb21` (the run) · plus this
document's metadata commit.

## The route taken for the narrowing, and the measured argument for it

The narrowing arrived as a **NEW pre-registration in a NEW file** — `scripts/phase23_resume_prereg.py`
— beside the frozen `scripts/phase23_matched_prereg.py`, which was not edited, not wrapped and not
passed a filtered input.

The reason is measured, not stylistic:

```
$ git merge-base --is-ancestor HEAD d99d2aa; echo $?
1
$ git log --oneline --diff-filter=A -- 'results/phase23_matched_*'
d99d2aa run(23-17): matched comparator, 3 of 5 seeds — HARNESS-KILLED mid-seed-4, NO record written
```

`d99d2aa` is the EARLIEST add of `results/phase23_matched_*` and is already an ancestor of HEAD.
`tests/test_phase20_prereg.py::_assert_ordering_holds` requires every commit touching a
pre-registration to be a **strict ancestor** of that earliest add, and it takes `adds[-1]`, so a
delete-and-re-add cycle launders nothing. A second commit touching the matched pin would have
reddened `tests/test_phase23_matched_prereg.py` **permanently, with no recovery path.**

**Stated at true strength, in the module docstring rather than only here:** this is clause (4)'s
**REMEDY SHAPE**, not its **CASE**. Clause (4) is about a comparator RENAMED OUT of
`MATCHED_ARTIFACT_GLOB` (`results/phase23_rematch_*`); these artifacts keep their names and stay
inside the glob. What is borrowed is the remedy the clause names — *a second rule must arrive with a
NEW pre-registration; that is VISIBLE, NOT REFUSED* — and 23-17-SUMMARY's own "Notes for whoever
plans the completion", item 3, names the same route.

### The discrimination, argued from write-ordering alone

`matched()` writes `results/phase23_matched_control.json` as its **LAST act**, after the
`for seed in seeds:` loop has scored every ladder seed. A COMPLETED attempt therefore necessarily
leaves five scored seeds, and `len(scored) < len(ladder)` is **a state the completion path cannot
produce**. Deleting a completed attempt's record does not un-score its seeds (`_state_record`
refuses to overwrite a recorded value at a different one), so reaching three would additionally
require deleting seed blocks — a visible diff against `git show HEAD:`, which is exactly what
conjunct 5 compares.

The argument is about the order the writer writes in. It is not about `0.7837301587301587`,
`0.7678571428571429` or `0.7718253968253969`, and it would be the same argument at any three values.

### Why that independence is checkable rather than asserted

| Leg | Mechanism | Where |
|---|---|---|
| (a) no reading can enter the signature | `prove_killed_run_continuation` is keyword-only over `tracked`, `ladder`, `trained_seeds`, `scored_seeds`, `committed_scored_seeds`, `record_exists` — nothing else | `test_the_predicates_signature_admits_no_reading` (AST) |
| (b) derivation is key MEMBERSHIP, never a value | `seed_status` reads `"adapter_sha256" in block` / `"primary" in block` | `seed_status`, and (c) below |
| (c) every value perturbed, verdict AND refusal text unmoved | whole-block substitution, three fillers | `test_the_continuation_predicate_is_invariant_under_arbitrary_readings` |
| tripwire | **no float constant anywhere in the module** — AST, not grep, because the docstring names `0.7837301587301587` and a grep would go false-RED against its own prose | `test_the_module_declares_no_float_constant` |

## The whole-block substitution test's result

Four states: the pinned blob `git show d99d2aa:data/phase23_run_state.json` plus three variants in
which **every seed block is rebuilt as `{k: <arbitrary> for k in block}`** — every value replaced,
key presence alone preserved — with fillers `0`, `10**9` and `None`. So `heldout_on.rate`,
`final_train_loss` and `training_seconds` are perturbed exactly as `primary.rate`/`.k`/`.n` are; a
three-field probe would not have proved this.

Across all four:

- the derived `(trained, scored)` arguments are **identical** — `([1337, 1338, 2024], [1337, 1338, 2024])`;
- `prove_killed_run_continuation(...)` returns **`True`** in all four;
- the refusing case, **derived FROM the substituted copy itself** (each state extended with a block
  for every ladder seed it is missing, the missing list COMPUTED and asserted non-empty first, never
  hardcoded as "the two missing seeds"), produces a **bit-identical** `SystemExit` string in all
  four — `len(set(refusals)) == 1`.

**The fixture is PINNED and reads no live state.** `git show d99d2aa:data/phase23_run_state.json`
carries exactly `scored = ['1337','1338','2024']` and `git merge-base --is-ancestor d99d2aa HEAD`
exits 0. Verified by AST exact-constant equality (never grep, which would go false-RED against the
file's own docstrings):

```
'd99d2aa:data/phase23_run_state.json' in constants -> True
'data/phase23_run_state.json'          in constants -> False
'results/phase23_matched_*'            in constants -> False
```

That third value is not decoration: Task 3 committed the record, so a live
`git ls-files 'results/phase23_matched_*'` now returns **six** entries including
`results/phase23_matched_control.json` — and conjunct 6 refuses exactly that path. A test sourcing
`tracked` live would have been green through Tasks 1 and 2 and red only here, after the GPU run.
Every `tracked` list is built from conjunct 7's own formula via `rp.seed_run_csv`.

## The refusal messages, watched firing

`.venv/bin/python scripts/phase23_resume_prereg.py` exits 0 and prints three admissions and nine
refusals against CONSTRUCTED inputs (the self-check opens no file, so it is time-invariant and still
passes now that the live state holds five scored seeds). Verbatim heads:

**Conjunct 2b — a COMPLETED attempt, the load-bearing one:**
```
[phase23_resume_prereg] ALL 5 LADDER SEEDS HAVE SCORED: [11, 22, 33, 44, 55]. That is a COMPLETED
attempt, not a killed one.

THE DISCRIMINATION IS THE RECORD'S WRITE-ORDERING AND NOTHING ELSE. `phase23_run.matched` writes
results/phase23_matched_control.json as its LAST act, AFTER the `for seed in seeds:` loop has scored
EVERY seed in the ladder. A completed attempt therefore NECESSARILY leaves every ladder seed scored,
and a scored set SHORTER than the ladder is a state the completion path CANNOT PRODUCE.

Deleting a completed attempt's record does NOT un-score its seeds — `phase23_run._state_record`
refuses to overwrite a recorded value at a different one — so to reach a short scored set the seed
blocks would have to be deleted too, which is a VISIBLE DIFF against `git show HEAD:` and is what
conjunct 5 compares. …
```

**Conjunct 2a — routed to the frozen rule, which is why the split exists:**
```
[phase23_resume_prereg] NO SEED HAS SCORED, so this is not a continuation of anything — it is a
FIRST ATTEMPT, and `phase23_matched_prereg.prove_first_attempt` is the rule that governs it. …
```

**Conjunct 5 — carries its own remedy, so a reader gets it from the mechanism:**
```
[phase23_resume_prereg] THE WORKING TREE AND GIT HISTORY DISAGREE about which matched seeds have
scored. The working tree says [11, 22, 44]; `git show HEAD:` says [11, 44]. …

THIS IS WHAT A HAND-EDITED STATE FILE LOOKS LIKE — AND IT IS ALSO WHAT A SECOND KILL LOOKS LIKE
BEFORE ITS STATE IS COMMITTED. …

THE REMEDY IS NOT A FLAG AND NOT A SECOND NARROWING. If a seed has just scored and the state file is
not yet committed, COMMIT IT AND THE NEWLY COMPLETED SEED DIRECTORY FIRST, then re-launch:

    git add data/phase23_run_state.json results/<the newly completed seed directory>
    git commit -m 'run: <seed> completed'
```

The other six refusals (existing record, non-prefix scored set, run-ahead trained set, tracked
control record, tracked verdict record, tracked path outside the reached seeds / not a per-seed
curve) all fire and are asserted on their content, not merely on the exception type.

## The detachment probe, verbatim, before any GPU second

```
DETACHED OK — pid 23851 is its own session leader; caffeinate holding
SESSION pid=23851 pgid=23851 sid=23851
```

That first line of `results/phase23_resume_run.log` is the process reporting its **own** pid, and it
is the committed evidence. Three machine facts made this necessary and were each re-measured here:

| Fact | Command | Result |
|---|---|---|
| `setsid(1)` does not exist | `command -v setsid` | exit 1, no output — a `nohup setsid …` line would have exited 127 while still printing a plausible pid |
| BSD `ps` has no `sid` keyword | `ps -o pid,pgid,sid -p $$` | `ps: sid: keyword not found` **with exit 0** — a probe written that way passes vacuously |
| `$!` after `cd … && nohup … &` is the SUBSHELL | (23-20-PLAN's measurement) | the pid was therefore taken from the log's first line, never from `$!` |

Detachment was done with `os.setsid()` **inside** the launched interpreter, which then `os.execv`s
the real script (exec preserves the pid and gives `scripts/phase23_run.py` an absolute `__file__`,
which `runpy.run_path` would not). The probe is `os.getsid(pid)` from a **second** interpreter, and
it asserted `pid == pgid == sid` both from the log line and live. `caffeinate -is -w 23851` held:

```
pid 23874(caffeinate): … PreventUserIdleSystemSleep named: "caffeinate command-line tool"
```

`ps -o stat` reported `SNs` throughout — the trailing `s` is "session leader". **No foreground call
ever held the run.** It was never killed.

## The five readings, exactly as they lie

| Seed | `primary` k/n | rate |
|---|---|---|
| 1337 | 790/1008 | `0.7837301587301587` |
| 2024 | 774/1008 | `0.7678571428571429` |
| 1338 | 778/1008 | `0.7718253968253969` |
| **2025** | **763/1008** | **`0.7569444444444444`** |
| **1339** | **773/1008** | **`0.7668650793650794`** |

**The floor: `0.0267857142857143`**, as counts **`790/1008 − 763/1008 = 27/1008`**. `noise_floor`
was CALLED, never inlined; `test_the_matched_writer_does_not_inline_the_reduction` re-checked green
after the call-site edit. For comparison only, not adjudication: the OLD control floor is
`0.05357142857142849` (`575/1008 − 521/1008`). The matched floor is the tighter of the two.

**No verdict is rendered here.** `phase23_prereg.sigma_zero_verdict` is 23-19's to call, against a
floor 23-18 re-pins from this record. The σ=0 arm's reading is `0.7837301587301587` and the matched
central reading (seed 1337, `readings[0]`) is `0.7837301587301587` — stated as two numbers, not as a
decision about them.

**Held-out, disclosed rather than interpreted:** `heldout_on` across the five seeds is
`0.5340 / 0.4938 / 0.5139 / 0.5386 / 0.5340`. `taught_off` and `heldout_off` are exactly `0.0` on all
five.

## Wall clock against the committed bound — no overrun to name this time

Per-seed bound, from 23-17's own worst observed legs: `165.79 s train + 1109.24 s score = 1275.03 s`.

| Seed | train s | ≤205.44 | score s | ≤1026.87 | total | ≤1275.03 |
|---|---|---|---|---|---|---|
| 2025 | 166.75 | ✓ | 973.62 | ✓ | 1140.38 | ✓ |
| 1339 | 155.67 | ✓ | 971.82 | ✓ | 1127.49 | ✓ |

**Named rather than absorbed, since 23-17 named its own:** seed 2025's training leg (166.75 s) is
`+0.96 s` above the previous worst-observed training leg (2024's 165.79 s). It is well under the
committed `≤205.44 s` training bound, so it breaches nothing — it is stated only because 23-17's
register says a figure that exceeds a prior maximum gets said out loud.

**Whole run, launch → record: 2269.93 s = 37.8 min**, under the plan's 2550.06 s ≈ 42.5 min estimate.
23-17's run was killed at ~60 min at 3 of 5 seeds; this one finished 2 of 2 owed seeds in 37.8 min.

## grad_clip: non-binding on both new seeds, proven BEFORE each was scored

| Seed | calls | `MAX_STEPS` | bound | pre-clip norm range |
|---|---|---|---|---|
| 2025 | 200 | 200 | **0** | `[0.35307, 2.26006]` |
| 1339 | 200 | 200 | **0** | `[0.35301, 2.30167]` |

The call count matters as much as the bind count: `bound_count == 0` is also what a never-taken
branch reports, so `calls == MAX_STEPS` is what proves the equalisation actually ran.

**Against the DP arm's measured `1.538`–`2.278`, stated rather than smoothed:** seed 2025's top end
`2.26006` sits **below** `2.278`. **Seed 1339's `2.30167` EXCEEDS it by `+0.02367`** — the same
direction and roughly the same magnitude as 23-17's seed 2024 (`2.29014`, `+0.012`). Both bottom
ends (`0.353`) sit well below `1.538`. `C = 1e6` clears every one of them by more than five orders of
magnitude, so nothing here approaches binding.

## The call site: both rules reachable, the frozen one unfiltered

Verified by AST, not grep (the file's prose names both functions):

```
sorted(called_attrs & {'prove_first_attempt','prove_killed_run_continuation'})
  -> ['prove_first_attempt', 'prove_killed_run_continuation']
type(guard.test).__name__ -> UnaryOp          # NOT BoolOp
```

`if not matched_glob_at_start and not scored:` would only ever hand the frozen rule an argument
control flow had already proved empty — **filtering by control flow**, which makes
`prove_first_attempt`'s refusal unreachable while the call site still reads correctly. `not scored`
alone is one token shorter and strictly stronger. The **B4 case** — a tracked artifact beside an
EMPTY scored set — is watched firing in
`test_both_one_attempt_rules_are_reachable_and_the_frozen_one_gets_an_unfiltered_argument`, raising
`SystemExit` containing `ONE ATTEMPT — REFUSED`.

**The GATE-ONLY check, run before the launch and at zero GPU cost, observed output:**
```
ADMITTED True
[phase23_run] matched preflight: 7 dp_fn branch(es), 21 production train() keyword(s), 19 on the
comparator (= production - {resume_from, dp_fn}) — all three AST gates GREEN
census 7
```

And the live run's own first two lines after the session banner:
```
[phase23_run] CONTINUATION of a killed run ADMITTED by
phase23_resume_prereg.prove_killed_run_continuation: scored [1337, 1338, 2024], trained
[1337, 1338, 2024], HEAD agrees at [1337, 1338, 2024], 3 tracked per-seed curve(s)
```

### The retained `_prove`, at TRUE strength

`scripts/phase23_run.py`'s (2b) `_prove` is retained, reachable on the first-attempt branch, and its
**rendered message is byte-identical** (only the source line break moved, because the deeper indent
pushed one fragment past 100 columns — recorded in a comment beside it). **But it is UNFIREABLE on
that branch**, and saying "not softened" without that would be the overclaim this plan's register
exists to refuse: `rp.seed_status`'s `scored` and `prior_scored_seeds_at_start` are the SAME
predicate (`"primary" in block`) over the SAME dict, so `not scored` implies
`not prior_scored_seeds_at_start` and the `_prove`'s first disjunct is tautologically true there. It
is a reader-visible marker of the rule that governed before the split, not a live refusal.

**And the relationship between the two rules, at TRUE strength:** the new predicate is **NOT
"strictly more demanding"**. On the one state that matters (3 scored, record absent) the old `_prove`
REFUSES and the new one ADMITS — in OUTCOME it is strictly more **PERMISSIVE**, which is the entire
point of it existing. What is stronger is its **SHAPE**: seven NAMED conjuncts against one, plus
committed-vs-working-tree agreement, ladder-prefix shape and tracked-path shape, none of which the
old `_prove` checked at all. The phrase "strictly more demanding" appears nowhere in the code, the
commits or this document except in this sentence disclaiming it.

## The record's disclosure

`results/phase23_matched_control.json` carries, beside the four UNEDITED attempt-state keys:

| Key | Value |
|---|---|
| `attempt` | `"continuation"` |
| `continuation_rule` | `"phase23_resume_prereg.prove_killed_run_continuation"` |
| `continuation_fingerprint` | all SIX inputs, `tracked` included |
| `continuation_scope` | `rp.CONTINUATION_SCOPE` VERBATIM (five clauses) |
| `continuation_discrimination` | one sentence naming the write-ordering |

The fingerprint **IS the argument dict** — `rp.prove_killed_run_continuation(**continuation_fingerprint)`
— so what the record publishes is literally what the predicate saw, not a hand-copied echo of it.
`ladder` is `list(SEED_LADDER)` = `[1337, 2024, 1338, 2025, 1339]`, **in LADDER ORDER and never
sorted**: conjuncts 3 and 4 INDEX it, and `sorted(SEED_LADDER)` = `[1337, 1338, 1339, 2024, 2025]`
would make `set(ladder[:3])` read `{1337,1338,1339}` and every re-admission REFUSE. Re-admission with
its own tracked list prints `True`, so conjuncts 6 and 7 are exercised on every suite run rather than
satisfied vacuously.

`one_attempt_rule` and the whole `one_attempt_scope` clause block are UNTOUCHED. The frozen rule
still governs; the continuation is an exception that arrived beside it, not a replacement.

## Seed 2025's partial bytes: discarded visibly, in their own commit

`a629d93` removes `results/phase23_matched_control_seed2025/run.csv` (`git rm`) and
`checkpoints/phase23_matched_control_seed2025_latest.pt` (plain `rm` — gitignored). All four
justifications are in the commit message body, where an auditor will look:

1. **Seed 2025 produced NO READING** — no `primary` block, no entry in the state file's `matched`
   section at all, no adapter. `matched()`'s own comment at `:2156-2158` states the governing
   distinction verbatim: the predicate is *scored*, not *trained*.
2. **A mid-train resume is REFUSED by a committed mechanism.** `prove_matched_protocol`
   (`scripts/phase23_run.py:1181-1187`) refuses `resume_from`, and two
   `DP_FN_BRANCH_DISPOSITIONS` items are dispositioned `unreached` precisely because this scheduling
   resumes nothing. D-07's `refuse_if_exists(expected=...)` inversion exists and was deliberately
   not used.
3. **The deletion is a VISIBLE DIFF**, and the recovery command in the message works —
   `git show d99d2aa:results/phase23_matched_control_seed2025/run.csv` still prints 6 lines. **Both
   halves said:** the `latest.pt` is gitignored and is **NOT recoverable from git**; it is
   regenerable from `seed_everything(2025)` plus the pinned corpus.
4. **Nothing scored was touched** —
   `git diff --exit-code d99d2aa HEAD -- results/phase23_matched_control_seed{1337,2024,1338} data/phase23_run_state.json`
   exited 0 at that point.

## Deviations from Plan

**None of substance. Three procedural notes, all disclosed rather than absorbed.**

### 1. [Procedural] The `_prove` message's source wrapping moved by one fragment

The plan requires the retained (2b) `_prove` kept "verbatim, byte-for-byte". Moving it inside the
`if not scored_seeds:` branch added four columns of indent and pushed one string fragment to 101
characters, which `ruff` (line-length 100) rejects. The fragment boundary was moved
(`"…the state a " + "deleted-and-re-run first attempt…"` instead of
`"…the state a deleted-and-re-run " + "first attempt…"`); the **rendered message is unchanged**,
verified by substring match against `git show HEAD:scripts/phase23_run.py`. A comment beside the call
records it.

### 2. [Procedural] The second kill never happened, so the commit-then-relaunch remedy was not exercised

Conjunct 5's remedy path is pre-registered, self-checked and tested, but the run completed on its
first launch, so it was never needed in anger. Recorded so a reader does not infer it was proven in
production.

### 3. [Plan instruction] Commit type `revert` for Step A

The plan prescribes `revert(23-20): …` for the deletion commit. `revert` is not in the executor's
standard commit-type table; the plan's explicit instruction was followed.

**No authentication gates occurred. No package was installed.** No refusal fired unexpectedly; no
seed was re-run, re-seeded, widened or tuned; no artifact was deleted to make an attempt look like a
first one; no force flag, override or warning branch was added to any refusal.

## TDD Gate Compliance

Tasks 1 and 2 are declared `tdd="true"`, but the plan's own `<action>` prescribes a single commit per
task (`feat(23-20): …`) with the module written before its tests. There is therefore **no separate
`test(...)` RED-gate commit** for either task. The RED evidence exists but is not separately
committed: each refusal is watched firing against a constructed defect inside the tests and inside
the module's `__main__` self-check, which is this repository's established register (23-15…23-17 all
did the same). Recorded here rather than silently satisfied.

## Verification

| Check | Command | Result |
|---|---|---|
| Frozen matched pin | `git diff --exit-code c100388 HEAD -- scripts/phase23_matched_prereg.py` | **exit 0** |
| …still ONE commit | `git log --format=%H -- <pin> \| wc -l` | **1** |
| Closed pin | `git diff --exit-code c7de5d4 HEAD -- scripts/phase23_prereg.py` | **exit 0** |
| Resume pin written once | `git log --format=%H -- scripts/phase23_resume_prereg.py \| wc -l` | **1** |
| Ancestry guard | `pytest tests/test_phase23_matched_prereg.py -q` | **12 passed** (at 3 tracked, and again at 6) |
| Self-check, every refusal | `.venv/bin/python scripts/phase23_resume_prereg.py` | exit 0, 3 admissions + 9 refusals printed |
| No float constant | AST walk of the module | `[]` |
| Signature carries no reading | AST kwonlyargs | the six declared names, `[] []` |
| Module imports | AST | `['phase23_matched_prereg']` only — no `subprocess`, `torch`, `requests`, `urllib`, `os` |
| Module reads no live state | AST exact-constant | `[]` |
| Test fixture PINNED | AST exact-constant | `True False False` |
| Both branches reachable | AST over `matched` | `['prove_first_attempt','prove_killed_run_continuation']` |
| Frozen refusal unfiltered | AST guard node type | `UnaryOp` (not `BoolOp`) |
| Reduction CALLED, not inlined | `test_the_matched_writer_does_not_inline_the_reduction` | PASS |
| Record floor re-derives | inline `noise_floor` check | `OK floor 0.0267857142857143 over 5 readings` |
| Fingerprint re-admits with own `tracked` | direct call | `True` |
| Deletion visible + recoverable | `--diff-filter=D` / `git show d99d2aa:…` | `1` / `6` lines |
| Tracked matched artifacts | `git ls-files 'results/phase23_matched_*'` | **6** (5 curves + the record) |
| `results/` + `data/` clean | `git status --porcelain` | empty |
| Detachment evidence committed | `head -1 results/phase23_resume_run.log` | `SESSION pid=23851 pgid=23851 sid=23851` |
| **Full suite** | `.venv/bin/python -m pytest -q` | **`1538 passed, 1 skipped`** (83 warnings, 369.14 s) |
| Lint | `ruff check . && ruff format --check .` | clean, 219 files |

**Suite arithmetic: `1538 = 1518` (the session baseline at HEAD) `+ 19` (`tests/test_phase23_resume_prereg.py`) `+ 1`
(`test_both_one_attempt_rules_are_reachable_and_the_frozen_one_gets_an_unfiltered_argument` in
`tests/test_phase23_matched.py`).** No pre-existing test changed status. One pre-existing test was
**widened, not deleted**: `test_matched_record_records_the_attempt_state`'s two `== []` assertions
(`matched_glob_at_start`, `prior_scored_seeds_at_start`) are now conditional on `record["attempt"]`,
with the continuation branch asserting strictly more (rule name, scope verbatim,
`record_exists is False`, scored == committed, scored shorter than the ladder, and a full
re-admission with the recorded `tracked`).

**Eight record guards moved from their VACUITY branch to their LIVE branch** now that the record
exists: `test_matched_record_floor_re_derives`,
`test_matched_record_carries_every_floor_provenance_key`,
`test_matched_record_grad_clip_was_non_binding_on_every_seed`,
`test_matched_record_declares_the_branch_census`, `test_matched_record_declares_the_visibility`,
`test_matched_record_records_the_attempt_state`, `test_matched_record_names_its_omitted_fields`,
`test_matched_record_names_the_superseded_ledger`.

## D-04 HALT compliance

**The halt stands and was not touched.** `git ls-files 'results/phase23_noised_*'` returns **0** at
the end exactly as at the start; nothing was written under `results/phase23_noised_*`.
`results/phase23_sigma_zero.json` and `results/phase23_control_floor.json` are byte-unchanged against
`d99d2aa`. `scripts/mitigation_gate.py`, `scripts/mitigation_accountant.py`,
`scripts/mitigation_budget.py`, `scripts/teach_persona.py` and `src/personacore/training/loop.py` are
byte-unchanged. `results/phase23_matched_verdict.json` does not exist. `sigma_zero_verdict` was not
called. `.planning/debug/sigma-zero-beats-control.md` was not touched — it is 23-19's.

## Requirements

**NO requirement is ticked, and none needs to be.** MEASURED at `.planning/REQUIREMENTS.md:156-160`,
`DPSGD-06` is ALREADY `[x] SATISFIED (plan 23-10)` — its tick records that the diagnostic FIRED and
that D-04 halted the sweep, not a passing verdict. It was not re-touched. CAL-01, CAL-02, CAL-05 and
CTRL-03 remain 23-11…23-14's **BLOCKED** scope. What this plan delivers is the comparator record;
the re-pin is 23-18's and the verdict is 23-19's.

## Known Stubs

None. The record exists, every guard that was vacuous is now live, and nothing here is placeholder
data.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema at a trust boundary. No
package was installed (T-23-SC holds). One register note for the next planner: **T-23-77 was accepted
and disclosed, not mitigated** — `scripts/phase23_resume_prereg.py` **cannot** be frozen by the
phase-20 ancestry guard (`adds[-1]` for `MATCHED_ARTIFACT_GLOB` is `d99d2aa`, which precedes it), so
`test_the_resume_pin_has_exactly_one_commit` is **detection after the fact, not prevention**. That is
clause (5) of `CONTINUATION_SCOPE`, and it travels with the record.

## Notes for 23-18 and 23-19

1. **The floor to re-pin is `0.0267857142857143`**, as counts `790/1008 − 763/1008 = 27/1008`. It is
   the RANGE over five readings, reduced by `phase23_prereg.noise_floor` CALLED, and it re-derives
   from the record's own per-seed counts under exact `==`.
2. **The central reading is `readings[0]` at seed 1337 = `0.7837301587301587`**, recorded as
   `central_reading` / `central_reading_seed` and pinned blind at `c7de5d4`.
3. **The record declares it was a continuation.** A reader who opens only the artifact learns it, by
   which rule, and under what five-clause scope.
4. **Do not delete anything to re-run.** The state file's `matched` section now carries five scored
   seeds and is committed, so any deletion is a visible diff against `04cdb21`.
5. **`sorted(SEED_LADDER)` is not ladder order.** `[1337, 1338, 1339, 2024, 2025]` vs
   `(1337, 2024, 1338, 2025, 1339)`. Anything indexing the ladder must use ladder order.

## Self-Check: PASSED

- `scripts/phase23_resume_prereg.py` — FOUND, exactly one commit (`e70a035`)
- `tests/test_phase23_resume_prereg.py` — FOUND, 19 tests passing
- `results/phase23_matched_control.json` — FOUND, 5 seeds, floor re-derives
- `results/phase23_matched_control_seed2025/run.csv` — FOUND and committed
- `results/phase23_matched_control_seed1339/run.csv` — FOUND and committed
- `results/phase23_resume_run.log` — FOUND and committed, first line `SESSION pid=23851 pgid=23851 sid=23851`
- `data/phase23_run_state.json` — FOUND, 5 scored matched seeds, committed same-session with the record
- Commits `e70a035`, `a629d93`, `d8f4263`, `04cdb21` — all FOUND in `git log`
- `scripts/phase23_matched_prereg.py` — byte-identical to `c100388`, ONE commit
- `scripts/phase23_prereg.py` — byte-identical to `c7de5d4`
- `git ls-files 'results/phase23_noised_*'` — **0**
- `results/phase23_matched_verdict.json` — confirmed ABSENT
