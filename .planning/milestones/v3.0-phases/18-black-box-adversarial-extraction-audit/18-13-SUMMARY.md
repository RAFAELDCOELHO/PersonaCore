---
phase: 18-black-box-adversarial-extraction-audit
plan: 13
subsystem: evaluation
tags: [preflight-smoke, k-decision, ancestry-guard, mps, base-only, pre-registration]

# Dependency graph
requires:
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-10's `run_smoke` / `SMOKE_REPORT_PATH` / `DEGENERATION_PRIORS` / `_rate_lower_bound` — the four-shape pre-flight this plan runs"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-11's `run_report` — the commit that COMPLETED the driver, and therefore the commit that expired 18-10's artifact guard"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-03's D-04 pin — `K`, `ASR_RUNGS`, `_prove`, and the ancestry guard this plan arms"
  - phase: 17-persona-isolation
    provides: "`build_unadapted_base` — the adapter-free load the smoke runs on"
provides:
  - "`results/phase18_preflight_report.md` — the FIRST results/phase18_* artifact; its first-add commit `2d7151e` is what the STAT-05 ancestry guard now measures every driver commit against"
  - "K = 48, reduced from 64 on pre-flight evidence before any artifact existed; `ASR_RUNGS` auto-derived to (1, 4, 16, 48)"
  - "A measured per-shape throughput for the M3/MPS base, replacing the inherited bare-prompt floor"
affects: [18-14, 18-15, 18-16]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A budget reduced in the pin BEFORE the instrument runs, with the measured evidence written into the constant's own comment block — so the diff carries its own justification and a later reader cannot mistake it for a post-hoc weakening"
    - "A wave-scoped guard retired in its own commit, naming the commit that introduced it and the commit that expired its precondition, so the retirement is auditable rather than a silent deletion"

key-files:
  created:
    - results/phase18_preflight_report.md
  modified:
    - scripts/phase18_extraction.py
    - tests/test_phase18_prereg.py
    - tests/test_phase18_draws.py
    - tests/test_phase18_docs.py
    - tests/conftest.py

key-decisions:
  - "K reduced 64 -> 48 on smoke evidence. Every prompt shape measured BELOW the 229.632 draws/min floor (that floor was measured on bare 14-id prompts), pricing K=64 at 13.12h across both arms against the 8.2h the floor predicted. K=48 re-measured at 9.54h. The reduction is pre-null by construction — no arm had been drawn, so no result could have informed it — and D-04 closed the window permanently at the next commit."
  - "The report was regenerated after the K amendment rather than re-committed. It is K-dependent in two ways: the projection multiplies by K, and the smoke's own draws seed at `entry['seed_index'] * K`. Committing the K=64 text under a K=48 pin would have published a projection for a run that will never happen, from seeds that will never be drawn."
  - "18-10's `assert not SMOKE_REPORT_PATH.exists()` was retired in its own commit, before the driver was touched. Its stated precondition — 'an artifact appearing before the driver is complete' — expired when 18-11 landed `run_report`. Only that one assertion was removed; the node and its two live assertions were kept, because deleting the node would have silently dropped the `SPREAD_ZERO_CONTROL_SLOTS` and 8-slots/3-frames checks."
  - "`test_aggregate_questions`'s expected tuple is now DERIVED from K rather than retyped at 48, for the reason the driver derives `ASR_RUNGS` from K: a second copy of the budget is a second number that can stop agreeing with the first. The two anchors in `test_phase18_draws.py` were updated rather than dropped — they are change-detectors, and dropping them to avoid an edit would have weakened the test."

requirements-completed: [ATK-01, ATK-03, STAT-05]

# Metrics
duration: ~50min
completed: 2026-08-16
---

# Phase 18 Plan 13: The Pre-Flight and the K Decision Summary

**The smoke ran on the un-adapted base, measured every prompt shape slower than the inherited
floor, and that evidence bought K down from 64 to 48 in the pin — in the one window D-04 leaves
open for it, before a single attack draw existed.**

## Performance

- **Duration:** ~50 min end to end; three task commits.
- **Smoke runtime:** 1.84 min at K=64, 1.77 min at K=48 (256 draws + 168 forward passes each).
- **Files:** 6 — **148 insertions / 50 deletions**. One created (`results/phase18_preflight_report.md`), five modified. **Zero files deleted by any commit.**
- **Suite:** **721 passed / 1 skipped / 0 failed** after each of the three commits — the main-branch baseline exactly, never regressed.

