---
phase: 39-instrument-context-2-2
verified: 2026-10-05T18:30:00Z
status: passed
score: 4/4 roadmap success criteria verified (CTX-01, CTX-02, CTX-03 satisfied; 10/10 plan must-have groups hold, read against the 05-10 orchestrator amendments)
overrides_applied: 0
re_verification: false
---

# Phase 39: Instrument × Context 2×2 Verification Report

**Phase Goal:** The rank/generation disagreement is split into its instrument part and its context part. Both are measured on the same adapters, at the answer anchor and at the full A2 question. (E6: NLL, rank and generation in both contexts, k = 0, 8, 16, 32, 64, 78 and M2.)
**Verified:** 2026-10-05 at HEAD 0c99759. The record is 78d2605, the report 86de12a, the ledger 4268f26, and the prereg was frozen at 9366134.
**Status:** passed
**Re-verification:** No. This is the initial verification.

Method: I did not take any SUMMARY number on trust. I wrote a read-only script that loads `results/phase39_ctx.json` and re-derives everything below through the frozen prereg and the pinned instruments:

- R_a is checked against `phase38_prereg.committed_gate_ranks()`.
- R_q n1 and the median are recomputed from the 27 per-question ranks.
- G_a hits are recomputed from the 48 stored anchor completions through `phase18_extraction.score_records`.
- G_q is checked against `phase39_prereg.committed_a2_counts()`.
- All 96 cells are re-classified through `classify_cell` from those values, which I built myself rather than taking from the record's cells. `class_counts`, `tie_audit` and `baseline_table` are recomputed the same way.
- `approval == approval_block()` is checked.
- The report bytes are compared against `render_report(record)`.

On top of that I ran git ancestry and single-path checks, and the targeted pytest files. I did not run the full suite, any `phase39_ctx.py` run/crosscheck/emit/report command, or MPS. I made no writes outside this file. `git status --porcelain` shows only the pre-existing ` D .claude/scheduled_tasks.lock`.

## Goal Achievement

