---
phase: 21
slug: the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-08-22
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
>
> **Source of truth for the full requirement→test map:** `21-RESEARCH.md` §`## Validation
> Architecture` (`:175`), whose every command and timing is marked `[VERIFIED]` against a real run.
> This file is the execution-time contract; that file is the evidence.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Python** | 3.11.15 — **`.venv` only.** The dev box is 3.14 and is NOT a supported target (CLAUDE.md). Never validate there. |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (`:24-26`) — `testpaths = ["tests"]`, `pythonpath = ["."]` |
| **Quick run command** | `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py tests/test_package.py tests/test_masked_batch.py tests/test_phase14_teaching.py` |
| **SC5 guard set** | `.venv/bin/python -m pytest -q tests/test_phase14_scoring.py tests/test_phase16_driver.py tests/test_phase16_ladder.py tests/test_phase18_corpus.py tests/test_phase18_prereg.py tests/test_phase19_erasure.py tests/test_phase14_factset.py tests/test_phase14_demo.py` |
| **Full suite command** | `make test` (`pytest -q`) |
| **Estimated runtime** | quick **3.45s** (62 passed) · SC5 guard set **~36s** (314 passed for 7 files; +`test_phase14_demo.py`) · full **195.26s** (877 passed, 1 skipped, exit 0) |

**The one skip is expected by design:** `test_loop_penalty_fn::test_golden_trajectory_bit_identity`
is platform-gated; the in-process identity tests carry the guarantee
(`tests/test_loop_penalty_fn.py:95-107`). A run reporting `877 passed, 1 skipped` is GREEN.

**CI prerequisite that is load-bearing here:** `.github/workflows/ci.yml:21` sets `fetch-depth: 0`.
`_assert_ordering_holds` asserts `rev-parse --is-shallow-repository == "false"` and refuses to skip
(`tests/test_phase20_prereg.py:136-141`) — a shallow clone turns the ancestry guard into an error,
not a silent pass.

---

## Sampling Rate

- **After every task commit:** the **quick run command** + every `tests/test_phase21_*.py` that
  exists at that point. ~3.5s.
- **After every plan wave:** the **SC5 guard set** + all `tests/test_phase21_*.py`. ~36s.
- **Before the first `results/phase21_*` COMMIT:** `pytest -q tests/test_phase20_prereg.py` must be
  **armed and green first** (1.86s / 21 tests). `git ls-files` is the guard's input, so an artifact
  becomes watched when it is **committed**, not when it is written. Arm-then-write is an ordering
  constraint on commits, and `:157` (`adds[-1]`, the earliest add) makes it irrevocable.
- **Before `/gsd:verify-work`:** full suite green — `877 passed, 1 skipped`.
- **Max feedback latency:** 36s at wave granularity; 3.5s at task granularity.

---

## Per-Task Verification Map

