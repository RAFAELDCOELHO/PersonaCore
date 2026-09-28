# Phase 33: Admission and Relearning on Admitted Points - Context

**Gathered:** 2026-09-28
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase calls the frozen v5.0 admission contract (`phase29_prereg.admission`) **once** on the
committed frontier `results/phase32_frontier.json`. It writes `results/phase33_admission.json`
write-once and ships whichever branch that record names.

**The branch is already measurable. It is MOOT.** Running `phase29_prereg.admission(frontier)` live
on the committed frontier (2026-09-28, during this discussion) returned `verdict: MOOT`,
`admitted_point_keys: []`, with these reasons:
`0 of 12 points PASS; tallies {PASS 0, FAIL 0, INCONCLUSIVE 6, REFUSED 6}`,
`advr_n64 fully REFUSED (advr_n64 control recall taught 0/1008, heldout 1/648); MOOT does not extend to that capacity`,
`MOOT: no measured point cleared the frontier — nothing to relearn`.
`relearning_scope()` gives `RELRN-06..09 ship as a MOOT named limitation`. The Phase 32
verification recomputed the same result (32-VERIFICATION.md:56). The planner re-derives this from
the committed frontier and does not trust this paragraph. Which branch runs is the record's output
(PREREG-02 / 29 D-10), never a decision.

Phase 33 therefore delivers five things: the admission driver; its write-once record; a refusal
surface for the RELRN-06..09 attack legs; the MOOT named limitation; and the disposal of carried
debt to the Phase 34 ledger. **Out of scope:** any relearning training or scoring code, any fix to
`phase32_points.py` / `phase32_frontier.py`, any edit to `phase27_prereg.py` / `phase29_prereg.py`,
and the rendered report (Phase 34).

</domain>

<decisions>
## Implementation Decisions

### Admitted-branch apparatus
- **D-01:** **Refusal surface only.** The Phase 33 driver has `admit` plus the attack-leg
  sub-commands. The first statement of every leg refuses unless the COMMITTED admission record reads
  ADMITTED, and no training or scoring code sits behind a leg. The advr port of
  `phase27_relearn`'s curve/gate/calibrate/structural-proof is **not built**. If a future milestone
  admits a point, it builds the body. A leg given a forged ADMITTED record must still refuse, with a
  message saying the v5.0 apparatus was not built because admission read MOOT. It must never look
  as though it ran.
- **D-02:** The refusal is proven by **tests plus live captures**, mirroring 27-05. A parametrized
  test makes each leg refuse on a MOOT / REFUSED / CANDIDATE-UNREPLICATED / INCONCLUSIVE record,
  and on an absent or untracked one. Live stderr captures of every leg on the real record are taken
  **before and after** its commit and must be byte-identical with exit 1.
- **D-03:** ADMIT-01 is met by **importing** `phase29_prereg` (`EXPECTED_POINTS`,
  `recall_threshold(frontier, leg, arm)`, `admission`, `relearning_scope`, `SCOPE_RULE`,
  `V5_RESULT_PATHS`). Nothing is retyped. `phase27_prereg.py` stays byte-unchanged and its ancestry
  guard stays green. `phase29_prereg.py` is not edited either, because it is the pre-registration.

### Admission record and commit
- **D-04:** **Thin record** at `results/phase33_admission.json` (the path is imported from
  `phase29_prereg.V5_RESULT_PATHS`). It contains:
  - the `admission()` result verbatim: verdict, reasons, admitted_point_keys, control_readings;
  - the `relearning_scope()` output;
  - frontier path, sha256 and bytes;
  - provenance: git_sha, head_at_write, `module_sha256` of phase29_prereg + the phase33 module + the
    gate modules admission reaches, and the prereg `COMMITTED` date;
  - the named limitation (D-08).

  Phase 27's baselines, disjointness, budget and rows fields are **not** carried, because they only
  fed an apparatus that ran.
- **D-05:** **Claude commits after developer review.** `admit` writes without committing, prints the
  verdict, the reasons and the control readings, and stops at a developer review checkpoint. After
  "approved", Claude commits the record **alone** in its own commit. This is the 31-06 / 32 D-16
  pattern. Claude never pushes.