### Observable Truths (Roadmap SC1-SC4)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | **SC1 / CTX-01:** which of the 216 A2 entries enter the full-context NLL is pre-registered before any scoring. | VERIFIED | `E6_ENTRY_SUBSET = phase35_prereg.fill("e6_entry_subset", ...)` in `scripts/phase39_prereg.py` == `tuple(range(216))`. It is derived and never typed (D-01: all entries). The record's `shape.entries` = 216 indices. The fill landed in 06e3893 (2026-10-04). That is before the first driver code (783b9be), before the rehearsal (after 7b32c41) and before the MPS run (16:15Z 2026-10-05). The prereg is frozen at 9366134. I computed sha256 4355b88024b41463daef9b17285246e74b7577988cd95c01e33d293594858297 at HEAD, and `git diff 9366134 HEAD -- scripts/phase39_prereg.py` is empty. `git merge-base --is-ancestor 9366134 78d2605^` returns true. The Phase 35/36 legs passed (slot ordering, owner fill vs `unit_caps.E6.entries = 216`): 7 passed. |
| 2 | **SC2 / CTX-02:** on the same adapters (k0, k8, k16, k32, k64, k78, M2), NLL and rank are scored at (a) the anchor and (b) the full A2 question, and generation runs in both contexts where it is defined. | VERIFIED | The record has status SCORED, `provenance.run.device = mps`, launch = end SHA 852e6b4 and `head_moved_during_run` False. Readings: k0..k78, M2 and adapter_off, × 8 slots. **(a) anchor:** gate 1 re-scored every committed reference on MPS through the pinned `value_span_nll` and the D-30 copy. The 64/64 ranks equal `committed_gate_ranks()` (my independent check). Copy equality is 448/448 bitwise and `unequal` is []. The IN-02 work-load check is 8/8 equal. **(b) question:** each reading × slot has 27 per-question ranks plus n1, the median and `rank_of_mean_nll`. The CPU cross-check found 0 of 1728 R_q, 0 of 1728 minted and 0 of 64 gate ranks differing, and the suffix sums agree 1728/1728. **Generation:** G_a is new anchor generation, 48 completions per cell, stored. My `score_records` recomputation matched the stored hits in 64/64 cells, and `seed_index = SLOTS.index(slot)` (D-28). G_q comes from the committed K = 48 A2 draws of the same adapters, reused by D-02 (`a2_regenerated_entries = 0`, the budget approval). The SHA-256 is verified and gate 2 re-derived it (passed; the k0 target row is `independent: True` against the phase18 report total). G_q count == the committed count in 64/64 cells. |
| 3 | **SC3 / CTX-03:** the report separates how much of the rank/generation disagreement comes from the instrument and how much from the context. | VERIFIED | `results/phase39_ctx_report.md` has the section `## Instrument share and context share (CTX-03)`. It is split by event (collapse, damage) and group (prefixes, M2, combined), and every count is given "of cells" and "of disagreement cells" with its share. Collapse: 48 cells, 9 disagreement cells. INSTRUMENT_SUFFICIENT 5/9, CONTEXT_SUFFICIENT 0/9, ALREADY_AT_K0 4/9 (G_a is 0/48 at k0 for sibling_name and hometown). Damage: 48 cells, 24 disagreement cells. INSTRUMENT_SUFFICIENT 11/24, CONTEXT_SUFFICIENT 0/24, EITHER 4/24, INTERACTION_ONLY 1/24, UNREACHABLE_AT_SIZE 8/24. M2 has 0 disagreement cells under both events, REVERSE 0, undecided 0. **I re-classified all 96 cells independently, and every cell plus the counts, the tie audit and the baseline match the record exactly.** The report matches `render_report(committed record)` byte for byte, and the record's `scripts/phase39_ctx.py` digest equals the HEAD bytes. All 23 provenance module digests equal HEAD. |
| 4 | **SC4 / CTX-02:** no record exists before the prereg module and its ancestry test are committed, and records are write-once and committed only after Rafael's approved. | VERIFIED | The prereg and `tests/test_phase39_prereg.py` were both first added in d05f18c (2026-10-04). The only `results/phase39_*` commits in any ref are 78d2605 and 86de12a. Each commit holds a single path: 4268f26 = the ledger only, 78d2605 = `results/phase39_ctx.json` only, 86de12a = `results/phase39_ctx_report.md` only. The ledger is an ancestor of the record. The ledger has exactly one start and one end line for `v6/39/E6/ctx`, and the end line names the record. The subjects carry "Rafael approved 2026-10-05", and the SUMMARYs record his "approved" (39-09 T1, 39-10 T2). The ancestry tests passed (`test_phase39_prereg_is_frozen_before_every_phase39_record`, `test_this_test_file_is_first_added_before_every_phase39_record`, `test_records_at_commit_is_true_at_the_first_commit`), as did the emit/report write-once refusal tests. |

**Score:** 4/4 roadmap truths verified.

### Plan must-haves (39-01..39-10), against the amended text