Task IDs are assigned by the planner. Rows below are the requirement-level contract every plan
must map its tasks onto; `File Exists` is measured against the repo as of 2026-08-22.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | UNIT-02 | — | N/A | golden fixture | `pytest -q tests/test_phase21_aligned_bins.py -k byte_identity` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-02 | — | N/A | unit (non-vacuity) | `... -k align_facts_is_wired` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-02 | — | N/A | content | `... -k window_purity_input` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-02 | — | N/A | content | `... -k window_purity_target` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-02 | — | N/A | adversarial | `... -k window_purity_adversaries` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-02 | — | N/A | unit | `... -k three_bin_alignment` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-02 | — | N/A | integration | `pytest -q tests/test_phase21_aligned_loader.py -k grad_accum` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-02 (D-06) | — | fact map read on EVERY access | adversarial | `... -k consumed_at_runtime` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-02 (D-06) | — | loader RAISES on missing/truncated fact bin | unit | `... -k fact_bin_required` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-03 | — | N/A | unit | `pytest -q tests/test_phase21_multiplicity.py -k conservation` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-03 | — | N/A | adversarial | `... -k instrument_can_report_not_one` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-03 | — | N/A | unit | `... -k seed_reproducible` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-04 (D-11) | — | replay volume independent of private fact VALUES | differential | `pytest -q tests/test_phase21_replay_volume.py -k side_channel_closed` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-04 (D-24) | — | N/A | unit | `... -k window_quantized` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-01/04/05 | — | N/A | unit | `pytest -q tests/test_phase21_unit_pin.py -k prove_guards` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-01/04/05 | — | frozen module imports ⊆ `{pathlib, sys, erasure_gate}` | AST | `pytest -q tests/test_phase20_prereg.py -k import_graph` | ✅ covers the new module via the glob | ⬜ pending |
| TBD | TBD | TBD | UNIT-01/04/05 | — | guard armed BEFORE first artifact | git history | `pytest -q tests/test_phase20_prereg.py -k phase21` | ❌ W0 (two additive edits, both required) | ⬜ pending |
| TBD | TBD | TBD | UNIT-01/04/05 | — | guard proven non-vacuous | git fixture | `... -k phase21_glob_red_then_green` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 (D-16) | — | N/A | golden fixture | `pytest -q tests/test_phase21_filler.py -k render_family_byte_identity` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 (D-16) | — | N/A | unit (non-vacuity) | `... -k forms_is_wired` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 (D-16) | — | filler slots DISJOINT from the 11 published slots | unit | `... -k slots_disjoint` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 (D-17) | — | collision refusal vs the 10, the 28, and each other | unit | `... -k minting_discipline` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 (D-13) | — | filler OUTSIDE `all_pools()`; `_BY_ID` gains no keys | unit | `... -k outside_all_pools` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 / SC5 (D-18) | — | no filler value reaches any published instrument | content | `pytest -q tests/test_phase21_sc5.py -k no_filler_leak` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 / SC5 | — | `scripts/phase18_extraction.py` byte-unchanged | sha256 | `... -k instruments_unchanged` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 / SC5 | — | 270-question fixture byte-unchanged | sha256 | `... -k instruments_unchanged` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 / SC5 | — | all 8 `== 10` wall sites still green | existing | the **SC5 guard set** command above | ✅ exists | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 / SC5 | — | `len(LOCKED_FACTS) <= 8`, `len(SOFT_TIER_FACTS) <= 3` | existing | `pytest -q tests/test_phase14_factset.py -k composition_targets` | ✅ `tests/test_phase14_factset.py:101-103` | ⬜ pending |
| TBD | TBD | TBD | all (RPT-03) | — | `pyproject.toml` untouched — zero new deps | sha256 | `pytest -q tests/test_package.py` | ✅ `tests/test_package.py:37` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### The `== 10` wall is 8 sites across 7 files, not 4

CONTEXT.md D-18 names **four**; `21-RESEARCH.md` corrected it to **seven across six**; a direct
grep finds **eight across seven**. Any plan sampling fewer under-samples the wall SC5 rests on:

| # | Site | Variable |
|---|------|----------|
| 1 | `tests/test_phase14_scoring.py:405` | `forbidden` |
| 2 | `tests/test_phase16_driver.py:313` | `forbidden` |
| 3 | `tests/test_phase16_ladder.py:443` | `forbidden` |
| 4 | `tests/test_phase16_ladder.py:711` | `forbidden` |
| 5 | `tests/test_phase18_prereg.py:127` | `forbidden` |
| 6 | `tests/test_phase19_erasure.py:625` | `forbidden` |
| 7 | `tests/test_phase18_corpus.py:430` | `values` |
| 8 | **`tests/test_phase14_demo.py:394`** | `values` — **named in neither CONTEXT.md nor RESEARCH.md**; B-01 demo fact-freedom, same `LOCKED_FACTS + SOFT_TIER_FACTS == 10` assertion |

`tests/test_phase14_demo.py` is therefore added to the SC5 guard set above.

---

## Wave 0 Requirements

- [ ] `tests/test_phase21_aligned_bins.py` — UNIT-02 content proofs + `build_bins` golden fixture
- [ ] `tests/test_phase21_aligned_loader.py` — UNIT-02 / D-06 run-time consumption proofs
- [ ] `tests/test_phase21_multiplicity.py` — UNIT-03 instrument validation
- [ ] `tests/test_phase21_replay_volume.py` — UNIT-04 / D-11 / D-24 side-channel differential
- [ ] `tests/test_phase21_unit_pin.py` — the frozen module's `_prove` guards
- [ ] `tests/test_phase21_filler.py` — UNIT-06 corpus + `render_family` golden fixture
- [ ] `tests/test_phase21_sc5.py` — SC5 non-disturbance
- [ ] `tests/fixtures/golden_build_bins_v2.json` — captured from a **git-clean, pre-edit**
      `teach_persona.py`. Captured after the edit it proves nothing.
