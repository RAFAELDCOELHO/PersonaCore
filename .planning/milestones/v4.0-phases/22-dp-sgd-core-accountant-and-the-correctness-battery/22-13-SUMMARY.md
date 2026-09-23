---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
plan: 13
subsystem: training
tags: [differential-privacy, checkpoint-provenance, resume, refusal, mutation-probe, gap-closure]

# Dependency graph
requires:
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-06's dp_fn= gradient-side seam in training/loop.py and the resume_from block's dp_noise_rng restore — the branch this plan gives its missing else"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-07's _dp_extra() splat across all three save_checkpoint sites — the MEASUREMENT the tolerated direction's reachability argument rests on"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-11's mutation-probe register (real-module mutation, exactly-once target assertion, distinct-RED accounting, sha256-verified restore) — the evidence format M-H follows"
provides:
  - "src/personacore/training/loop.py's refusal on the seamless-resume-of-a-DP-checkpoint direction: dp_fn is None with a present dp_noise_rng slot now raises instead of silently training non-privately"
  - "the THREE (seam, slot) combinations written out in loop.py, including the tolerated direction's reachability argument and the two committed guards that would redden if a future 'symmetry' edit refused it"
  - "tests/test_phase22_dpsgd.py::test_resume_without_the_seam_refuses_a_dp_checkpoint — three legs (refuse / tolerate / stay narrow) in one test"
  - "mutation M-H watched failing over the FULL suite: exactly ONE distinct RED, sha256-identical restore"