| Plan | Key must-have | Status | Evidence (this session) |
|------|---------------|--------|--------------------------|
| 39-01 | Prereg, fills, A2 pins, D-11/D-26/D-30 arithmetic, NOT_MEASURED | VERIFIED | `approval` in the record == `approval_block()`. Projection 0.7293568082878159 <= stop 0.7424221732238463. Gate NLLs: 512 priced, 448 actual. Minted NLLs: 12096. D-11 is quoted verbatim in the record and the report. `not_measured` = [\|R\| > 8, B1′]. |
| 39-02 | Gate 2, statuses, classifier precedence, class counts, rank summaries | VERIFIED | I read `count_status`, `rank_status`, `disagreement_of`, `_precedence`, `_tally` and `tie_audit` (prereg :1169-1477) against D-14/D-15/D-24/D-25 and rulings e/f/g/j. Damage uses strict `>` with the committed formula. The committed-data oracle is 9 collapse / 24 damage, and the live record reproduces it. |
| 39-03 | Review before the freeze; confirmations in the prereg; no unconfirmed label | VERIFIED | 39-REVIEW.md Resolution records the rulings verbatim. `grep -c "not yet confirmed by Rafael" scripts/phase39_prereg.py` = 0. The fixes are 2c0c300..9366134. |
| 39-04 | D-30 copy bitwise on CPU, anchor ids, draws, question scoring, preflight refusals | VERIFIED | `tests/test_phase39_ctx.py` passed (in 197 passed with the prereg file). On MPS, copy equality was 448/448. |
| 39-05 (amended) | Gate-then-work, write-once sidecars, ledger lines, D-27 pin, AST censuses with the amended callee set | VERIFIED | The ledger has a start and an end line. `rehearsal_disclosure.prereg_changed` is False. The AST census tests passed. |
| 39-06 (amended) | 48 cells per event through `cells(event)`; k0 and adapter_off never a cell; `class_counts` M2 apart; `tie_audit` as the D-33 block; baseline | VERIFIED | My check: no k0 or adapter_off cell in either event. The `baseline` covers all 8 slots and equals `baseline_table`. `drop_formula_audit` equals `tie_audit`: flips [], exact tie [k8, person_name, G_q], class_changes []. |
| 39-07 (amended) | Report renderer with both denominators, D-07/D-17/D-20/D-22/D-28/D-29/D-30 declarations, CPU rehearsal | VERIFIED | The report's Limitations list covers one seed, 1-vs-27, no generation cross-check, B1's two differences, G_a vs G_q, the seed-window overlap, IN-03 and Wilson clustering. The copy sentence reads "448 of 448". The rehearsal (7b32c41) is disclosed with its 7 fix commits. |
| 39-08 (amended) | Review before MPS; every fix committed with its reason; re-rehearsal; one MPS run; IN-02 check | VERIFIED | 39-REVIEW-3 Resolution. The seven fix commits 4f859b3..3590057 touch only `phase39_ctx.py`/tests and are listed in `rehearsal_disclosure.commits`. `work_load_check` is 8/8 equal. Run: 820.6 s. `run_within_stop` and `projection_within_stop` are both True (0.7308777162950072 <= 0.7424221732238463). |
| 39-09 | Ledger first, then the record, alone, after approved | VERIFIED | See SC4. |
| 39-10 | Report from the committed record, alone, after approved; SC1-SC4 by command | VERIFIED | See SC3/SC4. The hand-close of STATE/ROADMAP/REQUIREMENTS is still pending by design (see Info). |

### Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `scripts/phase39_prereg.py` | VERIFIED | 1496 lines. Frozen and sha-matched. The driver and tests import it, and the record embeds its approval block. |
| `scripts/phase39_ctx.py` | VERIFIED | 2270 lines. Its record digest equals HEAD, so the report was rendered by the same code. |
| `tests/test_phase39_prereg.py`, `tests/test_phase39_ctx.py` | VERIFIED | 197 passed in 77 s, with zero skips: the only `pytest.skip` strings are planted probes inside the skip-census tests. |
| `results/phase39_ctx.json` | VERIFIED | SCORED on MPS. Every derived value was re-derived (above). |
| `results/phase39_ctx_report.md` | VERIFIED | Byte-equal to `render_report(record)`. |
| `ledger/v6_mps_ledger.jsonl` | VERIFIED | +2 lines (start/end `v6/39/E6/ctx`), committed alone before the record. |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| phase39_prereg | phase35_prereg | `fill()` as E6_ENTRY_SUBSET / E6_DECOMPOSITION_RULE | WIRED |
| phase39_ctx | phase39_prereg | `cells` / `classify_cell` / `class_counts` / `tie_audit` / `baseline_table` (`_classified`, `_decomposition`) | WIRED: output identical to my independent recomputation |
| phase39_ctx | phase18_extraction | `value_span_nll` (gate), `score_records` (G_a, G_q) | WIRED |
| ledger end line | results/phase39_ctx.json | `record` field | WIRED |
| report | record | `render_report(record)` | WIRED: byte-equal |