- [ ] `tests/fixtures/golden_render_family_v2.json` — captured from a **git-clean, pre-edit**
      `phase14_factset.py`. Same constraint.
- [ ] **Two additive edits to `tests/test_phase20_prereg.py`** (D-20) — the `V4_ARTIFACT_GLOBS`
      addition **and** a `_assert_ordering_holds(..., artifact_glob="results/phase21_*")` call.
      Neither is sufficient alone: `globs` is used only at `:129` for a consistency check and the
      ordering loop runs on the singular `artifact_glob`.

**No new framework, no new fixture infrastructure, no conftest change, no new dependency.**

### The governing rule for every byte-identity proof in this phase

> **A byte-identity assertion with no paired non-identity assertion is vacuous.** `X=None` is
> trivially satisfied by a kwarg that is never read.

Every `*_byte_identity` row above is therefore paired with an `*_is_wired` row that fails if the
kwarg is inert. This is not redundancy — it is the only thing that makes the identity claim mean
anything. **RESEARCH.md Open Question 1 is a live instance:** `render_family(...,
question_bank=None)` appears **unfalsifiable as sited** — `SLOT_QUESTION_BANK` is read only at
`phase14_factset.py:279` inside `_assign_probes()`, and `_render_family:690` reads only
`SLOT_FORMS`, so no value of that kwarg can change `render_family`'s output. The planner must
either re-site the kwarg or drop it; it must not ship a guard that cannot fail.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Arm-then-write commit ORDER for the ancestry guard | UNIT-01/04/05 (D-20) | The property is over **git history**, not over a working tree. A test can assert the ordering holds, but only the operator controls which commit lands first — and `:157` (`adds[-1]`) makes a wrong order permanent. | Land the two `test_phase20_prereg.py` edits GREEN in a commit that is a strict ancestor of the first `results/phase21_*` commit. Verify with `git merge-base --is-ancestor <pin-commit> <artifact-commit>` before committing any artifact. Note `:300-304`: `--is-ancestor X X` exits 0, so same-commit PASSES the mechanism — "strictly after" is a tighter discipline than the guard enforces, and it is deliberate. |
| `results/phase21_*` artifacts are COMMITTED, not merely written | UNIT-03 (D-26) | `git ls-files` is the guard's input. `results/` is not gitignored, but an uncommitted artifact is invisible to the guard — a silent no-op, not a failure. | After the driver writes, confirm `git ls-files results/phase21_*` is non-empty before claiming the guard covers them. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies — **29/29 tasks; zero MISSING markers**
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references — all 10 artifacts owned by a named plan (aligned_bins→21-04, aligned_loader→21-06, multiplicity→21-10, replay_volume→21-08, unit_pin→21-01, filler→21-05/21-07, sc5→21-09, both goldens→21-02, both `test_phase20_prereg.py` edits→21-01)
- [x] Every `*_byte_identity` test is paired with a non-vacuity `*_is_wired` test — `question_bank` was **dropped** rather than shipped unfalsifiable (21-05)
- [x] Every new guard proven **deliberate-RED then byte-identically restored**
- [x] No watch-mode flags — task-granularity commands run 1.9s–36s
- [x] Feedback latency < 36s
- [x] `nyquist_compliant: true` set in frontmatter

`wave_0_complete` stays **false** by design: the ten Wave 0 files are *planned and owned*, not yet
written. It flips during execution, not during planning.

### Wave structure — SIX waves, not five