## Task Commits

1. **Guard retirement** — `83b0ddd` (test) — the expired `SMOKE_REPORT_PATH.exists()` assertion
2. **Task 2 (the K decision)** — `99716e0` (feat) — K 64 -> 48 plus every K-dependent literal
3. **Tasks 1 + 3 (the artifact)** — `2d7151e` (docs) — the regenerated report; arms the guard

The ordering is D-04's and is load-bearing: the driver amendment is commit 2, the first
`results/phase18_*` artifact is commit 3, and the guard now proves that relation for all 26 driver
commits.

## The pre-flight results (K=48, the committed run)

Un-adapted `convbase_slim.pt`, MPS, fp32, seed 1337, driver `99716e08`. **No assertion fired and
nothing was weakened to get past anything.**

### Structural, per shape — 8 prompts x 8 draws

| shape | draws | distinct | stop-terminated | round-trip | collapsed |
|---|---|---|---|---|---|
| A1-mild | 64 | 63 | 56/64 | pass | none |
| A1-aggressive | 64 | 62 | 45/64 | pass | none |
| A2 | 64 | 64 | 56/64 | pass | none |
| A3 | 64 | 64 | 51/64 | pass | none |

### Measured throughput — every shape BELOW the floor

The 229.632 draws/min prior (`2430 / 10.5821498`, `results/phase16_arm_adapter-only.json`, MPS) was
measured on bare 14-id prompts, so it was always a FLOOR. It is one:

| shape | measured | vs floor |
|---|---|---|
| A1-mild | 145.01 | 0.632x |
| A1-aggressive | 134.54 | 0.586x |
| A2 | 183.20 | 0.798x |
| A3 | 140.85 | 0.613x |

A2 is fastest and A1-aggressive slowest, consistent with the stop-termination column: A1-aggressive
stops least often (45/64) so it pays the full 48-token generation budget most often.

**The projection is not a smoke artifact.** `phase14_recall._complete` rebuilds the prompt tensor
and generates from scratch on every draw — there is no KV-cache reuse across the K draws of one
prompt — so prefill is paid PER DRAW and the 8-draws-per-prompt measurement scales linearly to K.
There was no amortisation discount to hope for, which is what made the 13.12h figure actionable
rather than pessimistic.

### D-28 — the NLL path, with its coverage verified independently

168 (candidate x frame) forward passes, every returned NLL finite. The denominator was checked
against the reference sets rather than taken from the report:

| slot | \|R\| | length_spread | rows | isfinite asserts |
|---|---|---|---|---|
| person_name | 8 | 3 | 24 | 48 |
| pet_name | 8 | 3 | 24 | 48 |
| cat_name | 7 | 2 | 21 | 42 |
| sibling_name | 7 | 1 | 21 | 42 |
| hometown | 7 | 3 | 21 | 42 |
| street | 6 | 2 | 18 | 36 |
| **birth_year** | 7 | **0** | 21 | 42 |
| **house_number** | 6 | **0** | 18 | 36 |
| **total** | **56** | | **168** | **336** |

56 candidates x 3 frames = 168 rows, matching `nll_candidates_scored` exactly — so every candidate
in R was reached and no slot was silently short. Each row asserted BOTH reductions: **336
`math.isfinite` calls, all true, no NaN and no infinity.**

**The spread-0 control RAN rather than merely not raising.** Realized `controls` ==
`('birth_year', 'house_number')` == `SPREAD_ZERO_CONTROL_SLOTS`.
`assert_spread_zero_reductions_agree` returns `False` on the six length-confounded slots, so a
control that silently skipped would have produced a short tuple and aborted the smoke. Both slots
were independently confirmed to measure `length_spread == 0` — the premise the monotonic-transform
argument rests on — and the assertion is full `ranking` equality, not just the taught value's rank:
all 7 candidates on `birth_year` and all 6 on `house_number` ordered identically under sum and mean.

### Degeneration attractors — all eight intervals overlapped their prior

No shape degenerated. The closest call was A2's role-token leakage at 6/64, lower bound 0.049256
against the 56/936 prior's upper bound of 0.073894 — still overlapping, so no abort. Worth
recording because a POINT comparison against the prior rate (0.0598) would have flagged 6/64
(0.094) as degenerate. This is exactly the false abort 18-10's non-overlap construction was built
to avoid, and it was realized on the first run that mattered.

