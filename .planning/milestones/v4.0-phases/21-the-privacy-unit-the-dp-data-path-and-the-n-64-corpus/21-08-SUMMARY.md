---
phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
plan: 08
subsystem: replay-volume
tags: [unit-04, d-11, d-24, d-25, d-09, d-10, side-channel, differential, wave-3, t-21-01, t-21-09, t-21-35, t-21-36, t-21-37, t-21-15]
requires:
  - "21-04 — the aligned branch and its replay_ratio refusal, which this plan must not defeat"
provides:
  - "scripts/teach_persona.py::REPLAY_WINDOWS_PER_FACT = 4 and replay_window_budget(n_facts, block_size) — THE ONLY SITE computing the v4.0 replay volume"
  - "scripts/teach_persona.py::_prepend_replay(..., n_facts=None) — the additive kwarg; None keeps the legacy v3.0 side channel ALIVE as the negative control"
  - "src/personacore/training/loop.py::train(replay_bin, replay_mask_bin, replay_windows) — the additive replay seam, drawn in its OWN pass per lot"
  - "src/personacore/training/loop.py::_optimizer_step(..., replay_fn=None) — the injection point, after the accumulation loop and before unscale_"
  - "tests/test_phase21_replay_volume.py — the differential, its negative control, the non-vacuity direction, and the seam's identity pair"
affects:
  - "21-11 — the replay-in-bin @1.0 row exercises the LEGACY path (n_facts=None); the v4.0 rows call replay_window_budget"
  - "Phase 22 (DPSGD-01/04) — the replay pass is structurally outside the per-record loop, so the clipping seam has a place to NOT apply"
tech-stack:
  added: []
  patterns:
    - "A side-channel claim is proven by a DIFFERENTIAL in BOTH directions, never by a constant assertion — insensitive-to-everything is vacuous, so the public quantity must be varied too"
    - "The defective legacy branch is RETAINED and ASSERTED PRESENT by a passing negative-control test; an open defect that a test watches is a different artifact from one tolerated in silence"
    - "The public/private classification is enumerated per-quantity and justified by DERIVATION rather than publication, with the ambiguous row reported rather than resolved to the convenient reading"
    - "Restore-by-checkout only AFTER the GREEN commit, verified by a sha256 recorded BEFORE the mutation"
key-files:
  created:
    - "tests/test_phase21_replay_volume.py"
    - ".planning/phases/21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus/21-08-SUMMARY.md"
  modified:
    - "scripts/teach_persona.py"
    - "src/personacore/training/loop.py"
decisions:
  - "No build_bins replay_n_facts pass-through, per the plan's own refusal — and it is also what keeps 21-04's aligned-branch replay_ratio refusal untouched. The two guards live on branches that cannot both execute, verified by diff hunk"
  - "The v4.0 branch does NOT raise on a non-default replay_ratio. A raise would be self-defeating: the differential runs the SAME call one kwarg apart, and that shared call shape is the only thing making the verdict a property of the BRANCH rather than of two fixtures"
  - "Replay micro-batches are weighted by ACTUAL windows / replay_windows, not 1/n_micro_batches. With a ragged tail (4+4+2) the naive divisor over-weights the 2-window batch by 1.67x"
  - "replay_ratio's public/private classification is reported AMBIGUOUS, not resolved. Published constant, but derived from replay_required(4.5737, 14.8559) measured on the real corpus. The v4.0 volume ignores it entirely, so it need not be settled here"
metrics:
  duration: "~40 min"
  tasks_completed: 3
---

# Phase 21 Plan 08: The D-11 Side Channel, Closed by Differential Summary

`replay_window_budget(n_facts)` is the single site computing the v4.0 replay volume, and its
independence from private data is proven by a differential with a live negative control — not by
a constant assertion, which passes on the defective implementation.

## The Central Claim, Proven in Both Directions

The prompt named this the thing most likely to be quietly wrong: *"a test that computes the
volume from public inputs and checks it matches proves nothing — of course it matches, you wrote
both sides."* So the evidence is a differential, and it is run in **both** directions plus a
control.

Two synthetic 8-fact corpora. Ids, slots, tiers, the family set and the register are held
**byte-identical**; only the private `value` strings differ. Measured:

| corpus | episodes (PUBLIC) | `teaching_tokens` (PRIVATE) | v4.0 `replay_tokens` | legacy `replay_tokens` |
|---|---|---|---|---|
| short | 176 | 6,766 | **8,192** | 6,766 |
| long  | 176 | 9,206 | **8,192** | 9,206 |

- **Insensitivity** — the v4.0 volume is identical at 8,192 across a **2,440-token** private
  spread. The two calls were handed genuinely different `teaching_tokens`, asserted first.