Plan 21-09 was moved from wave 4 to **wave 5**, and 21-11 from wave 5 to **wave 6**. Reason, recorded
here because it is a validation-integrity fact and not a scheduling preference: 21-09's three
deliberate-REDs transiently mutate WORKING-TREE files it does not own — `scripts/phase14_factset.py`
(21-05's), `scripts/phase21_filler.py` (21-07's) and the ancestry-guarded
`scripts/phase18_extraction.py` (nobody's). Same-wave 21-10 runs the FULL SUITE and
`git diff --exit-code scripts/phase18_extraction.py` in its `<verification>` block. A canary live
during a concurrent reader is a flake attributed to the innocent plan, and `files_modified` cannot
prevent it because the plan that READS a file need not DECLARE it. An explicit `depends_on: 21-10`
edge on 21-09 serializes them; the three guarded/non-owned paths were removed from 21-09's
`files_modified` so that listing them can no longer read as permission to edit.

| Wave | Plans |
|------|-------|
| 1 | 21-01, 21-02 |
| 2 | 21-03, 21-04, 21-05 |
| 3 | 21-06, 21-07, 21-08 |
| 4 | 21-10 |
| 5 | 21-09 |
| 6 | 21-11 |

---

## Approval

**RE-VERIFIED 2026-08-22**, against the plan set produced by the blocker-fix revision on top of
`9cc2c94`. This is the CURRENT set and it is the one this document covers.

**The earlier line is superseded and was stale.** It read *"approved 2026-08-22 — plan set `fc2e6dc`,
verified by `gsd-plan-checker` (0 blockers)"*. Six plans — 21-04, 21-06, 21-08, 21-09, 21-10, 21-11 —
changed after `fc2e6dc` (`git diff --stat fc2e6dc..HEAD`), so that approval never covered the set
subsequently reviewed. It is retained here as a corrected record rather than deleted, because a
sign-off quietly overwritten is indistinguishable from one that was always right.

**And the "0 blockers" claim was false of the set it was later read against.** A `gsd-plan-checker`
pass over the post-`fc2e6dc` set returned **1 blocker and 7 warnings**. All eight were closed by this
revision:

| # | Severity | Finding | Closed by |
|---|----------|---------|-----------|
| 1 | **BLOCKER** | `fact_window_impurities` defaulted to `space="both"` (the UNION), which refuses every CORRECTLY built bin — measured `[]` in input space but `[1, 2]` in target space on the plan's own A0 fixture, so proof-7 would abort every aligned build. The stated padding justification was also false: the boundary crossing is a property of the +1 label shift, not of padding. | 21-04, 21-06 — default is `space="input"` (SC2's own wording), no union mode; the target-space claim is restated POSITIVELY as `n_facts - 1` boundary rows with every boundary token's mask asserted 0 |
| 2 | warning | 21-09's transient mutation of ancestry-guarded / non-owned files could flake same-wave 21-10 | 21-09 → wave 5 behind 21-10; guarded paths removed from `files_modified`; 21-11 → wave 6 |
| 3 | warning | `count_aligned` could not obtain `per_step_distinct_facts` — the loader raises first, and neither offered route was pinned | 21-10 pins `strict=True` in the signature; `strict=False` reuses 21-06's newly EXPORTED `fact_window_span`, so it is not a re-implementation |
| 4 | warning | `render_filler_episodes` omitted `sorted()` over a frozenset — measured three different orders in three processes | 21-07 mirrors `teach_persona.py:251`; a cross-process digest test and a deliberate-RED were added |
| 5 | warning | 21-07 asserted an unmeasured `56 * 22 == 1232` | 21-07 marks it an ESTIMATE with a record-and-STOP clause; the binding assertion is EQUALITY with a scored fact's observed count inside `PARAPHRASES_PER_FACT_TARGET` |
| 6 | warning | 21-04's aligned branch left `episodes` undefined while `stats["episodes"]` still reported it | 21-04 pins `episodes=[]` on the aligned branch, raises on ambiguous non-empty input, and defines the key as the pairs' row total |
| 7 | warning | five stale line references | corrected in 21-02, 21-05, 21-07, 21-09 — every one re-verified against the repo before writing |
| 8 | warning | this sign-off was stale | this section |

### Re-check pass 2 — the blocker CLOSED, three regressions found and fixed

