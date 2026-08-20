---
phase: 19-selective-memory-erasure
plan: 07
subsystem: testing
tags: [pre-registration, human-checkpoint, pin-audit, dialogue-noise-floor, seed-pair, d3, representational-read, fisher-overlap, cli-closure, erase-01, stat-05]

requires:
  - phase: 19-selective-memory-erasure
    provides: "19-01..19-06's complete pin — mechanism, target, denominator, floor, estimators, arm runners, report text, closed CLI"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "`results/phase18_arm_adapter-on.json` and `results/phase18_corpus.json` — the committed records the audit measured the (b) row set against"
provides:
  - "the human-reviewed pin — the amendment window used, then closed"
  - "`dialogue-floor` subcommand + `DIALOGUE_FLOOR_RECORD_PATH` + `DIALOGUE_FLOOR_ARM` + `dialogue_floor_from_record`"
  - "`REPRESENTATIONAL_RECORD_PATH` + `_load_representational`; `_cmd_representational` now CALLS `fisher_overlap` and writes its record"
  - "`nontarget_rows` — the (a)/(b) split, by slot"
  - "a `report` subcommand that RUNS end to end, driven live rather than inspected"
affects: [19-08, 19-09, 19-10, 19-11, 19-12, 19-13, 19-14, 19-15, 19-16]

tech-stack:
  added: []
  patterns:
    - "drive the subcommand, do not read it — `report` passed every structural scan in 19-05 and 19-06 and crashed four separate ways the first time it was executed"
    - "a defect in the MECHANISM is fixed by wiring the mechanism, never by amending the prose to describe the defect as intentional"
    - "when a pinned guard bites correct-looking code, the CALLER changes: `_nontarget_rates` was right that (b) takes seven slots, and `_cmd_report` was wrong to hand it eight"
    - "an absent input record aborts NAMING the subcommand that writes it; a fallback is a second estimator chosen by which files happened to exist"

key-files:
  created: []
  modified:
    - scripts/phase19_erasure.py
    - tests/test_phase19_erasure.py

key-decisions:
  - "BLOCKER 1 fixed by WIRING the pinned seed pair, not by amending `DIALOGUE_NOISE_FLOOR_ESTIMATOR`. The estimator's text was already correct; the code did not match it. Amending the clause to describe (post - pre, one arm) as intentional would have documented a defect as a decision — the same class as 19-03's pinned sentence claiming the floor 'rounds toward the harder side' when running the function showed it did not"
  - "BLOCKER 2 fixed by the PREFERRED route — carrying a real representational read into the report. The fallback (dropping the Fisher block) was rejected on evidence: `REPRESENTATIONAL_READ_LABEL`, `render_report`'s section 6 and `DESCRIPTIVE_ONLY_FUNCTIONS` naming `fisher_overlap` all promise that block, so dropping it loses something the pre-registration already promises to deliver"
  - "the (c) defect was NON-MONOTONE IN HARM, not merely mislabelled: at the measured pre-erasure PPL 5.8154 the old wiring failed on (5.4014, 7.0575) and CLEARED on both sides, because the cap widened in exact proportion to the damage"
  - "three further blockers were found ONLY by executing `_cmd_report`; all three are in code that passed every AST scan the pin already commits"
  - "`DIALOGUE_FLOOR_ARM` is never `real` — `teach_persona.arm_outputs` maps that arm to `checkpoints/persona_adapter.pt` unconditionally, so a `real`-named (c) re-teaching would overwrite the pre-erasure adapter the whole phase measures against"
  - "the (c) floor is DERIVED at report time by `dialogue_floor_from_record`, never stored as a scalar in its own record: a stored number would be a second copy free to disagree with the two PPLs beside it"
  - "the recipe is READ from `tp.arm_spec(\"real\")` rather than retyped, so the estimator's seven pinned values stay the live ones"