## The K decision (Task 2)

**Presented at K=64:** 13.12h across both arms (~6.56h per arm), from the four measured rates —
1.605x the 8.173h floor, blended effective rate 143.04 draws/min. Full derivation in the
checkpoint return and re-derived in the report.

**Decision: `reduce-k`, K = 48.** Projected 9.91h at decision time from the K=64-measured rates;
**re-measured at 9.54h** once the smoke re-ran under the new seeds.

K = 48 was also the largest reduction that keeps the ladder well-formed: `ASR_RUNGS = (1, 4, 16, K)`
means any K <= 16 collapses the top rung into the third, so 24 was the floor available without
redesigning the tuple.

## Deviations from Plan

### 1. [Rule 3 — Blocking] A stale guard from 18-10 forbade the artifact this plan exists to create

- **Found during:** Task 1, on the first full-suite run after the smoke wrote its report
- **Issue:** `tests/test_phase18_prereg.py::test_smoke_covers_nll_path` ended with
  `assert not extraction.SMOKE_REPORT_PATH.exists()`. Running the smoke — Task 1's whole action —
  turned it red (720 passed / 1 failed against the 721/0 baseline). Task 3 could not satisfy both
  "commit the report" and "full suite green" while it stood. The plan never mentions it.
- **Root cause, not symptom:** the guard's own message states its precondition — "an artifact
  appearing **before the driver is complete** would freeze the pin mid-assembly". `e37395e` (18-10)
  added it while the driver was mid-assembly; `ec18cfe` (18-11) landed `run_report` and completed
  the driver, expiring it. By 18-13 it had inverted into an assertion that the pre-flight had not
  happened yet.
- **Fix:** removed that ONE assertion, in its own commit, BEFORE any driver amendment. The node and
  its other two assertions were kept — deleting the node would have dropped the
  `SPREAD_ZERO_CONTROL_SLOTS` and 8-slots/3-frames checks with it. A comment records the
  retirement and names both commits. The ordering it protected is still enforced, where git can
  see it: `tests/test_phase16_prereg.py` proves every driver commit precedes the artifact.
- **Ancestry impact:** none. The commit touches only `tests/test_phase18_prereg.py`, so it never
  enters the driver's ancestry set.
- **Commit:** `83b0ddd`

### 2. [Rule 2 — Correctness] K=48 falsified 32 literals beyond the constant itself

- **Found during:** Task 2
- **Issue:** `K = 64` appears once, but the value is restated across the pin's arithmetic, the
  report renderer, assertion messages, docstrings and two test anchors. Left alone, the pinned file
  would have contradicted its own constant and the committed artifact would have carried a false
  floor line.
- **Fix — driver (20 literals):** the cost-model pin block (82,944 attack + 2,016 control = 84,960
  draws ~ 6.2h); `_render_smoke_report`'s floor line (112,608 at 8.2h -> 84,960 at 6.2h, which is
  rendered INTO the artifact); "the attacks' 64-draw rungs"; the four "64 rates / proportions /
  Wilson bounds" curve-point mentions; the four D-25/D-26 budget mentions; `ASR@64`; the
  "disjoint 64-seed window ... K = 64" pair and its "63 questions" neighbour count (K-1); and seven
  "8.2h" run-cost mentions. Rhetorical cost mentions took the MEASURED 9.9h; the one sentence
  explicitly about the floor took the new floor, 6.2h.
- **Fix — tests (12 literals):** `test_aggregate_questions`'s expected tuple, now **derived** as
  `(K - i, K)`; `test_strided_seeds_are_disjoint`'s `13824 -> 10368` and `279 -> 263`
  (`N_SOURCE_QUESTIONS + K - 1`); `_FIXTURE_DRAWS`; and prose in `conftest.py`,
  `test_phase18_draws.py` and `test_phase18_prereg.py`.
- **Deliberately NOT changed:** the three "64"s in `_rate_lower_bound`'s docstring. Those are the
  SMOKE's own 64 draws per shape — `SMOKE_PROMPTS_PER_SHAPE` (8) x `SMOKE_DRAWS_PER_PROMPT` (8) —
  and are independent of K. Changing them would have been the one edit in this sweep that made the
  file less true.
- **Commit:** `99716e0`

### 3. The report was regenerated, not re-committed