The revision above was re-checked. The blocker is **closed and independently confirmed**: the
checker rebuilt the real 8-fact bin at `block_size = 256` and measured input space `[]`, target space
`[3, 7, 11, 15, 19, 24, 28]` = exactly 7 = `n_facts - 1`, `fact_ids[(k+1)*256] == fact_ids[k*256] + 1`
at all seven, and `serialize.py:81` verbatim. W2 and W4-W8 all confirmed closed.

That pass found **three NEW warnings, every one introduced by the revision itself**. Recorded here
rather than silently repaired, because a revision that fixes a blocker and quietly adds three
regressions is the failure mode this phase exists to make visible:

| # | Severity | Regression the revision introduced | Closed by |
|---|----------|------------------------------------|-----------|
| A | blocker-adjacent | The W3 fix put only the LOADER call inside `try/except`, but plan 21-06 requires `fact_window_span` to raise on non-contiguous rows — and task 3's roll-by-1 makes fact index 7 non-contiguous (measured: rows `[0, 30, 31, 32]`). `count_aligned(strict=False)` therefore aborted out of the SPAN call at step 7, i.e. on any run with `steps >= n_facts`, which is exactly the full lot task 3 runs. The fix aborted on the very adversary it was written to observe. | 21-10 — BOTH calls in ONE `try/except ValueError`; `per_step_raised` records `"span"` as its own outcome class; task 3 pins `steps >= n_facts` and asserts a `"span"` entry is present. `fact_window_span`'s contiguity raise is explicitly NOT relaxed |
| B | warning | Five threat IDs minted by the revision (T-21-50…54 in 21-04 / 21-06 / 21-10) each collided with an unrelated threat plan 21-11 already held, breaking the register's own convention that a shared ID means the SAME threat | renumbered to **T-21-59…63**; 21-11 untouched. The separately double-booked pre-existing **T-21-49** was also fixed: 21-10's became **T-21-64** (21-11 keeps T-21-49), stated in 21-10's register |
| C | warning | A stray duplicate `</output>` closing tag in five plans | deleted from 21-04, 21-06, 21-07, 21-09, 21-10; the six already-balanced plans untouched. All 11 now 1/1 |

Two non-blocking notes were also addressed: every downstream plan citing a file plan 21-04 or 21-08
rewrites (**21-06, 21-08, 21-09, 21-10**) now carries a `LINE ANCHORS: resolve BY SYMBOL` paragraph,
because those anchors are correct only against the PRE-wave-2 tree; and 21-06 task 1's acceptance
criterion now says out loud that `tests/test_phase21_aligned_loader.py` is created in task 2 and the
criterion closes there.

**Threat register invariant, stated precisely — the earlier wording here was overstated and is
corrected.** It read *"across all 11 plans, every `T-21-NN` denotes exactly one threat"*, which is
false at the literal level for two pre-existing IDs. The accurate claim: **every ID denotes one
threat CLASS, instantiated per component.** Shared IDs and their classes:

| ID | Class | Sites |
|----|-------|-------|
| T-21-03 | the pin is not actually in force when an artifact lands | 21-01 (post-hoc edit), 21-03 (glob silently reverted), 21-11 (artifact committed before the pin) |
| T-21-04 | a value or edit moves a published instrument | 21-05 (edit moves a row), 21-07 / 21-09 (filler value enters the leak vocabulary) |
| T-21-05 | a guard that cannot fail | 21-01, 21-02, 21-03, 21-04, 21-05 |
| T-21-06 | ancestry laundering by delete-and-re-add | 21-01, 21-03, 21-11 |
| T-21-08 | an edit reaches a frozen file | 21-05, 21-07, 21-09 |
| T-21-11 | supply chain | all 11 |
| T-21-15 | a test depends on machine-local `data/` | 21-02, 21-08 |
| T-21-20 | correct offsets over wrong bytes | 21-04, 21-06 |
| T-21-24 | a test writes into `data/` | 21-04, 21-06 |

T-21-03 and T-21-04 are the two the earlier sentence got wrong; both patterns are identical at HEAD,
i.e. pre-existing convention rather than anything this revision introduced. What IS newly true and
was the actual defect fixed in pass 2: no ID denotes two UNRELATED threats. High-water mark:
**T-21-65**.

### Re-check pass 3 — VERIFICATION PASSED, then four warnings closed