patterns-established:
  - "the audit DRIVES the artifact it audits, into a tempdir, with `render_report`'s call redirected — an audit that writes `results/phase19_erasure_report.md` closes the pin it is auditing (T-19-30). That footgun fired once, live, and was caught by checking the invariant after every run"
  - "every name in `SUBCOMMANDS` must appear in the module docstring's rule 2b, asserted by test, so the published set and the documented set cannot drift"

requirements-completed: [ERASE-01, STAT-05]

duration: 95min
completed: 2026-08-18
---

# Phase 19 Plan 07: The Gate Before the Pin Becomes Unamendable — Summary

**The human did not approve as-is. The audit's two blockers were fixed by changing the CODE, not
the prose — and driving `_cmd_report` live, which no prior plan had done, found three more. The
pinned `report` subcommand crashed four separate ways on records in the exact shape its own
writers produce. All five are fixed; the audit re-runs to ZERO blocker rows; the pin is closed.**

## Performance

- **Duration:** ~95 min (including the checkpoint pause)
- **Tasks:** 2 of 2 (Task 1 read-only; Task 2 the human gate, resumed with corrections)
- **Files modified:** 2 (0 created)
- **Tests:** +2 (820 -> 822 passed, same single pre-existing CUDA-only skip)

## The Two Routes Taken, and Why — Stated Explicitly

The human asked for this by name. Both are recorded here and in `3ba3e2c`'s message.

### Blocker 1 — the (c) dialogue noise floor: **WIRED the real seed-pair estimator**

The rejected alternative was amending `DIALOGUE_NOISE_FLOOR_ESTIMATOR` to describe the current
behaviour as intentional. It was rejected because **the estimator's text was already right and the
code was wrong.** Clause 1 says the floor is `|dPPL|` between *two independently seeded
re-teachings*; `DIALOGUE_NOISE_FLOOR_SEEDS = (1337, 2024)` was pinned at `:1040` and captioned at
`:2187`. What `_cmd_report` actually computed was `dialogue_noise_floor(post, pre)` off **one arm,
one process** — the erasure's own effect size — and published it under the seed pair's name.

Amending the clause would have documented a defect as a decision. This phase already caught that
exact move once: 19-03's pinned sentence claimed the floor "rounds toward the harder side" and
running the function showed it did not.

### Blocker 2 — `_cmd_report`'s hardcoded literal: **carried a REAL representational read**

The preferred route, taken. The fallback (drop the Fisher block) was permitted only if it lost
nothing the pre-registration promises. It loses three promised things, so it was not taken:

| promise | where |
|---|---|
| the Fisher block is rendered with both denominators and no ratio | `render_report` §6, `:2226-2231` |
| `fisher_overlap` is one of the three functions 19-14 will **call rather than commit** | `DESCRIPTIVE_ONLY_FUNCTIONS = ("delta_w_cells", "delta_w_cosine", "fisher_overlap")` |
| the read is published "with its denominators", never converted to pass/fail | `REPRESENTATIONAL_READ_LABEL` |

`_cmd_representational` now calls `fisher_overlap` over the ablated addresses **read off the
erased arm's own record** and writes `results/phase19_representational.json`; `_cmd_report` loads
it and aborts naming the subcommand if it is absent.

## The Three Blockers Only a Live Drive Could Find

`report` is the subcommand the phase's verdict comes out of. It had passed every structural scan
19-05 and 19-06 committed. It had never been executed.

| # | Defect | Raised |
|---|--------|--------|
| 3 | `target_fact_id(erased["per_fact"])` — `per_fact` keys the id, so iterating yields strings | `TypeError: string indices must be integers` at `:3541` |
| 4 | `nontarget_deltas` handed all EIGHT core slots; `_nontarget_rates` proves exactly the seven non-targets | `PROOF FAILED: the pre-erasure rows cover slots [...8...]` |
| 5 | `deltas` is a TUPLE ordered by `GATED_NONTARGET_SLOTS`; `_cmd_report` used `.values()` and `sorted(deltas)` | `AttributeError: 'tuple' object has no attribute 'values'` |