- **D-06:** **No override.** If the record exists, `admit` refuses, and it has no `--force` flag.
  The only way to redo admission is to delete the record in its own commit. The overwrite refusal
  comes first and the dirty-tree refusal second, before any digest. The dirty check's pathspec
  excludes the record itself, as `phase27_relearn.admit` does. The planner confirms that exclusion in
  code with a test on a file that is **not yet tracked**, which is the state during the review
  checkpoint.
- **D-07:** **"Called exactly once" is proven three ways** (ADMIT-02):
  1. The write refusal (D-06).
  2. A git test: the record has exactly **one** commit, and that commit touches only that path. The
     test **fails loudly on a shallow clone** instead of passing vacuously.
  3. The record is pinned to the frontier both ways. The recorded sha256 is recomputed in the test
     from the live file's bytes, and the frontier has a single commit, derived from `git log` and
     never typed.

  The structure follows Phase 27's `test_the_record_is_pinned_to_the_frontier_both_ways`. The tests
  must handle the "written but not yet tracked" state of the review checkpoint. The prereg-before-
  result ancestry comes for free: `test_phase29_prereg_is_frozen_before_every_v5_result` already
  covers `results/phase33_*` through `ARTIFACT_PATHSPECS`.

### MOOT limitation and requirement ticks
- **D-08:** The limitation **is per leg and is carried verbatim from `admission()`'s reasons**. No
  hand-typed wording or numerals. n8 was measured: 0 of 6 PASS, all 6 INCONCLUSIVE, none a
  replication candidate. n64 **could not be measured**: its own control is unlearnable (taught
  0/1008), and MOOT does not extend to that capacity. It must never read "the mitigation held". The
  limitation states plainly that **only the refusal surface exists**, meaning the advr relearning
  apparatus was not built because the scope rule read MOOT. It **must not** copy Phase 27's
  "apparatus built and guarded, never exercised" phrasing.
- **D-09:** **Ticks follow the Phase 27 D-05 precedent, with a timing condition.**
  - **ADMIT-01 and ADMIT-02** are ticked only **after** the record is committed and the D-02/D-07
    proofs exist.
  - **RELRN-06..09 stay unticked.** Each traceability row reads
    `NOT SATISFIED — named limitation: admission read MOOT`. It cites the record and PREREG-02 and
    says only the refusal surface exists.
  - REQUIREMENTS.md / ROADMAP.md / STATE.md are **edited by hand**: snapshot before, diff after.
    **Zero `gsd-sdk` mutation handlers** are used, per the memory rule on handlers corrupting planning
    frontmatter.

  The phase can still pass verification, because ROADMAP SC4 calls MOOT a success path.

### Carried debt disposal
- **D-10:** **P31-WR-01** is the relearning csv under `results/` that trips `refuse_if_dirty` before
  crash recovery; Phase 32 D-09 assigned it to Phase 33. It is **closed in Phase 33 for lack of a
  consumer**, because no relearning artifact is written on the MOOT branch. No output-location code
  is written. It goes to the Phase 34 ledger as **RE-DEFERRED**, with:
  - reason: no relearning artifact on the MOOT branch;
  - target: the milestone that builds the legs' body;
  - prerequisite: decide where relearning artifacts live relative to `refuse_if_dirty` before the
    first one is written.
- **D-11:** The **open 32-REVIEW findings go to the Phase 34 ledger without being fixed in Phase 33.**
  `phase32_points.py` is pinned in 7 records, `phase32_frontier.py` is pinned in the frontier, and
  Phase 33 reuses neither.
  - **CR-01, WR-01 and WR-05** enter as **RE-DEFERRED**, with target "the milestone that reuses
    `phase32_points`". They keep the prerequisite fixed by the security ruling AR-32-02/03
    (`32-SECURITY.md:107-110`): fix them with dated pin continuations before any reuse.
  - Ledger ids carry a phase prefix (`P31-WR-01`, `P32-WR-01`, …) so they do not collide.
  - The ledger declares `provenance.git_sha` the authoritative pin and cites 32-VERIFICATION.md by
    reference, not by copying.
  - The planner checks whether any **IN-*** finding touches a field already published in the
    frontier. If one does, it needs a **dated continuation** instead of RE-DEFERRED.
  - WR-03 is already fixed (`325aaf0` RED, `f7c1a83` fix).