- **Negative control** — the SAME call **one kwarg apart** (`n_facts=None`, same
  `replay_ratio=1.0`) differs by exactly that **2,440 tokens**. The differential provably CAN
  see a side channel; it is not merely blind.
- **Non-vacuity** — varying the PUBLIC `n_facts` from 8 to 16 moves the volume 8,192 -> 16,384.
  Without this, a function returning a constant for every input passes the insensitivity
  direction while proving nothing about the mechanism.

**8,192 sits BETWEEN the two corpora's teaching totals (6,766 and 9,206).** That is the concrete
reason a bare `== 8192` assertion is not the evidence: on a corpus that happened to total 8,192
tokens the defective implementation would pass it (RESEARCH Pitfall 8).

## The Public/Private Classification, Enumerated

Naming which quantities are public is half the claim; a differential that varies the wrong thing
is green and blind. Each row is justified by **derivation**, not publication — D-24's whole point
is that "public because we published it" is not enough.

| Quantity | Class | Justification |
|---|---|---|
| `n_facts` | PUBLIC | D-11 names it. A COUNT of records, not a function of their content; SC2 pre-registers `grad_accum_steps = n_facts` publicly at both capacities |
| `REPLAY_WINDOWS_PER_FACT = 4` | PUBLIC | D-24. Chosen from the {3,4,5}-window table, all small integers authored before any fact existed |
| `block_size = 256` | PUBLIC | D-24. `ModelConfig.block_size`, fixed before the fact set existed |
| episode count (176) | PUBLIC | the facts x families x instances cross product; held fixed and **asserted** across both arms, so it cannot be the source of any delta |
| each fact's `value` | PRIVATE | the invented persona secret — literally what the DP unit protects, and the quantity varied |
| `teaching_tokens` | PRIVATE | D-11: the sum of the FACTS' OWN token lengths, "varying with the fact values". Private BY DERIVATION even though nothing hides it |
| per-fact token lengths / `windows_per_fact` | PRIVATE | same reason |

**One row is genuinely ambiguous and is reported rather than resolved to the convenient
reading.** `replay_ratio` is published as a committed constant (`REPLAY_ARM_RATIO = 1.0`), so
public by publication — but it was DERIVED from `replay_required(4.5737, 14.8559)`, a measurement
taken on the REAL corpus. Under D-24's own strictest test ("public by publication, private by
derivation") its classification is not clean. **The v4.0 branch does not need it settled**,
because the volume ignores `replay_ratio` entirely. Had the design used it even as a cap, this
ambiguity would have to be resolved before the D-11 claim could be made at all.

## The Deliberate-RED

Mutation: the v4.0 branch pointed at `int(round(replay_ratio * teaching_tokens))`.

```
E  AssertionError: replay volume moved with the private fact values: 6,766 (short corpus,
   6,766 teaching tokens) vs 9,206 (long corpus, 9,206). D-11 requires the volume to depend
   on PUBLIC quantities only ...
E  assert 6766 == 9206
1 failed, 4 passed
```

`test_side_channel_closed` reddened on the insensitivity assertion; `test_side_channel_negative_control`
**stayed GREEN**, which is the point of having it. **The plan's predicted RED count was CORRECT
this time** — exactly 1 failure, negative control green, as written. Recorded because this phase
has measured the opposite twice (21-04 predicted 2 and got 3; 21-05 predicted 2 and got 3).