**No guard was weakened to fit any of them.** #4 in particular: `_nontarget_rates`'s proof that
(b) takes exactly seven slots is correct and untouched — the target's own slot belongs to
condition (a). The caller now removes that row, by slot, through `nontarget_rows`.

## Task Commits

1. **Task 1** — no commit. `<files>(read-only)</files>`, and T-19-30 makes the audit stdout-only:
   an audit file under `results/phase19_*` would itself close the pin before the human read it.
   No `scripts/phase19_*.py` audit script was added either — it would enter `_GATE_MODULES` and
   add a commit to the pin's own file set at the moment the pin closes.
2. **The five fixes** — `3ba3e2c` (fix): the seed-pair wiring, the representational record, and
   the three runnability defects.
3. **The tests** — `0c5e754` (test): 2 tests, one behavioural + structural for blocker 1, one
   end-to-end drive of `_cmd_report` for blockers 2-5.

## Files Created/Modified

- `scripts/phase19_erasure.py` (modified, 3632 -> 3887 lines). sha256
  `c407246de3c470094ab0bdd868961b7b1c22529c5e00522fec67c3852cb6e303`. **11 subcommands now**,
  not ten: `dialogue-floor` was added to `SUBCOMMANDS`, to `_SUBCOMMAND_TABLE` and to the module
  docstring's rule 2b together, because the module-scope `_prove` requires the published set and
  the runnable set to be one set.
- `tests/test_phase19_erasure.py` (modified, 3508 -> 3631 lines), 90 tests, all CPU-only.

## Evidence

### The audit, re-run against the committed tree — ZERO blocker rows

```
================================================================================================
. VERDICT
================================================================================================
no blocker rows.

1 NOTE(S) — plan-vs-pin naming, not a defect in the pin:

  1. D7: the plan names TARGET_FACT_ID; the pin has no such constant (see note)

results/phase19_* tracked : 0
phase18_extraction commits: 26
pin commits to be checked : 15
```

The single NOTE is unchanged from Task 1 and is not a defect: the plan names D7's landing site
`TARGET_FACT_ID`, and the pin deliberately has no such constant because **no fact value may enter
this file** and every core `fact_id` ends in its own value (module docstring `:95-100`). The
target is keyed by `TARGET_SLOT = 'pet_name'`; `target_fact_id(records)` resolves the id from DATA
at call time.

### Blocker 1 — the seed pair is now consumed, and the caption is now true

```
wiring at _cmd_report:
    dialogue_ppl_noise_floor = dialogue_floor_from_record()
    dialogue_ppl             = post['dialogue_ppl']['adapter_on']

DIALOGUE_NOISE_FLOOR_SEEDS = (1337, 2024)
  every occurrence in the pin (10): [... :1041, :1050, :2187, :2616, :2622, :2624, :2628,
                                     :3628, :3650, :3658]

  the floor is NOT computed inside _cmd_report : True (producer is `dialogue_floor_from_record()`)
  subcommands that CONSUME the pinned seed pair : ['dialogue-floor']
  `dialogue-floor` re-teaches per seed (train_arm(..., seed=seed)) : True
  and scores each adapter through dialogue_ppl_pair              : True
  never the `real` arm (that path IS checkpoints/persona_adapter.pt): True (arm stem 'erase_dialogue_floor')
  an ABSENT record aborts, naming the subcommand : True
```

Before this plan the seed pair occurred **3** times — defined, commented, rendered — and was read
by no code path that produced a number.

### Why blocker 1 was arithmetic, not labelling — the old wiring, computed live