Phase 39 changed no file outside its own four modules plus its records and ledger lines (`git diff --stat d05f18c^ HEAD -- scripts src tests results ledger`). The pinned instruments, the budget, `phase36_ledger.py` and `phase36_caps.py` are untouched.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Independent re-derivation and re-classification | scratchpad `v39.py` (read-only) | every PASS; 0 bad blocks of 64; 96 cells identical | PASS |
| Driver and prereg tests | `.venv/bin/pytest tests/test_phase39_prereg.py tests/test_phase39_ctx.py` | 197 passed in 77.12 s | PASS |
| Phase 35/36 legs (ordering, owner fill, launch line) | `.venv/bin/pytest tests/test_phase35_prereg.py tests/test_phase36_caps.py tests/test_phase36_ledger.py -k ...` | 7 passed | PASS |
| Debt markers | grep for TBD/FIXME/XXX/TODO/HACK in the four modules and the report | none | PASS |

Step 7c (probes): no phase-39 probe is declared, so none was run.

### Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
|-------------|--------------|--------|----------|
| CTX-01 | 39-01, 39-03, 39-10 | SATISFIED | SC1 |
| CTX-02 | 39-02, 39-04..39-10 | SATISFIED | SC2, SC4 |
| CTX-03 | 39-01, 39-02, 39-03, 39-06, 39-07, 39-09, 39-10 | SATISFIED | SC3 |

No requirement is orphaned: REQUIREMENTS.md maps only CTX-01..03 to Phase 39. All three are still unticked and marked "Pending" by design, because the orchestrator ticks them by hand after verification. I did not count that as a gap.

### Anti-Patterns Found

None.

### Info (non-blocking)

1. **Carry-forward of the milestone-report notes is recorded where ruled.**
   - The second CPU rehearsal is recorded in the 39-08 SUMMARY, as Rafael ruled ("fica registrado no SUMMARY do 39-08").
   - The 1/48-baseline caveat is recorded verbatim in the 39-09 SUMMARY, with the orchestrator's premise check. I re-measured that check from the record: k0 G_a h is house_number 1, birth_year 1, person_name 20, street 18, cat_name 32, pet_name 45.
   - The 39-10 SUMMARY restates both as v6.0-report carry-forwards.
   - The milestone report itself (Phase 45, RPT-07/08) does not exist yet. No anchor outside the phase-39 SUMMARYs points at these two notes: they are not in STATE.md and there is no pending todo. Suggestion: name both in STATE.md during the hand-close so Phase 45 picks them up.
2. **The phase hand-close is still pending.** The 39-10 SUMMARY's Task 4 refers to "the close commit". HEAD 0c99759 only adds the SUMMARY, and STATE/ROADMAP/REQUIREMENTS are not yet updated (STATE still reads "Phase 39 PLANNED"). This is the expected next orchestrator step.
3. **The interpretation of the result rests on the anchor baseline.** Of the 24 damage disagreement cells, 8 are UNREACHABLE_AT_SIZE because G_a is 0/48 at k0 for sibling_name and hometown. Four of the 11 INSTRUMENT_SUFFICIENT damage cells rest on a 1/48 k0 baseline. The record and report state this per cell (k0 values beside every relation), and Rafael has ruled the caveat into the milestone report. This is not a gap in this phase.

### Human Verification Required

None. Rafael read and approved both the record (39-09) and the report (39-10).

### Gaps Summary

None. The phase goal is achieved:

- E6 scored NLL and rank at the anchor (gate 1, bitwise) and under the full A2 question (27 ranks per cell, cross-checked on CPU) on all seven CTX-02 adapters plus adapter-off.
- Anchor generation was run fresh. A2 generation was reused from the same adapters' committed draws, re-derived in gate 2.
- The disagreement is decomposed by the frozen rule into instrument and context shares for collapse and damage. Every number re-derives from the committed record.

---

_Verified: 2026-10-05_
_Verifier: Claude (gsd-verifier)_