Restore sha256 `337cc8c294d3860fa799aa0e9d608699e3edf642c5622d1fe274b528ad9248c2`, equal to the
value recorded BEFORE the mutation; `git diff --exit-code scripts/teach_persona.py` returns 0.
**The mutation was performed AFTER the GREEN commit** (carry-forward #4), so `git checkout` had a
committed state to restore to and nothing was lost — the failure mode that destroyed work in
21-01 and 21-04.

## The Seam: Exactly the Public Budget, and Not Vacuous

`train()` gained `replay_bin` / `replay_mask_bin` / `replay_windows`, all keyword-only, all
defaulting to `None`. `_optimizer_step` gained `replay_fn=None`, invoked **after** the
per-micro-step accumulation loop and **before** `scaler.unscale_` — structurally outside the
per-record loop (D-25).

| Claim | Evidence |
|---|---|
| bit-identical when off | `test_replay_seam_off_is_bit_identical` (unconditional, never skips) |
| **and not merely accepted-and-discarded** | `test_replay_seam_on_changes_the_trajectory` — the fingerprints DIFFER |
| draws exactly the public budget | counted `[4, 4, 2]` per optimizer step at `replay_windows=10`, `batch_size=4` — **10 windows, 3 steps, 30 total** |
| partial wiring refused by name | 5-case parametrization over the three kwargs |

`replay_windows=10` is deliberately **not** a multiple of `batch_size=4`, so a ceil-division
overdraw (which would draw 12) cannot hide behind a clean division.

**An unprompted correctness fix in the weighting.** Each replay micro-batch is weighted by its
ACTUAL window count over `replay_windows`, not by `1/n_micro_batches`. With the ragged `4+4+2`
tail the naive divisor would over-weight the 2-window batch by **1.67x**, making the replay term
a function of how the budget happened to split rather than a mean over its windows.

**Independent bit-identity evidence:** `tests/test_loop_penalty_fn.py::test_golden_trajectory_bit_identity`
is platform-gated and **PASSED rather than skipped** on this box — so the v1.0 trajectory replay
(exact CSV text, exact final-loss repr, exact param sha256) actively certified that the off-path
bits survived the `loop.py` edit. That was not guaranteed to be available.

## 21-04's Refusal Was Not Defeated

21-04 added a `SystemExit` when `replay_ratio` is passed alongside `align_facts`
(`scripts/teach_persona.py:466`, inside `_refuse_ambiguous_aligned_input`). It guards the
**aligned** branch, which raises before `_prepend_replay` is ever reached; `_prepend_replay` is
called only from the flat branch's `if replay_ratio > 0` guard. The two cannot both execute.

The thing that WOULD have collided is a `build_bins(..., replay_n_facts=)` pass-through — and the
plan refuses one, on the independent grounds that it would have no caller and therefore no
non-vacuity pair (`21-VALIDATION.md:138`). **Verified mechanically:** no diff hunk in this plan
reaches `_refuse_ambiguous_aligned_input`; hunk starts are `133, 555, 559, 560, 566, 572`.

The v4.0 branch deliberately does **not** raise on a non-default `replay_ratio`, and this is not
a quiet loosening of 21-04's posture. A raise there would be self-defeating: the differential
runs the SAME call one kwarg apart (`replay_ratio=1.0, n_facts=8` vs `replay_ratio=1.0,
n_facts=None`), and that shared call shape is the only thing making the two verdicts a property
of the BRANCH rather than of two different fixtures. Instead the precedence is made LOUD — both
ignored inputs are named in the function's own short-slice reporting.

## Plan vs Code Fidelity

**EVERY line anchor in this plan's `<interfaces>` block was stale.** The plan warned this would
happen once wave 2 landed and instructed locating by symbol; that instruction was correct and
necessary. Measured:

| Symbol | Plan says | Actual |
|---|---|---|
| `_prepend_replay` | `:327-348` | **`:555`** |
| the side-channel `want =` line | `:338` | **`:566`** |
| `BLOCK_SIZE` | `:100` | `:103` |
| `REPLAY_RATIO` | `:128` | `:131` |
| `REPLAY_ARM_RATIO` | `:129` | `:132` |
| `REAL_RUN_REPLAY_RATIO` | `:151` | `:154` |
| `_prepend_replay` short-slice raise | `:341-345` | `:676-679` |
| `arm_spec` | `:405-421` | `:633-651` |
| `build_bins`'s `_prepend_replay` call | `:274-275` | `:299-300` |

`loop.py`'s anchors (`:160-169`, `:172-201`, `:165`) held, exactly as the plan predicted — wave 2
did not touch that file.

Three further findings, reported rather than silently adapted:

**1. The task-3 criterion "shows ONLY added lines plus the three new parameters — no existing
line reordered" is not literally achievable, and the reason is benign.** Measured: **113 added,
2 removed**. Both removed lines are `_optimizer_step`'s signature and its call site, **reflowed**
one-argument-per-line by `ruff format` because adding a 9th parameter pushed them past the line
limit. Parameter ORDER is preserved and both new parameters are appended last. Reflowed, not
reordered — but the criterion as written would read as violated by a diff-line count.

**2. The plan's honest-limit instruction about 21-02's golden fixture is CORRECT, and verified
rather than repeated.** `tests/fixtures/golden_build_bins_v2.json` carries
`meta.recipe = "... build_bins(..., replay_ratio=0.0)"` and `stats_repr` containing
`'replay_tokens': 0, 'replay_ratio': 0.0`. Because `build_bins` guards the call with
`if replay_ratio > 0`, **`_prepend_replay` is never entered at all** — so the fixture covers
NEITHER of its branches. It is not weak coverage of the legacy branch; it is zero coverage of
both. The differential in this plan is the only instrument pointed at that function.

**3. `_prepend_replay`'s `n_facts` validation rejects `bool` explicitly.** `bool` subclasses
`int` in Python, so `n_facts=True` would otherwise pass `isinstance(n_facts, int) and n_facts > 0`
and silently size replay at `4 * 1 * 256 = 1,024`. Same guard added to `replay_windows` in
`train()`. Not named by the plan; it is the difference between "a positive int" as written and as
enforced.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Replay micro-batches weighted by actual window count, not by micro-batch count**

- **Found during:** Task 3
- **Issue:** The plan says "accumulate its scaled loss into the same gradient buffer, in its OWN
  loop" without naming the divisor. A `1/n_micro_batches` divisor is the obvious reading and is
  wrong under ceil division: at `replay_windows=10, batch_size=4` the split is `4+4+2`, so the
  2-window micro-batch would carry 1/3 of the replay gradient instead of 2/10 — over-weighted by
  **1.67x**.
- **Why it matters here specifically:** it would make the replay term a function of how the
  public budget happened to split against the batch size, which is a (public) dependency the
  plan does not intend and which changes with `batch_size` rather than with `n_facts`.
- **Fix:** weight each micro-batch by `micro / replay_windows`. Exact for any split.
- **Files modified:** `src/personacore/training/loop.py`
- **Commit:** `8dba440`

**2. [Rule 2 — Missing critical functionality] `bool` rejected explicitly in both int validations**

- **Found during:** Tasks 1 and 3
- **Issue:** `isinstance(True, int)` is `True`, so `n_facts=True` / `replay_windows=True` would
  pass a plain positive-int check and silently size replay at one fact's worth.
- **Fix:** `isinstance(x, bool)` short-circuits both guards.
- **Commits:** `eb61396`, `8dba440`

**3. [Rule 2 — Missing critical functionality] A 5-case wiring-refusal parametrization**

- **Found during:** Task 3
- **Issue:** The plan specifies the validation but lists no test for it, so a silently-no-op
  partial wiring (e.g. `replay_bin` set, `replay_windows` omitted) would be untested.
- **Fix:** `test_replay_seam_refuses_partial_or_malformed_wiring`, 5 cases, each asserting the
  message NAMES the offending kwarg.
- **Commit:** `8dba440`

## Verification

| Check | Result |
|---|---|
| `pytest -q tests/test_phase21_replay_volume.py` | **13 passed** |
| Scoped set (replay_volume, loop_penalty_fn, phase14_teaching, masked_batch, aligned_bins, unit_pin, train_loop, package) | **93 passed, 1 skipped** |
| The 1 skip | `test_train_loop.py:81` — "fp16 AMP smoke needs a CUDA GPU". Pre-existing, platform-gated, unrelated |
| `21-VALIDATION.md:76` `-k side_channel_closed` | selects and passes |
| `21-VALIDATION.md:77` `-k window_quantized` | selects and passes (2 params) |
| `git status --porcelain data/` | empty — no test wrote into recorded evidence |
| `git ls-files 'results/phase21_*'` | empty |
| `git diff --exit-code` on 3 frozen pins | 0 — `mitigation_gate.py`, `mitigation_unit.py`, `phase18_extraction.py` byte-unchanged |
| `scripts/mitigation_unit.py` sha256 | `45f37e152bb4035667b804c1463431b3f12fa5096c47de32b1dc27abbe000473` — matches the 21-01 pin |
| `ruff check . && ruff format --check .` | All checks passed, 182 files formatted |
| `.planning/STATE.md` / `ROADMAP.md` | byte-unchanged (worktree mode) |

**No bare `pytest -q` was run.** 21-06 and 21-07 hold live deliberate-RED canaries in sibling
worktrees during wave 3, and this plan's own RED reddened
`tests/test_phase21_replay_volume.py`, which their runs would have collected. Every run above was
scoped to an explicit file list. The full suite is a **wave-close** gate
(`21-VALIDATION.md:47,52`), not a plan-close one.

## Known Stubs

None. Every function this plan adds is fully implemented and exercised: `replay_window_budget`
against both capacities, both `_prepend_replay` branches against real 8-fact corpora, and the
`train()` seam against a running optimizer with its draw count observed.

## Threat Flags

None. This plan adds no network endpoint, no auth path and no new file-access pattern. The
replay seam reads two caller-supplied `.bin` paths through `get_batch_memmap_masked`, the same
already-validated function the mask seam already used, and every test drives synthetic bins under
`tmp_path` (T-21-15).

## Commits

| Commit | Task | Content |
|---|---|---|
| `eb61396` | 1 | `REPLAY_WINDOWS_PER_FACT`, `replay_window_budget`, `_prepend_replay(..., n_facts=None)` |
| `f756474` | 2 | the differential, the negative control, the non-vacuity direction, the 947.625 refusal |
| `8dba440` | 3 | `train()`'s replay seam, `_optimizer_step(..., replay_fn)`, the seam's 4 tests + 5-case wiring parametrization |

## Self-Check: PASSED

All three claimed source files exist on disk (`scripts/teach_persona.py`,
`src/personacore/training/loop.py`, `tests/test_phase21_replay_volume.py`); all three commits
present in `git log ae5eb18..HEAD`; working tree clean before this SUMMARY; `.planning/STATE.md`
and `.planning/ROADMAP.md` untouched as required in worktree mode.