```
Had the floor stayed a (post, pre) difference off one arm, the (c) criterion would read:
  clears iff  post <= 4.5733 + 2 * |post - 5.8154|

  post-erasure dialogue PPL    cap it would generate   clears (c)?
  --------------------------------------------------------------------------
  4.5733                       7.057500                CLEARS
  5.0000                       6.204100                CLEARS
  5.4014                       5.401300                fails
  5.4015                       5.401100                fails
  5.8154                       4.573300                fails
  6.5000                       5.942500                fails
  7.0574                       7.057300                fails
  7.0575                       7.057500                fails
  8.0000                       8.942500                CLEARS
  12.0000                      16.942500               CLEARS
```

**NON-MONOTONE IN HARM.** It fails on `(5.4014, 7.0575)` and clears on both sides: a catastrophic
erasure would have cleared (c)-dialogue and a mild one would not, because the cap widened in exact
proportion to the damage. That is the "wider ruler" the estimator's own clause 6 and
`D8_PUBLICATION_POSTURE` both name as the thing not to do. The seed-pair floor has no such term —
it does not move when the erasure gets worse.

### `report` DRIVEN LIVE, end to end — the check that reading could not perform

```
  (a) with NO representational record — must ABORT, naming the subcommand:
      SystemExit: [phase19_erasure] PROOF FAILED: .../phase19_representational.json does not exist. ...
  (b) with every required record present — must COMPLETE:
      _cmd_report COMPLETED; wrote a 92-line report
      (c) caption: ...MEASURED noise floor of 0.017500 (`DIALOGUE_NOISE_FLOOR_ESTIMATOR`,
                   seeds (1337, 2024)). Pre- and post-erasure are pri...
      the number beside 'seeds (1337, 2024)' IS that pair's spread (0.017500): True
      condition (b) table rows: 7 — ['cat_name', 'street', 'sibling_name', 'person_name',
                                     'house_number', 'birth_year', 'hometown']
```

Seven (b) rows, never eight, and the target's slot absent from that table.

### Blocker 4 verified against the COMMITTED Phase 18 record, not a fixture

```
$ REAL pre_erasure per_fact slots:
['birth_year', 'cat_name', 'hometown', 'house_number', 'person_name', 'pet_name',
 'sibling_name', 'street']
n rows: 8   TARGET_SLOT present: True
GATED_NONTARGET_SLOTS: 7
```

The Phase 18 corpus covers exactly the eight core slots, so both `per_fact` blocks carry eight
rows and dropping the target leaves exactly seven. `nontarget_rows` is that drop.

### The invariants held at every step

```
$ git ls-files 'results/phase19_*'          -> 0     (checked at start, after every commit, at end)
$ git status --porcelain -uall | grep results/phase19_  -> (none)
$ git log --format=%H -- scripts/phase18_extraction.py | wc -l
      26                                              # 26 before Phase 19, 26 now
```

**One live near-miss, recorded rather than hidden.** The first end-to-end drive of `_cmd_report`
wrote a real `results/phase19_erasure_report.md` into the repo, because `render_report`'s `path`
default is bound at def time and rebinding the module constant does not move it. It was untracked,
`git ls-files` never left 0, and it was deleted immediately. Both the audit harness and the
committed test now redirect the `render_report` **call**. Without that redirect the committed test
suite would write a `results/phase19_*` artifact on every CI run and redden the ancestry guard
permanently.

### Full suite and lint, from a fresh run on the committed tree