Check 3 returned **`## VERIFICATION PASSED`, 0 blockers, and no third generation of regressions.**
W-A, W-B, W-C and both notes were confirmed closed against the files rather than against the summary;
both sha256 pins re-verified live; the δ arithmetic re-run in `.venv`; the 7-boundary target-space
count re-derived from D-01's geometry; waves, graph, collisions, UNIT-01…06, D-01…D-26 and Nyquist
all clean.

Four warnings survived that pass and were closed afterward. **Two were pre-existing at HEAD and two
came from the revisions** — recorded that way because which is which is the only part a reader
cannot reconstruct later:

| # | Origin | Finding | Closed by |
|---|--------|---------|-----------|
| W1 | **introduced by revision 2** | `count_aligned(strict=False)` never pinned that `np.unique` must run BEFORE the loader call, and one `try` gave no way to tell `"span"` from `"loader"`. MEASURED on the rolled bin: **all 8 steps raise** — the loader raises impurity at steps 0-6 (fact 0 owns rows `[1,2,3,4]`; row 4 = `rolled[1024:1280]` = `original[1023:1279]` carries facts 0 and 1) and the span raises at step 7. Unique-after-loader ⇒ `per_step_distinct_facts == [None]*8` ⇒ task 3's `max(...)` dies with `max() arg is an empty sequence`, i.e. the non-vacuity test ERRORS. | 21-10 task 1 — order pinned (`np.unique` immediately after `fact_window_span`, strictly before the loader) plus a `stage` local (`"span"`→`"loader"`) that the single `except` records as `per_step_raised` |
| W2 | **hazard fixed twice, missed here** | Wave 3 carried the exact hazard 21-09 was serialized out of wave 4 to remove: all three of 21-06 / 21-07 / 21-08 ran a bare `pytest -q` (`testpaths = ["tests"]`) while each held a live working-tree deliberate-RED a sibling's run would collect — including 21-06's full suite collecting `tests/test_phase21_replay_volume.py`, which 21-08 is deliberately reddening | scoped, not serialized: the six per-plan full-suite invocations in 21-06 / 21-07 / 21-08 were replaced with explicit file lists plus a note that the full suite is a WAVE-CLOSE / `/gsd:verify-work` gate — which `:47` and `:52` above already said. **Wave 3 stays parallel; no `depends_on`, `wave` or ROADMAP change.** Waves 1 and 2 were audited for the same pattern and are clean (transient mutations, zero full-suite runs); waves 4-6 are single-plan |
| W3 | **pre-existing at HEAD** | `test_wall_census_is_eight_sites` was specified to FAIL: the same task requires `test_phase21_sc5.py` to carry `len(forbidden) == 10`, while the census greps for exactly that and asserts 8 sites / 7 files with an explicit instruction not to adjust the number. Measured: 8/7 today, 9/8 with the new file | 21-09 — mechanical `__file__` exclusion in the walk (not a comment), with the reason stated: the census measures the PRE-EXISTING wall. The re-siting alternative (21-05's non-matching `len(fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS) == 10` form) was rejected for dodging the grep by accident of phrasing |
| W4 | **pre-existing convention, overstated by revision 2** | The pass-2 paragraph claimed every `T-21-NN` denotes exactly one threat. False for `T-21-03` (three sites) and `T-21-04` (two) | the paragraph above, rewritten as a threat-CLASS table naming all nine shared IDs. Nothing renumbered |

**A ninth `== 10` assertion exists and is now recorded** (INFO, surfaced by check 3):
`tests/test_phase14_demo.py:568` — `assert len(result["values"]) == 10`. It matches NEITHER census
grep pattern, so the 8/7 count stays internally consistent, and it IS executed because the SC5 guard
set runs that whole file. Written into 21-09's census docstring so the next reader meets it as a
known fact instead of re-discovering it as a regression.

**Status: revised three times, awaiting re-check.** No `gsd-plan-checker` pass has run against the
set as it stands after the four fixes above. `status: approved` in the frontmatter refers to the
validation STRATEGY, which is unchanged; it is not a claim that the current plan set has been
re-checked. The next `gsd-plan-checker` run is what upgrades this line.