affects: [23 DP resume — the moment teach_persona.py gains a resume path (WARNING-2), this refusal is what stands between a killed DP arm and a silently non-private continuation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A checkpoint field's PRESENCE used as provenance, with the provenance argument itself carried by a measurement (all three save sites splat the same closure) rather than by convention"
    - "A tolerated branch documented with the reachability argument that makes it correct AND the node ids of the committed tests that would redden if someone 'fixed' it — the anti-re-litigation record"
    - "A refusal test with a NARROWNESS leg: the case the guard must NOT catch, asserted alongside the case it must, so an over-broad guard cannot pass on the positive leg alone"
    - "Refusal placement asserted, not just refusal existence: the guard fires before any save, so the non-private continuation is never released to disk"

key-files:
  created: []
  modified:
    - src/personacore/training/loop.py
    - tests/test_phase22_dpsgd.py

key-decisions:
  - "22-REVIEW's CR-04 fix was NOT implemented, and that is the plan's own instruction rather than a deviation. CR-04 proposed refusing dp_fn-set-with-slot-absent; 22-VERIFICATION traced the three splat sites and rejected it. Implementing it would have inverted two committed assertions. Both were run by node id after the change and both PASS."
  - "The mutation deletes the `if` AND the `raise`, not the `raise` alone: an `if` with an empty body is a SyntaxError, so raise-only is not a runnable mutation. Deleting the block reproduces the exact pre-22-13 source, which is the honest 'the refusal is not there' state."
  - "M-H's blast radius was measured over the FULL 1303-test suite rather than over tests/test_phase22_dpsgd.py alone. The plan asked only for the module; the full run is what turns 'one distinct RED' from a claim about one file into a claim about the tree, and it simultaneously proves no OTHER test depends on the refusal."
  - "Leg 3 writes a GENUINE non-DP checkpoint via train(dp_fn=None, ...) rather than reusing leg 2's stripped blob. Reusing the stripped blob would prove the guard tolerates a hand-edited file; writing a real one also proves _dp_extra() returns {} without a seam, which is the other half of the provenance argument."
  - "Leg 3 resumes with max_steps_override=2 so a real post-resume step runs. 'Did not raise' with zero steps executed would be weaker evidence than 'trained its step and wrote step==2'."
  - "The refusal reads `.get(...) is not None`, mirroring the restore, rather than `\"dp_noise_rng\" in ckpt`. _dp_extra() writes either nothing or a real tensor, so the two forms agree on every checkpoint this project writes; matching the sibling branch keeps a future reader from inferring a distinction that is not there."

patterns-established:
  - "Anti-re-litigation comment: a tolerated branch that names the review finding it rejects, the measurement that rejected it, and the node ids that would redden if it were 'fixed'"
  - "Three-leg refusal test: positive (refuses), tolerated (does not refuse the sibling case), narrow (does not refuse the ordinary case)"

requirements-completed: []
requirements-contributed: [DPSGD-04, DPSGD-05]

# Metrics
duration: 30min
completed: 2026-08-26
---

# Phase 22 Plan 13: Refuse a Seamless Resume of a DP Checkpoint Summary

`train()` now refuses `dp_fn=None` against a checkpoint carrying `dp_noise_rng` — the direction
that turns a private run non-private in silence — while the opposite direction stays tolerated on
its measured reachability argument, with the two committed guards that pin it named in the code.

## What Shipped

### The refusal (`src/personacore/training/loop.py`)

One new branch in the `resume_from` block, immediately before the existing restore:

```python
if dp_fn is None and ckpt.get("dp_noise_rng") is not None:
    raise ValueError(...)
```

The message carries the whole argument rather than gesturing at it: the slot's **presence is the
provenance** (all three `save_checkpoint` sites splat `**_dp_extra()`, which is empty without a live
seam, so only a DP run writes that key); resuming it seamlessly keeps training the **same
parameters** with no per-record clip and no Gaussian noise while the checkpoint, the CSV curve and
every downstream artifact still read as that private run's continuation; nothing else in the tree
can notice, because `DPSGD` is not *constructed* on this path, so none of D-16's runtime invariants
exist to fire; and the fix is named — pass the `dp_fn=` seam, or resume from a checkpoint a non-DP
run wrote.

### The three-way record above it

All three reachable `(seam, slot)` combinations are now written out. The one that matters for the
future is (2), **slot absent + seam live → seed fresh, deliberately, NOT a refusal**, which carries
its reachability argument (the three splat sites) *and* the node ids of the two committed guards
that would redden if someone refused it, *and* the note that 22-REVIEW's CR-04 proposed exactly
that and 22-VERIFICATION rejected it on measurement. That comment is the thing that stops this being
re-litigated.

### The test (`tests/test_phase22_dpsgd.py`)

`test_resume_without_the_seam_refuses_a_dp_checkpoint`, three legs in one test:

| Leg | `(seam, slot)` | Asserted |
|-----|----------------|----------|
| 1 | `dp_fn=None`, slot **present** | **REFUSES.** Meta-guard asserts `"dp_noise_rng" in blob` FIRST; `pytest.raises(ValueError, match="dp_noise_rng")`; the message is confirmed to be *this* guard (`"dp_fn=None" in str(excinfo.value)`); and `not unreachable.exists()` — the refusal fires before any save, so the non-private continuation is never released to disk. |
| 2 | seam live, slot **absent** | **STILL TOLERATED.** Key deleted, re-saved, resumed with a seam: completes, and the fresh generator state is `torch.equal`-untouched. |
| 3 | `dp_fn=None`, slot **absent** | **NOT CAUGHT.** A genuine `train(dp_fn=None, ...)` checkpoint (asserted to carry no slot — which also proves `_dp_extra()` is empty without a seam) resumed with `dp_fn=None` and `max_steps_override=2`, asserted to have trained its post-resume step (`blob["step"] == 2`). |

Without leg 3, a guard refusing *every* seamless resume would pass leg 1 and break
`test_resume_curve.py`, `test_resume_memmap.py` and `scripts/pretrain_tinystories.py`.

## Evidence

### Mutation M-H — watched failing

**Target:** the new `if dp_fn is None and ckpt.get("dp_noise_rng") is not None:` block.
**What was deleted:** the `if` **and** its `raise` — 15 lines. Stated because the plan allowed
either: deleting the `raise` alone leaves an `if` with an empty body, which is a `SyntaxError` and
therefore not a runnable mutation. Removing the block reproduces the exact pre-22-13 source. The
probe script asserted the target appears **exactly once** and `compile()`d the mutated module before
writing it (the `tests/test_phase22_fakes.py::_mutate` discipline).

```
$ .venv/bin/python .../mutate_MH.py
M-H applied: removed 15 lines (the if + its raise)
```

**RED, verbatim:**

```
        unreachable = tmp_path / "unreachable.pt"
        seamless = _model()
>       with pytest.raises(ValueError, match="dp_noise_rng") as excinfo:
E       Failed: DID NOT RAISE <class 'ValueError'>

tests/test_phase22_dpsgd.py:1120: Failed
=========================== short test summary info ============================
FAILED tests/test_phase22_dpsgd.py::test_resume_without_the_seam_refuses_a_dp_checkpoint
```

**Distinct-RED accounting.** One mutation was applied; it produced **exactly ONE distinct RED**, and
that count is over the **full suite**, not one module:

| Instrument under M-H | Result |
|----------------------|--------|
| `pytest tests/test_phase22_dpsgd.py -q` | `1 failed, 29 passed in 14.41s` |
| `pytest -q` (FULL suite) | `1 failed, 1302 passed, 1 skipped, 83 warnings in 226.82s` |

The only failing node id in either run is
`tests/test_phase22_dpsgd.py::test_resume_without_the_seam_refuses_a_dp_checkpoint`. So the guard
has exactly one detector — stated as one, not rounded up — and no other test in the tree depends on
the refusal existing.

**Restore, proven not asserted:**

```
pre-probe  sha256: 293772eaed524cfa1dd8eb57024a49f30dd99ac79a6e6c82be8165d381f67da5  src/personacore/training/loop.py
post-restore sha256: 293772eaed524cfa1dd8eb57024a49f30dd99ac79a6e6c82be8165d381f67da5  src/personacore/training/loop.py
$ git diff --exit-code -- src/personacore/training/loop.py   # exit 0
```

### The tripwire for the wrong fix — both PASS, by node id

The plan's central hazard was implementing CR-04's inverted fix. The two committed guards that drive
the tolerated direction were run by node id **after** the change:

```
tests/test_phase22_dpsgd.py::test_dp_noise_rng_round_trips_through_a_kill_and_resume PASSED [ 25%]
tests/test_phase22_checkpoint.py::test_resume_epsilon_bit_identical[1.0] PASSED [ 50%]
tests/test_phase22_checkpoint.py::test_resume_epsilon_bit_identical[0.0] PASSED [ 75%]
tests/test_phase22_dpsgd.py::test_resume_without_the_seam_refuses_a_dp_checkpoint PASSED [100%]

============================== 4 passed in 4.43s ===============================
```

Both were also **unmodified** by this plan, and `git show --numstat` proves it rather than my saying
so: `tests/test_phase22_checkpoint.py` appears in neither commit, and
`tests/test_phase22_dpsgd.py`'s only change is `106  0` — 106 insertions, **zero deletions**, so no
existing line of the back-compat leg was touched. (`345461d` is `56 insertions(+), 10 deletions(-)`
in `loop.py` alone; the 10 are the old comment lines the three-way record replaced.)

### Non-regression: the count, with its denominator

| Run | Result |
|-----|--------|
| Baseline this session (pre-change, `tests/test_phase22_dpsgd.py` + `tests/test_phase22_checkpoint.py`) | `41 passed in 15.47s` |
| Same two modules, post-change | `41 passed in 15.32s` |
| **FULL suite, post-change** | **`1303 passed, 1 skipped, 83 warnings in 222.00s`** |

`1303 = 1302 baseline + 1 new test`. **Zero regressions, zero failures.** The prompt's stated
baseline of 1302 passed / 1 skipped was confirmed independently by the M-H run (`1 failed, 1302
passed, 1 skipped` — the 1 failed being the new test with its guard removed).

**Why the reachability claim about the new refusal is safe rather than hopeful.** Of the
`resume_from=` call sites in the tree (`tests/test_lora_training.py`, `tests/test_resume_curve.py`
×4, `tests/test_resume_memmap.py`, `tests/test_phase22_dpsgd.py` ×2 + this plan's 3,
`tests/test_phase22_checkpoint.py` ×2, `scripts/train_adapter_smoke.py`,
`scripts/pretrain_tinystories.py`), **none** resumed with `dp_fn=None` from a slot-carrying
checkpoint before this plan — every non-Phase-22 site passes no `dp_fn` at all and resumes a
checkpoint a non-DP run wrote. That is leg 3's case, and the full-suite green is the executed proof.

### Byte-unchanged and lint

```
$ git diff --exit-code -- src/personacore/lora/ pyproject.toml scripts/mitigation_accountant.py   # exit 0
$ grep -n "CKPT_SCHEMA_VERSION" src/personacore/checkpoint.py
39:    NO format change and NO ``CKPT_SCHEMA_VERSION`` bump. **This is the slot the DP path actually
61:CKPT_SCHEMA_VERSION = 1
127:        "schema_version": CKPT_SCHEMA_VERSION,
$ grep -c "dp_fn is None and ckpt" src/personacore/training/loop.py
1
$ .venv/bin/ruff check . && .venv/bin/ruff format --check .
All checks passed!
203 files already formatted
```

## Deviations from Plan

### 1. [Plan instruction, followed] The review's CR-04 fix was deliberately NOT implemented

Not a deviation from the plan — a deviation from the **review**, and the plan mandated it. Recorded
here because it is the single most consequential thing this plan did *not* do. CR-04 proposed
refusing `dp_fn` set with the slot absent. That direction is driven and asserted-tolerated by two
committed guards, both of which pass unmodified above. The code now records why, so the next reader
does not close the loop the other way round.

### 2. [Strengthened] M-H's blast radius measured over the full suite, not one module

The plan's Task 2 specified `pytest tests/test_phase22_dpsgd.py -q` under the mutation. Both were
run. The full-suite run costs ~227 s and is what makes "one distinct RED" a statement about the
tree; the module-only run alone could not have distinguished "one detector" from "one detector in
this file". Both counts are reported above.

### 3. [Resolved from the code, not the plan] Line numbers in the plan's `read_first` had drifted

The plan cited `loop.py:705-737`, `:870-930`, `:877/:900/:927` and
`tests/test_phase22_checkpoint.py:522-540`. All resolved correctly *before* the edit (the three
splat sites really are at 877/900/927 pre-change, and the checkpoint negative control really does
start at 519). Recorded as a non-finding: this is the first plan in the phase whose cited line
numbers were all accurate. The comment written into `loop.py` nonetheless names the three save sites
**descriptively** ("the best.pt save, the in-loop latest.pt save, and the end-of-call save") rather
than by line number, because the refusal itself shifts them by 46 lines.

### 4. [Withheld] No requirement marked complete

The plan's frontmatter lists `requirements: [DPSGD-04, DPSGD-05]`. Both are **already** `[x]
SATISFIED` in `REQUIREMENTS.md` — DPSGD-04 at plan 22-11, DPSGD-05 at plan 22-07 — so
`requirements.mark-complete` was not called: it would either no-op or rewrite two large, accurate
traceability rows for no gain. This plan **contributes** to both (`requirements-contributed` in the
frontmatter records it) and completes neither. This is the phase's own recorded
over-claim-avoidance discipline, applied again.

## Deferred Issues

None from this plan. Two pre-existing warnings from `22-VERIFICATION.md` remain open and are **not**
closed by this work:

- **WARNING-2** — DP kill→resume still has no production driver; `teach_persona.py::train_arm`
  never passes `resume_from` and its `refuse_if_exists` blocks re-running a killed DP arm. The
  refusal shipped here is the guard that becomes load-bearing the moment that driver exists.
- **WARNING-3** — no production consumer of the accountant. Untouched by this plan.

`deferred-items.md` was not appended to: nothing out-of-scope was discovered.

## Known Stubs

None. Both files ship working code with executed evidence.

## Threat Flags

None. This plan added a refusal at an existing trust boundary and introduced no new network
endpoint, auth path, file-access pattern or schema change. `CKPT_SCHEMA_VERSION` is unchanged and
`_dp_extra()`, the save sites and the checkpoint format were not touched.

## Threat Register Disposition

| Threat ID | Disposition | Where it landed |
|-----------|-------------|-----------------|
| T-22-24 (a DP checkpoint continued by a non-DP run) | **mitigated** | The `ValueError` in `loop.py`'s resume block; pinned by leg 1 and watched reddening under M-H. |
| T-22-25 (a future "symmetry" edit refusing the tolerated direction) | **mitigated** | The three-way comment names the splat measurement, the CR-04 rejection and both node ids; leg 2 asserts the tolerated case at run time. |
| T-22-26 (an over-broad refusal blocking every seamless resume) | **mitigated** | Leg 3 resumes an ordinary non-DP checkpoint with `dp_fn=None` and asserts it trained its post-resume step; the full-suite green over 11 other `resume_from=` sites is the corroboration. |
| T-22-SC (package installs) | **accepted** | No installs; `pyproject.toml` byte-unchanged (`git diff --exit-code`, exit 0). |

## Commits

| Commit | Type | What |
|--------|------|------|
| `345461d` | `fix` | The refusal + the three-way `(seam, slot)` record in `loop.py` |
| `2de419e` | `test` | `test_resume_without_the_seam_refuses_a_dp_checkpoint` — three legs |

## Tooling Hazards Hit

Recorded because this phase has hit `gsd-sdk` frontmatter corruption in every prior session, and
this is the **sixth in a row**. The SUMMARY was written **before** any `roadmap.update-plan-progress`
call, per the plan's environment note, and `git diff .planning/` was inspected after **every**
handler call.

| Handler | Form used | Result |
|---------|-----------|--------|
| `state.advance-plan` | positional (takes none) | **CORRUPTED the body.** Frontmatter was clean this time (`completed_plans` 40→41), but it flattened the Current Position `Status:` line to `Ready to execute`, destroying the gap-closure prose, and left the `(12/16)` counter in the `Phase:` line stale. Both hand-repaired. |
| `state.update-progress` | positional (takes none) | **Silent no-op** — `{"updated": false, "reason": "Progress field not found in STATE.md"}` against a frontmatter that plainly has a `progress:` block. Same failure as 22-12. `percent: 22` is correct as-is (phase-based, 2/9) so nothing needed repair. |
| `state.record-metric` | `--flag` | Clean. `\| Phase 22 P13 \| 30min \| 2 tasks \| 2 files \|`. |
| `state.add-decision` | `--flag` | **CORRUPTED.** Wrote `- [Phase ?]:` — wrong phase number *and* a stray colon where the house style is `- [Phase 22] `. Hand-repaired; the two remaining decisions were written by hand rather than risking a second corruption. |
| `state.record-session` | `--flag` | Clean. |
| `roadmap.update-plan-progress` | `--flag` | **CORRUPTED.** Emitted `\| In Progress\|  \|` — lost the cell's trailing space and **blanked the date**. Identical to 22-12. Hand-repaired to `\| In Progress \| 2026-08-26 \|`. |

Also confirmed still true: `make test` is broken (bare `pytest` resolves to the pyenv 3.12.13, no
torch). Every run in this SUMMARY used `.venv/bin/python -m pytest` (Python 3.11.15). The
`git commit -F -` heredoc form was used for both commits — no `-m` with backticks, per 22-12's
zsh-expansion incident.

## Self-Check: PASSED

| Claim | Verification | Result |
|-------|--------------|--------|
| `22-13-SUMMARY.md` exists | `[ -f ... ]` | FOUND |
| `src/personacore/training/loop.py` exists | `[ -f ... ]` | FOUND |
| `tests/test_phase22_dpsgd.py` exists | `[ -f ... ]` | FOUND |
| commit `345461d` exists | `git log --oneline --all \| grep -q` | FOUND |
| commit `2de419e` exists | `git log --oneline --all \| grep -q` | FOUND |
| `2de419e` has zero deletions in the test file | `git show --numstat --format= 2de419e` → `106  0` | CONFIRMED |
| `345461d` touches only `loop.py` | `git show --stat` → `1 file changed, 56 insertions(+), 10 deletions(-)` | CONFIRMED |
| loop.py restored byte-identically after M-H | sha256 equal + `git diff --exit-code` exit 0 | CONFIRMED |

Two quotes in this SUMMARY were corrected during the self-check before it was committed, because a
verbatim quote that is not verbatim is exactly the defect this phase's evidence discipline exists to
catch: pytest's banner is `short test summary info`, not `...item`; and the `grep -n
CKPT_SCHEMA_VERSION` block originally carried a trailing annotation I had written, which would have
read as text present in `checkpoint.py`. Both now reproduce the tools' actual output.