- **D-12:** **The AR-32-02/03 condition becomes an AST guard.** A census of the `scripts/phase33_*.py`
  modules turns RED on any import of `phase32_points` (any form: `import`, `from … import`,
  `importlib`), and its failure message cites AR-32-02. The RED is taken naturally from a temporary
  copy that carries the import, never planted in the real file. See the memory rules
  natural-red-beats-planted-red and grep-criteria-measure-prose, and use AST, not grep.

### Plan-time rulings (2026-09-28, after 33-RESEARCH.md)
- **D-13:** **D-06 strengthening: refuse if the record is tracked but absent.** The researcher measured the gap and it was confirmed in
  `phase27_relearn.admit:369-380`. If the committed record is deleted but the deletion is not
  committed, the overwrite check passes and the `:(exclude)` pathspec hides the deletion from
  `refuse_if_dirty`, so `admit` would re-run without the "delete it in its own commit" step.
  Phase 33 `admit` therefore **also refuses when the record path is tracked in HEAD
  (`git ls-files`) but missing on disk**, and tells the user to commit the deletion first. The
  refusal order is: overwrite, then tracked-but-absent, then dirty, all before any digest. The new
  refusal gets its own test.
- **D-14:** **WR-02 and WR-04 ledger dispositions (the researcher's split).**
  - **P32-WR-02** (the frontier's `module_sha256` omits the gate modules) enters the Phase 34
    ledger as a row citing 32-VERIFICATION.md:13 ("`git_sha` is the authoritative pin"), by
    reference. It gets no code fix and no continuation.
  - **P32-WR-04** (a non-positive control gap crashes the frontier with a `ValueError`; latent,
    since the n8 gap is +0.134325) is **RE-DEFERRED** with target "the milestone that reuses
    `phase32_frontier`".
- **D-15:** **ACTRL-01 stays unticked, as a named limitation of partial exercise** (the developer's
  wording, 2026-09-28).
  - Exercised on real data: the recall floors and `control_gap` came from each leg's own advr
    control (32-07-SUMMARY.md:80, cited by reference).
  - Not exercised: the relearning Z baseline, because admission read MOOT and no relearning leg
    ran.
  - The text **must not** claim the DP-origin refusal fired on real data.
  - It enters the Phase 34 ledger as **NAMED-LIMITATION** with id `ACTRL-01`. Phase 33 records the
    state and does not take the requirement.
- **D-16 (defaults the developer did not contest):**
  - **IN-03** gets a dated continuation note, staged as a ledger row in the Phase 33 SUMMARY. It
    carries the measured evidence: one add `4339f2b`, zero deletes, all 8 published
    `calibration.add_commit` values equal. No pinned file changes.
  - The leg sub-commands mirror Phase 27's `calibrate`, `curve`, `gate` and `structural-proof`.
    Each maps to its RELRN-06..09 id in a module tuple.

### Claude's Discretion
- Module and sub-command names (e.g. `scripts/phase33_admission.py` with `admit` + leg sub-commands),
  as long as the record path is imported from `phase29_prereg`.
- The exact set of gate modules hashed into `module_sha256`, derived from what `admission()` actually
  reaches, never typed from memory. 32-VERIFICATION's `module_sha256` note is the counter-example to
  avoid.
- Where the Phase 34 ledger rows are staged. The ledger file itself belongs to Phase 34, so Phase 33
  may record the rows in its SUMMARY/VERIFICATION for Phase 34 to import.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### The frozen contract Phase 33 calls
- `scripts/phase29_prereg.py` — `admission()` (§9), `SCOPE_RULE` / `relearning_scope()` (§10), `recall_threshold`, `EXPECTED_POINTS`, `V5_RESULT_PATHS` (§4), `NAMED_LIMITATIONS` (§7), the D-09 relearning pins (§8)
- `.planning/phases/29-v5-0-pre-registration-and-carried-debt/29-CONTEXT.md` — D-06..D-10 (the admission contract is frozen in full; Phase 33 only imports and calls it once), D-15 option 2 (no promotion)
- `results/phase32_frontier.json` — the input; write-once and committed
- `tests/test_phase29_prereg.py:109` — the prereg-before-every-v5-result ancestry guard (already covers `results/phase33_*`)

### Phase 27 precedent (pattern, not code to edit)
- `scripts/phase27_relearn.py:131-160` (`_require_admitted`), `:361-412` (`admit`: overwrite then dirty refusal order, pathspec excluding the record) — pinned in `results/phase27_admission.json` `module_sha256`, so do not edit
- `scripts/phase27_prereg.py` — must stay byte-unchanged (ADMIT-01)
- `tests/test_phase27_relearn.py::test_each_leg_refuses_unless_admitted`, `tests/test_phase27_prereg.py::test_the_record_is_pinned_to_the_frontier_both_ways` — the structures D-02 / D-07 follow
- `.planning/REQUIREMENTS.md:574-578` — the RELRN-01..05 traceability rows (the wording shape D-09 follows, minus "apparatus built")
- `.planning/milestones/v4.0-phases/27-*/27-CONTEXT.md` D-05 — the tick precedent

### Carried debt sources
- `.planning/phases/32-replay-bearing-frontier-re-run-and-verdict/32-CONTEXT.md` D-09, D-10 — P31-WR-01 assigned to Phase 33; never fix code that has no consumer
- `.planning/phases/31-mps-cost-probes-and-budget-commitment/31-REVIEW.md` WR-01
- `.planning/phases/32-replay-bearing-frontier-re-run-and-verdict/32-REVIEW.md` — CR-01, WR-01..05, IN-01..07
- `.planning/phases/32-replay-bearing-frontier-re-run-and-verdict/32-SECURITY.md:107-110` — AR-32-02/03 and the reuse condition
- `.planning/phases/32-replay-bearing-frontier-re-run-and-verdict/32-VERIFICATION.md:13` — `git_sha` is the authoritative pin (module_sha256 block incomplete)

### Requirements / roadmap
- `.planning/ROADMAP.md` § Phase 33 (SC1-SC4)
- `.planning/REQUIREMENTS.md:599` (PREREG-02), `:627-635` (ADMIT-01/02, RELRN-06..09)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `phase29_prereg.admission` / `relearning_scope` / `recall_threshold`: the whole decision logic already exists. Phase 33 writes no admission logic.
- `personacore.provenance.refuse_if_dirty`, `git_sha`: the dirty-tree refusal and provenance.
- `phase25_run.atomic_write_json`: the atomic record write used by every prior write-once record (check its import cost; `phase27_relearn` uses it).
- The `_assert_frozen_before` helper in `tests/test_phase29_prereg.py`: ancestry checks.

### Established Patterns
- Write-once record: the overwrite refusal first, the dirty refusal second (pathspec excludes the record), provenance, then one atomic write. Seen in `phase27_relearn.admit`, `phase26_canary.emit` and `phase32_frontier.emit`.
- Every attack leg's first statement is a guard on the COMMITTED record (`git ls-files` conjunct), never a live re-read.
- The review checkpoint emits without committing, the developer says "approved", and Claude commits the file alone (31-06, 32 D-16).
- Planning files are hand-edited with snapshot and diff; `gsd-sdk` mutation handlers are never used.

### Integration Points
- Input: `results/phase32_frontier.json`. Output: `results/phase33_admission.json` (consumed by Phase 34's renderer and ledger).
- Phase 34's `docs/REPORT.md` v5.0 section renders the limitation from the record, so D-08 wording must come from the record, not from prose.

</code_context>

<specifics>
## Specific Ideas

- The developer's rulings came with exact wording requirements. The RELRN rows say
  "NOT SATISFIED — named limitation: admission read MOOT", and must not reuse Phase 27's "apparatus
  never exercised".
- Ledger ids carry a phase prefix (`P31-WR-01`, `P32-WR-01`).
- The single-commit test fails loudly on a shallow clone.

</specifics>

<deferred>
## Deferred Ideas

- **Building the advr relearning apparatus** (the curve, gate, calibrate and structural-proof bodies)
  is deferred to whichever future milestone admits a point. Its prerequisites are P31-WR-01 (the
  artifact location relative to `refuse_if_dirty`) and, if it reuses `phase32_points`, the
  CR-01/WR-01/WR-05 fixes with dated pin continuations.

</deferred>

---

*Phase: 33-admission-and-relearning-on-admitted-points*
*Context gathered: 2026-09-28*
