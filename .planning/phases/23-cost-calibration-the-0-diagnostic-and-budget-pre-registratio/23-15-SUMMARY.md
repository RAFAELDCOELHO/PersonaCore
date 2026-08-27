---
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
plan: 15
subsystem: pre-registration
tags: [pre-registration, dp-sgd, comparator, ast-census, blind-commit, d-04]
requires:
  - scripts/phase23_prereg.py (imported by nothing here; asserted BYTE-UNCHANGED)
  - src/personacore/training/loop.py (the dp_fn branch census reads it live)
  - scripts/teach_persona.py (the wiring + train-call censuses read it live)
  - tests/test_phase23_prereg.py::_ordering_guard (IMPORTED, never copied)
  - tests/test_phase20_prereg.py::_git (IMPORTED, never copied)
provides:
  - scripts/phase23_matched_prereg.py (the blind protocol pin, EDIT-ONCE from 23-17's first artifact)
  - MATCHED_CONTROL_RECORD / MATCHED_VERDICT_RECORD / MATCHED_ARTIFACT_GLOB / matched_arm
  - MATCHED_GRAD_CLIP (1e6, with a re-measured exception-bounded inertness claim)
  - DP_FN_BRANCH_COUNTS / DP_FN_BRANCH_DISPOSITIONS / dp_fn_branch_census / prove_branch_ledger_complete
  - DP_TRAIN_KEYS / DP_KWARGS_KEYS / dp_wiring_key_census / prove_dp_wiring_keys
  - TRAIN_CALL_KEYS / prove_train_call_keys
  - MATCHED_EQUALISED / MATCHED_DIFFERENCES
  - prove_first_attempt (one attempt, four scope clauses)
  - SIGMA_ZERO_VISIBILITY_DISCLOSURE / VERDICT_REQUIRED_KEYS
  - prove_verdict_record_declares_visibility / prove_control_record_declares_visibility
affects:
  - 23-16 (preflight checks the TRAIN_CALL_KEYS subtraction)
  - 23-17 (writes MATCHED_CONTROL_RECORD; bound by prove_first_attempt + the control disclosure)
  - 23-18 (the budget; untouched here)
  - 23-19 (writes MATCHED_VERDICT_RECORD; bound by VERDICT_REQUIRED_KEYS)
tech-stack:
  added: []
  patterns:
    - "AST census over live source in place of hand enumeration (the 23-08 defect, closed structurally)"
    - "`_prove`/SystemExit refusal register, never `assert` (python -O strips assert)"
    - "blind pre-registration committed while the glob it governs is empty"
    - "a guarantee stated at its true strength, with its residual disclosed rather than closed"
key-files:
  created:
    - scripts/phase23_matched_prereg.py
    - tests/test_phase23_matched_prereg.py
  modified:
    - tests/test_phase23_resume.py
decisions:
  - "Committed both new files in ONE commit, as the plan's Task 2 requires — and folded the
     test_phase23_resume.py register update into the same commit so the suite is GREEN at that
     commit rather than red at an intermediate one."
  - "RE-MEASURED the grad-clip inertness claim on this machine rather than inheriting the
     plan-checker's figure. The plan's figure reproduced AND a further finding was made that the
     plan did not record (see Divergences)."
  - "Registered the two new files' synthetic AST fixtures in test_phase23_resume.py's call-site
     register under a new `fixture` kind, rather than dodging its grep by writing `train_arm (`.
     Evading a guard is not fixing one, and the register exists to be updated."
metrics:
  duration: ~65min
  completed: 2026-08-27
  tasks: 2
  files: 3
  commits: 1
---

# Phase 23 Plan 15: The Protocol-Matched Comparator's Blind Pre-Registration — Summary

Every rule that will govern the protocol-matched comparator is now committed **while
`git ls-files 'results/phase23_matched_*'` returns nothing** — the artifact register, the
non-binding grad clip, three AST completeness censuses, the seven-branch disposition ledger, the
one-attempt rule stated at its true strength in four clauses, and the σ=0 visibility disclosure
required of *both* downstream records. `scripts/phase23_prereg.py` is byte-identical to `c7de5d4`.

**Commit:** `c100388` — `feat(23-15): pre-register the protocol-matched comparator BLIND`

## The blindness claim, as recorded at commit time

The emptiness of the matched glob **is** the blindness claim, so the command and its output are
quoted rather than described. Run immediately before `git commit`:

```
$ git ls-files 'results/phase23_matched_*'
$ git ls-files 'results/phase23_matched_*' | wc -l
       0
```

No output. Re-run immediately **after** the commit: still `0`. The pin therefore precedes every
artifact it governs as a fact about git's object graph, not as a claim in a paragraph.

## Critical premises — all three verified before any work started

The plan is a blind pre-registration whose correctness depends on repository facts at execution
time. All three were re-verified, not assumed:

| Premise | Verification | Result |
|---|---|---|
| `git ls-files 'results/phase23_matched_*'` returns exactly 0 lines | `git ls-files 'results/phase23_matched*' 'results/phase23_rematch*' \| wc -l` | **0** ✓ |
| `scripts/phase23_prereg.py` byte-identical to `c7de5d4` | `git diff --exit-code c7de5d4 -- scripts/phase23_prereg.py` | **exit 0** ✓ |
| `data/phase23_run_state.json` tracked, committed baseline has NO `matched` section | `git ls-files`; `git show cfa2c87:… \| json keys` | tracked; keys = `['control', 'cost', 'never_taught', 'sigma_zero']` ✓ |

`.gitignore:14` = `checkpoints/` and `.gitignore:17` = `data/` were also confirmed by line number,
since the honest wording of `prove_first_attempt` rests on both.

## Re-measured counts — every one reproduces

The plan instructed me to re-measure its stated counts against live source and report divergence
rather than silently adopting either number. **All three reproduce exactly.**

| Quantity | Plan states | Measured here | Agrees |
|---|---|---|---|
| `dp_fn`-conditioned branches in `training/loop.py` | 7 | **7** | ✓ |
| — `("_optimizer_step", "dp_fn is not None")` | 3 | **3** | ✓ |
| — `("_optimizer_step", "dp_fn is None")` | 1 | **1** | ✓ |
| — `("_dp_extra", "dp_fn is None")` | 1 | **1** | ✓ |
| — `("train", "dp_fn is None and ckpt.get('dp_noise_rng') is not None")` | 1 | **1** | ✓ |
| — `("train", "dp_fn is not None and ckpt.get('dp_noise_rng') is not None")` | 1 | **1** | ✓ |
| `dp_accum` keys | 1 (`grad_accum_steps`) | **1** | ✓ |
| `dp_kwargs` keys | 6 | **6** | ✓ |
| `train(...)` named kwargs at `teach_persona.py:1613` | 15 | **15** | ✓ |
| splats | 1 (`**dp_kwargs`) | **1** | ✓ |
| **`TRAIN_CALL_KEYS` union** | **21** | **21** | ✓ |

Line numbers also reproduce (`L189/211/213/220` in `_optimizer_step`, `L709` in `_dp_extra`,
`L766/781` in `train`; `dp_accum` at `:1585`, `dp_kwargs` at `:1586`, the call at `:1613`).

## Divergence: the grad-clip inertness re-measurement

The plan required re-measuring the `MATCHED_GRAD_CLIP` inertness claim on this machine, because
that comment is edit-once and a number that cannot be corrected must not be inherited on trust.
Measured: 3 trials × 65,536 float32 elements, normal-range gradients scaled to ‖g‖ ≈ 2, subnormals
planted, `clip_grad_norm_` at `C = 1e6`, CPU and MPS, torch 2.7.1.

**The plan's figure reproduced.** CPU is bitwise identical including planted subnormals
(0/65,536 changed). MPS is bitwise identical for normal-range gradients but flushes subnormals:
`1.401298464324817e-45 → 0.0` and `4.999999675228202e-39 → 0.0`, while the smallest normal float32
(`1.1754943508222875e-38 = 2**-126`, verified against `torch.finfo(torch.float32).tiny`) and `1e-30`
both survive. The boundary is exactly the subnormal threshold.

**One finding the plan's inherited figure did NOT record, and it is the reason re-measuring was
worth the seconds:**

> **An on-device bitwise check cannot see this flush.** `torch.equal(before, after)` evaluated on
> MPS returns `True`, and `(before != after).sum()` returns `0`, because the comparison operator
> flushes its own subnormal operands too. The flush is visible only by reading elements back to
> host with `.item()`.

Isolated further: the subnormals **survive the host→device copy intact**, so it is the clip's
`_foreach_mul_` — not the transfer — that flushes them.

Consequence, and why it is recorded rather than filed away: a future guard that "verifies
inertness" with an on-device comparison would be **green and blind**. That is this repository's
most-named defect class, found in a new place. Both the reproduction and this extra finding are
written into the edit-once comment beside `MATCHED_GRAD_CLIP`.

The exception cannot matter at this operating point, stated as a magnitude rather than a hope: LoRA
trainable params = 331,776, so at ‖g‖ ≈ 2 the RMS per-element gradient is `2/sqrt(331776) = 2/576 =
3.472e-3` — about 35 orders of magnitude above the subnormal ceiling.

## What landed

**`scripts/phase23_matched_prereg.py`** (stdlib only: `ast`, `collections`; no torch, no numpy,
zero `Assert` nodes — all three checked by AST walk, not grep, because the docstrings discuss both
words):

- **(a) Artifact register** — `MATCHED_CONTROL_RECORD`, `MATCHED_VERDICT_RECORD`,
  `MATCHED_ARTIFACT_GLOB`, `MATCHED_ARM_PREFIX`, `matched_arm(seed)` (refuses non-int / bool).
- **(b) `MATCHED_GRAD_CLIP = 1e6`** with the measured, exception-bounded inertness claim above. The
  unqualified phrase "arithmetically inert" is deliberately **not** written.
- **(c)-(f)** `DP_FN_BRANCH_COUNTS` (a `Counter`, so a pure reorder in `loop.py` does not redden but
  a new/removed branch does), seven `DP_FN_BRANCH_DISPOSITIONS` over a closed disposition set,
  `dp_fn_branch_census`, `prove_branch_ledger_complete` (+ non-empty meta-guard).
- **(g)** `DP_TRAIN_KEYS`, `DP_KWARGS_KEYS`, `dp_wiring_key_census`, `prove_dp_wiring_keys`.
- **(h)** `MATCHED_EQUALISED` (lot volume 8.125× / teaching weight 2.30× / grad_clip) and
  `MATCHED_DIFFERENCES` — including the two end-of-run `masked_perplexity` sweeps that do **not**
  run for a comparator calling `tp.train` directly, so six diagnostic fields are declared ABSENT
  ahead of time rather than read later as a truncated run.
- **(i)** `prove_first_attempt`, four scope clauses, none softened.
- **(j)** `SIGMA_ZERO_VISIBILITY_DISCLOSURE`, the full 14-name `VERDICT_REQUIRED_KEYS`, and both
  record refusals.
- **(k)** `TRAIN_CALL_KEYS` + `prove_train_call_keys` — the third leg, covering the 15 keywords
  neither other census can see.
- **(l)** A `__main__` self-check printing **7 numbered watched refusals**, all against constructed
  inputs labelled SYNTHETIC.

**`tests/test_phase23_matched_prereg.py`** — 12 tests: the ancestry guard (`_ordering_guard`
**imported and called**, never copied), three censuses against live source, and seven refusals
watched RED.

## The one-attempt rule, stated at its true strength

The plan is emphatic that this claim has already been overstated twice, so the wording itself is
the deliverable. `prove_first_attempt`'s message carries **four** clauses, and test 9 asserts each
by name — including **both halves** of clause (3), because an auditability claim without its start
point is the same overclaim in new clothes, and a test checking three clauses passes against a
message naming three of four:

1. Binds **across commits only** — not inside the uncommitted window (`.gitignore:17` / `:14`).
2. In that window, 23-17's `prior_scored_seeds_at_start` covers only half the escape. A delete that
   **also** removes the state file's `matched` section is **PREVENTED BY NOTHING** — indistinguishable
   from a first attempt at run time.
3. That case is **NOT PREVENTED, BUT AUDITABLE AFTER THE FACT** — *and* tracking is **NOT
   RETROACTIVE**, so auditability begins only **at** 23-17's same-session commit. That commit is a
   **DISCIPLINE, NOT A MECHANISM**.
4. Scoped to **one glob** — a `results/phase23_rematch_*` rename is **VISIBLE, NOT REFUSED**.

Test 9 additionally asserts the message never calls the residual "closed".

## Deviations from Plan

### 1. [Rule 3 - Blocking] `tests/test_phase23_resume.py`'s call-site register reddened

- **Found during:** Task 2, full-suite run.
- **Issue:** `test_resume_from_none_is_inert` greps `scripts/` and `tests/` for the literal
  `train_arm(` and asserts the hit count equals its register. My two new files contain three such
  hits — `def train_arm(is_dp):` lines inside **synthetic Python source strings** that
  `prove_train_call_keys` parses with `ast`. The census matches on `FunctionDef.name == "train_arm"`,
  so its fixtures *must* carry that name. Grep counted them as call sites: 20 hits vs 17 registered.
- **Fix:** added three register entries under a new `fixture` kind. The guard's teeth are unmoved —
  its per-file AST check counts `ast.Call` nodes named `train_arm`, and both new files contain
  **zero** (the text lives in a `Constant`), so `expected_calls == 0 == found` for both, and
  `_RESUME_PASSERS.get(path, 0) == 0` holds. The `8+1+1` call-count tripwire only counts
  `kind == "call"` and is untouched.
- **Rejected alternative:** writing `train_arm (` (valid Python, dodges the grep). That is evading a
  guard rather than fixing one, would leave the register's count wrong in the other direction, and
  would baffle the next reader.
- **Files modified:** `tests/test_phase23_resume.py`
- **Commit:** `c100388`

### 2. [Rule 1 - Bug] My own register comment was itself a grep hit

- **Found during:** the fix for deviation 1.
- **Issue:** the explanatory comment I added contained the literal `def train_arm(...)`, producing a
  21st hit against a now-20-entry register. This is exactly the recorded "grep criteria measure
  prose" failure mode, reproduced by the fix for it.
- **Fix:** reworded to "driver-named `def` lines". No register inflation.
- **Commit:** `c100388`

### 3. [Rule 1 - Bug] A decorative banner comment reddened `tests/test_phase21_sc5.py`

- **Found during:** Task 2, full-suite run.
- **Issue:** `test_wall_census_is_the_measured_set` censuses sites asserting on `LOCKED + SOFT`
  facts. My banner `# ===== 10-11. THE VISIBILITY DISCLOSURE …` contains `== 10` and was counted as
  a 12th site (12 observed vs 11 expected).
- **Fix:** reworded all six banners in the new test file to `TEST n —` / `TESTS n-m —` form, so no
  decorative comment reads as a numeric assertion. **Not** added to that census's `_NOT_WALL_SITES`
  exclusion list — a false hit produced by my own cosmetic comment should be removed at the source,
  not permanently excused in a shared register.
- **Commit:** `c100388`

### 4. [Plan instruction] Both new files in ONE commit

Task 2 explicitly requires "COMMIT both files in one commit". The three deviation fixes above are in
that same commit, so the suite is green **at** the commit rather than red at an intermediate one.
This is the plan's intent, not a departure from it.

**No authentication gates occurred. No package was installed. No architectural decision was needed.**

## Verification

| Check | Command | Result |
|---|---|---|
| Self-check prints each refusal | `.venv/bin/python scripts/phase23_matched_prereg.py` | exit 0, **7** numbered refusals |
| Branch ledger vs live `loop.py` | `prove_branch_ledger_complete` | Counter sums **7**; dispositions **7** |
| DP wiring vs live `teach_persona.py` | `prove_dp_wiring_keys` | `{grad_accum_steps}` / 6 keys ✓ |
| `train()` call vs live caller | `prove_train_call_keys` | union **21** ✓ |
| `matched_arm(1337)` | — | `matched_control_seed1337` ✓ |
| `VERDICT_REQUIRED_KEYS` | — | **14** names ✓ |
| Zero `Assert` nodes / zero torch-numpy imports | `ast.parse` walk | **0 / 0** ✓ |
| New tests | `pytest tests/test_phase23_matched_prereg.py -q` | **12 passed** |
| **Full suite** | `.venv/bin/python -m pytest -q` | **`1500 passed, 1 skipped`** (83 warnings, 368.46s) |
| Lint | `.venv/bin/ruff check . && .venv/bin/ruff format --check .` | clean, 216 files formatted |
| Matched glob at commit | `git ls-files 'results/phase23_matched_*'` | **empty**, before and after |
| Blind pin unchanged | `git diff --stat c7de5d4 HEAD -- scripts/phase23_prereg.py` | **empty** |
| Frozen files | `git diff --exit-code -- phase23_prereg, mitigation_{gate,accountant,budget}` | **exit 0** |
| No accidental deletions | `git diff --diff-filter=D --name-only HEAD~1 HEAD` | none |

**Full-suite count matches the plan's expectation exactly: `1500 passed, 1 skipped`** = the 1488
baseline + the 12 new tests.

> Note on the baseline: a background baseline run launched at plan start reported
> `1 failed, 1487 passed, 1 skipped`. That failure was `test_phase23_resume.py::test_resume_from_none_is_inert`
> — **caused by this plan's own in-flight file creation racing the background run**, not a
> pre-existing defect. It is deviation 1 above, and it is fixed. The true pre-existing baseline is
> `1488 passed, 1 skipped`, as the plan states.

## Requirements

**NO requirement is ticked, and none is claimed.** This plan makes a valid comparator *possible*,
which is a precondition for CAL-01 / CAL-02 / CAL-05 / CTRL-03, not a delivery of any of them.
`DPSGD-06` remains open — the D-04 halt stands.

## D-04 HALT compliance

Zero noised sweep points ran. `23-11`…`23-14` were not touched. No `results/` artifact was created,
modified or deleted. No training ran. Everything in this plan is stdlib AST analysis and text.

## Known Stubs

None. Every constant, path and rule the four downstream gap plans consume is declared, and every
function is exercised — 7 refusals in the module self-check plus 12 tests, with 7 watched RED.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema at a trust boundary. The
module runs no subprocess (`prove_first_attempt` takes the caller's `git ls-files` result as an
argument precisely so it does not), imports no torch/numpy, and writes nothing.

## Notes for 23-16 … 23-19

- This module is **EDIT-ONCE from 23-17's first matched artifact**. `VERDICT_REQUIRED_KEYS` is
  pinned at 14 names; a key needed later **cannot be added**. Derive from what is here.
- 23-16's preflight is where `TRAIN_CALL_KEYS` **minus `{resume_from, dp_fn}`** is checked.
- 23-17 must write `sigma_zero_was_visible: True` **and** a non-empty
  `sigma_zero_visibility_disclosure` into `results/phase23_matched_control.json`, and must commit
  the state file's `matched` section **in the same session** — that commit is what converts the
  residual in clause (3) from invisible to auditable.
- The comparator trains on `dp_n8`'s existing fact-aligned three-bin corpus and **builds no bins**.
- New AST fixtures naming `train_arm` or comments reading `== 10` will redden
  `tests/test_phase23_resume.py` and `tests/test_phase21_sc5.py` respectively. Both are live
  repository-wide censuses; see deviations 1-3.

## Self-Check: PASSED

- `scripts/phase23_matched_prereg.py` — FOUND
- `tests/test_phase23_matched_prereg.py` — FOUND
- `.planning/phases/23-…/23-15-SUMMARY.md` — FOUND
- Commit `c100388` — FOUND in `git log`
- `git ls-files 'results/phase23_matched_*'` — still empty
- All four frozen pre-registrations — byte-unchanged