- **Found during:** the checkpoint return
- **Issue:** the K=64 report was already on disk and passing every acceptance criterion. Committing
  it under a K=48 pin would have published a projection for a run that will never happen.
- **Fix:** re-ran `--smoke` after the driver commit. The report is K-dependent twice over — the
  projection multiplies by K, and the draws seed at `entry['seed_index'] * K`, so the completions
  and attractor hits genuinely differ (A2's role-token count moved 3/64 -> 6/64). `run_smoke` has
  no clobber guard by design, so it overwrote in place. Provenance now records driver `99716e08`.

### Acceptance criteria reported rather than contorted

**`build_corpus` was confirmed unaffected rather than assumed.** K is draws per prompt, not prompt
count. Measured after the amendment: 864 entries, 216 per family, and `corpus_sha256` **byte-identical**
at `ff8e6e3c...` across the K=64 and K=48 runs.

**The `229.68` vs `229.632` discrepancy is recorded, not acted on.** `18-RESEARCH.md` R-14 gives
229.632 as exact (`2430 / 10.5821498`); the driver and CONTEXT both say 229.68. Every projection in
this plan was computed from 229.632. Correcting the literal would be a driver amendment with no
behavioural need, and after `2d7151e` the driver is uneditable — so this is a **known note, closed
by the pin**, not an outstanding action.

## Verification

| Check | Result |
|---|---|
| `pytest -q` after `83b0ddd` | **721 passed, 1 skipped, 0 failed** |
| `pytest -q` after `99716e0` | **721 passed, 1 skipped, 0 failed** |
| `pytest -q` after `2d7151e` | **721 passed, 1 skipped, 0 failed** (137.93s) |
| `pytest -q tests/test_phase16_prereg.py -k phase18` | 1 passed — **`checked` = 26**, previously vacuous 0 |
| `git log --diff-filter=A -- results/phase18_preflight_report.md` | one SHA, `2d7151e` |
| `git merge-base --is-ancestor <driver> 2d7151e` | exit 0 for **all 26** driver commits |
| `grep -ciE "adapter-on\|persona_adapter\|adapter_disabled"` (report) | **0** — zero adapter-arm preview |
| `grep -cE "\b0(\.0+)?%"` (report) | **0**; the only `%` tokens are two "95%" confidence labels |
| `grep -c draws_per_min` (report) | **4** — one per prompt shape |
| report length | 81 lines (>= 40 required) |
| `ruff check . && ruff format --check .` | All checks passed; 84 files formatted |
| Files deleted by any commit | **0** |

### RED confirmation (Task 3 acceptance)

A trivial comment appended to `scripts/phase18_extraction.py`, committed on branch
`scratch-red-confirm` as `fc69ed1`, turned the guard **red** with exactly the intended failure:

```
subprocess.CalledProcessError: Command ('git', 'merge-base', '--is-ancestor',
  'fc69ed18...', '2d7151ee...') returned non-zero exit status 1
```

The branch was deleted (`git branch -D`) and `main` verified **byte-identical**: HEAD still
`2d7151ee`, driver blob still `817df7a7`, working tree clean. No `git stash`, no force flag, no
reset of `main`.

**From `2d7151e` forward, `scripts/phase18_extraction.py` is permanently uneditable.** Any further
edit turns the guard red; the honest recovery is a reviewed deletion commit, never a force flag.

## Threat register disposition

| Threat ID | Disposition | Discharged by |
|---|---|---|
| T-18-13-01 (Tampering — K reduced after seeing a null) | mitigated | The decision was a blocking checkpoint taken on smoke evidence alone, before any `results/phase18_*` artifact existed and before any arm was drawn. The evidence is in the committed report; the reduction and its justification are in the pin block itself; the ancestry guard makes any later change red, proven by the RED confirmation |
| T-18-13-02 (Information Disclosure — the smoke previews the adapter arm) | mitigated | `grep -ciE "adapter-on\|persona_adapter\|adapter_disabled"` returns **0** on the committed report; `run_smoke` builds the base through `build_unadapted_base` and is AST-scoped to it by 18-10's guard |
| T-18-13-03 (Repudiation — an assertion weakened to get past an abort) | mitigated | No assertion fired in either run. Nothing was weakened, no tolerance relaxed, no parameter retried. The two test-anchor updates are K-arithmetic reconciliations under a changed constant, not relaxations — one was replaced by a **derivation** from K, which is strictly stronger than the literal it replaced |
| T-18-13-04 (Repudiation — the guard passes vacuously) | mitigated | `checked` recorded as **26** (26 driver commits x 1 tracked artifact), up from a vacuous 0. The RED confirmation proves the non-vacuous branch actually fails |
| T-18-13-SC (Tampering — package installs) | accepted | Zero installs; `pyproject.toml` untouched |

## Issues Encountered

- **The stale 18-10 guard** — Deviation 1. The only cross-plan guard this plan tripped, and it
  tripped because its precondition had expired rather than because anything was wrong.
- **Two K-dependent test anchors** — `13824` and `279` in `test_phase18_draws.py`, plus the
  staircase tuple in `test_phase18_prereg.py`. Found empirically by running the suite after the K
  change rather than by static reading, which is why the sweep was trustworthy: the guards named
  themselves.
- **No abort in either smoke run.** The regenerated run drew from entirely new seeds
  (`seed_index * K` with K=48) and still cleared every structural and degeneracy assertion.

## Deferred Issues

None new. The one item in `deferred-items.md` is 18-04's and is untouched.

## Known Stubs

None. Measured rather than inherited: the driver has **0 `TODO` and 0 `FIXME`**, and 10 hits for
`placeholder`, all legitimate. One is 18-06's `ans1` `{v}` template token — the same one 18-07
through 18-10 reported. The other **nine are 18-11's `append_addendum`**, whose keyword parameter is
literally named `placeholder`; they are an API surface, not a stub marker. The report has **0** of
any of the three. 18-10's one declared stub (`run_report` undefined) was closed by 18-11 in
`ec18cfe`.

*(18-10's SUMMARY recorded this count as 1. That was true at 18-10 and is stale rather than wrong —
`append_addendum` landed in the next wave. Re-counted here rather than carried forward.)*

## User Setup Required

None. The smoke needs only `checkpoints/convbase_slim.pt`, which is gitignored and present in the
main checkout. **Note for whoever runs 18-15:** the two arms additionally need
`checkpoints/persona_adapter.pt`, and the smoke cannot be run from a git worktree — the base
checkpoint is gitignored and exists only in the main checkout.

## Threat Flags

None. No new network endpoint, auth path or schema change. One new file-access pattern reaching
disk for the first time — `run_smoke` writing `SMOKE_REPORT_PATH` — which is the plan's declared
artifact, re-runnable by design because it is a pre-flight measurement rather than evidence a rate
was scored from.

## Next Phase Readiness

- **The pin is armed and closed.** `scripts/phase18_extraction.py` is uneditable from `2d7151e`.
  Every future `results/phase18_*` artifact must descend from all 26 driver commits.
- **18-14 can generate the corpus as-is.** `--corpus` writes `canonical_json(corpus)` with no
  trailing newline behind a clobber refusal. Its content is **unchanged by the K reduction** —
  confirmed at sha `ff8e6e3c...`, 864 entries — so 18-14's byte-equality guard is unaffected.
- **18-15 should budget ~9.5h across both arms**, ~4.8h per arm, at K=48. That figure is measured
  on the base; the adapter arm's stop-termination rate is unknown and unknowable without previewing
  the taught column, so it carries that irreducible uncertainty honestly.
- **18-16 reports the ladder at rungs (1, 4, 16, 48).** The top rung is re-priced: ASR@48 rather
  than ASR@64. Any inherited text naming ASR@64 is now wrong.

## Self-Check: PASSED

- `results/phase18_preflight_report.md` — FOUND (81 lines, tracked, first-add `2d7151e`)
- `.planning/phases/18-black-box-adversarial-extraction-audit/18-13-SUMMARY.md` — FOUND
- `83b0ddd`, `99716e0`, `2d7151e` — all FOUND in `git log`
- `fc69ed1` — correctly UNREACHABLE: no branch contains it and it appears in no ref's history
  (`git log --all` count 0). The object survives as dangling until `gc`, which is expected; what
  matters is that no ref points at it and `main` is byte-identical
- `git status --short` clean apart from this SUMMARY
- No `STATE.md`, `ROADMAP.md` or `REQUIREMENTS.md` touched — the orchestrator owns them
- No file deleted by any commit; 50 line removals, all K-literal reconciliations and the retired
  assertion

---
*Phase: 18-black-box-adversarial-extraction-audit*
*Completed: 2026-08-16*