```
$ .venv/bin/python -m pytest -q
822 passed, 1 skipped, 83 warnings in 166.20s (0:02:46)

$ .venv/bin/python -m ruff check . && .venv/bin/python -m ruff format --check .
All checks passed!
166 files already formatted
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `_cmd_report` crashed on `target_fact_id(erased["per_fact"])`**
- **Found during:** Task 2, driving the `report` subcommand
- **Issue:** `per_fact` is `{fact_id: row}`; iterating it yields strings, so `record["slot"]`
  raised `TypeError`. Every other call site (`:748`, the committed tests) passes `record["draws"]`.
- **Fix:** pass `erased["draws"]`, the shape the docstring names
- **Commit:** `3ba3e2c`

**2. [Rule 1 - Bug] the (b) inputs carried the target's own row**
- **Found during:** Task 2, same drive
- **Issue:** `nontarget_deltas` received all eight core slots; `_nontarget_rates` proves exactly
  the seven non-targets. Verified against `results/phase18_arm_adapter-on.json`.
- **Fix:** `nontarget_rows` removes the target's row by slot, at all four call sites. The guard was
  **not** weakened.
- **Commit:** `3ba3e2c`

**3. [Rule 1 - Bug] `deltas` treated as a mapping**
- **Found during:** Task 2, same drive
- **Issue:** `nontarget_deltas` returns a tuple ordered by `GATED_NONTARGET_SLOTS`;
  `_cmd_report` called `.values()` on it and iterated `sorted(deltas)` as fact ids.
- **Fix:** pass the tuple straight through, iterate the seven non-target ids for the table rows
- **Commit:** `3ba3e2c`

**4. [Rule 2 - Missing critical functionality] the plan declared `files_modified: []`**
- **Issue:** 19-07 is a review gate and expected to modify nothing. The human's corrections
  required amending the pin — which is legal at 19-07 and **illegal from 19-08 onward**.
- **Resolution:** the amendment window was used deliberately and for exactly the gap the audit
  identified (§8: no subcommand in the closed set of ten trained a second-seeded adapter, while
  `teach_persona.train_arm` has taken `seed=` since `:530`). This is the reason the gate exists.

### Not a Deviation — the checkpoint

Task 2 is a `checkpoint:human-verify` with `gate="blocking"`. It paused, the human reviewed the
audit, withheld approval and routed both blockers explicitly. This is the plan working as written.

## Handover to 19-08+

1. **The pin is CLOSED.** From the first `results/phase19_*` commit onward, all **15** commits to
   `scripts/phase19_erasure.py` must be ancestors of that artifact's first-add. There is no skip
   path and no force flag.
2. **19-10 now has a subcommand:** `python scripts/phase19_erasure.py dialogue-floor`. It costs
   two adapter retrains (~81 s each per `results/phase17_training_run.log:19,39,58`) plus two
   `masked_perplexity` pairs. It refuses to clobber its own record.
3. **19-14 must run `representational` BEFORE 19-15 runs `report`.** `report` now aborts naming
   the subcommand if `results/phase19_representational.json` is absent. `_cmd_representational`
   reads the ablated addresses off the **erased** arm record, so 19-11 must precede it.
4. **19-12 still must pass `adapter_path=` explicitly** to `run_bit_identity_control`; left alone
   it passes while measuring the production adapter (19-06 handover 7, re-confirmed by audit §10).
5. **The (c) result is published as FAILURE regardless of where the floor lands** (D3). The
   pre-erasure adapter already exceeds the Δ_dialog cap by **+1.2387**. A floor wide enough to
   admit that reading is not a better result; it is a wider ruler, and the report says so.
6. **Do not add anything to `scripts/phase19_erasure.py`.** If a run needs something the pinned
   CLI cannot express, the answer is an unpinned throwaway (`python -c ...`, or a new
   `scripts/phase19_run.py`) — never a commit here.

## Self-Check: PASSED

- `scripts/phase19_erasure.py` — FOUND (3887 lines, sha256 `c407246d...`)
- `tests/test_phase19_erasure.py` — FOUND (3631 lines)
- `.planning/phases/19-selective-memory-erasure/19-07-SUMMARY.md` — FOUND
- commit `3ba3e2c` — FOUND
- commit `0c5e754` — FOUND
- `git ls-files 'results/phase19_*'` — 0, as required at the moment the pin closes
- `git log --format=%H -- scripts/phase18_extraction.py | wc -l` — 26, unchanged
