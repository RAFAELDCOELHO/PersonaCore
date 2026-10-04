---
phase: 38-exposure-rank-at-larger-minted-sets
verified: 2026-10-04T20:30:00Z
status: passed
score: 4/4 roadmap success criteria verified (RANK-01, RANK-02, RANK-03 satisfied; 10/10 plan must-have groups hold)
overrides_applied: 0
re_verification: false
---

# Phase 38: Exposure Rank at Larger Minted Sets Verification Report

**Phase Goal:** The exposure rank of the committed ablation prefixes is re-measured against larger same-slot sets minted by a pre-registered rule, and the report says whether the rank moves before generation collapses.
**Verified:** 2026-10-04 at HEAD 8216d11 (records at 7357577 / d6984f4 / 7043e9c, ledger 8ae5994)
**Status:** passed
**Re-verification:** No. This is the initial verification.

Method: I did not take any SUMMARY number on trust. Every value below was re-derived by a command run in this session. The commands were: an independent recomputation from the NLL sidecars, which uses none of the driver code; an independent read of the 64 committed gate ranks from the five source records; a re-mint in verify mode; a byte-compare of the report against render_report(record); git ancestry checks; and the targeted pytest files. I did not touch MPS, the ledger, results/ or data/. The re-mint is read-only when the record exists, and `git status --porcelain` afterwards showed only the pre-existing ` D .claude/scheduled_tasks.lock`.

## Goal Achievement

### Observable Truths (Roadmap SC1-SC4)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | **SC1 / RANK-01:** the minting rule is pre-registered. Numeric slots are enumerated. Name and place slots are minted by rule and cleared against the base as in Phase 17. Set sizes (up to 512, as far as minting allows) are declared before any scoring. | VERIFIED | The rule lives in `scripts/phase38_prereg.py` (the `e5_minting_rule` entry plus the executable `mint_all`). Its last commit d33986c strictly precedes the minting record 7357577 (`merge-base --is-ancestor`, strict). **I re-minted in verify mode** (`.venv/bin/python scripts/phase38_mint.py`), exit 0, output "MINTING VERIFIED (record re-minted and matched)", stop_draw 58195. The six name/place slots hold 2125/2048/2113/4951/2087/2102 values, all >= 2048. birth_year holds 219 (7 taught years excluded) and house_number 8768 (= 9000 - 13 - 219), both enumerated and Fisher-Yates shuffled. Phase 17 clearance: `phase17_filter_proof.passed = true` on 3796 values with all four `phase17_personas.filter_*` functions, and the `clearance` rejection count is published per slot (pet_name 1, others 0). Sizes are filled in `scripts/phase38_sizes_prereg.py` (`E5_SET_SIZES = phase35_prereg.fill(...)`), giving 512 for seven slots and 220 for birth_year. The values are read via `max_set_size(n_cleared)` and never typed. Order: minting 7357577 < sizes b2416ee < first driver code d379fd1 < rehearsal 91553d9 < rank record d6984f4, so the sizes were declared before any scoring. |
| 2 | **SC2 / RANK-02:** k = 0, 8, 16, 32, 64, 78 are re-scored with `ans1` and mean reduction, reconstructed from `persona_adapter.pt` and the committed `ordered_prefix` with SHA-256 verified. The report states whether the rank moves before generation collapses, against the committed A2 counts. | VERIFIED | Frame and reduction: the driver calls `phase19_erasure.value_span_nll_mean`, which reads `phase18_extraction.ADMISSIBLE_NLL_FRAME = "ans1"` and `ADMISSIBLE_NLL_REDUCTION = "mean"`. Reconstruction: prefix-k models come from `phase36_probe.adapted_model` (`load_adapted_model` + `ablate_components(e1_components()[:k])`). I recomputed the digests myself. sha256(checkpoints/persona_adapter.pt) = 226f2ae5… equals phase19_collateral_curve `adapter_in_sha256`. The components digest of the committed 78-entry `ordered_prefix` = a7cc2271… equals phase36_probe_e1 `configuration.components_sha256`. The M2 adapter 22e66552… equals phase19_retrain_scores. As an exactness check, all 64 gate cells reproduce the committed rank with `abs_nll_diff = 0.0`. Report: `results/phase38_rank_report.md` has "## Did the rank move before generation collapsed?" with 64 rows (8 slots x 4 sizes x 2 events). Each row gives the first k and BEFORE/SAME/AFTER/NEVER against first collapse and first damage, and names "never collapsed within the grid" (cat_name, birth_year, house_number). The A2 counts table comes from the committed records. |
| 3 | **SC3 / RANK-03:** `reference_set_for` and `phase18_extraction.py` are untouched. The larger sets live in a new module that imports them. | VERIFIED | `git diff --stat 255380f^ HEAD -- scripts/ src/` lists only the four new `scripts/phase38_*.py` files. The last commit to phase18_extraction.py is 99716e0 (Phase 18). The record's `module_sha256` for phase18_extraction is d2b44806… at launch and at write. `test_instruments_unchanged_byte_for_byte` passed. `scripts/phase38_rank.py` imports `phase18_extraction` and calls `reference_set_for(slot)` (lines 403, 549, 659) for the gate. No phase38 module defines `exposure_rank`, `_rank_of`, `reference_set_for` or `value_span_nll*`. My grep and the RANK-03 AST tests agree. The minted sets overlap the committed reference sets in 0 values for every slot (measured). |
| 4 | **SC4:** no record exists before the pre-registration module and its ancestry test are committed. Records are write-once and committed only after Rafael writes approved. | VERIFIED | The prereg and its test were first added at 1a988c3; the ancestry guard landed at aff8da7. Both precede 7357577 (the first results/phase38_* file). Each record has exactly one commit and is the only file in it: 7357577 = minting.json, d6984f4 = rank.json, 7043e9c = rank_report.md. The ledger (8ae5994, ledger only) precedes the rank record. All three commit subjects carry "Rafael approved". Write-once refusals are covered by tests (existing record, sidecar digest, dirty tree, partial shape) and passed. `test_phase38_prereg_is_frozen_before_every_phase38_record` and the Phase 35 leg tests passed. |

**Score:** 4/4 roadmap truths verified.

### Plan must-haves (38-01..38-10), regression of key claims

| Plan | Key must-have | Status | Evidence (this session) |
|------|---------------|--------|--------------------------|
| 38-01 | D-12/D-28/D-29 definitions, D-13/D-14 A2 readers, D-18 gate, D-20 digest, D-21/D-22/D-23 arithmetic | VERIFIED | `APPROVED_E5_PREFIXES = 8`, projection 0.467956566879681 <= stop 0.5418565110509128. The A2 first collapse and first damage were recomputed independently from the record's counts and match all 8 slots. person_name k = 8 drops by 8/27 = margin, so it is not damaged (strict >). |
| 38-02 | Executable rule; seed `phase35_prereg.seed_list()[0]` by reference | VERIFIED | Line 1226 reads `seed = phase35_prereg.seed_list()[0]` (record seed 1337). The re-mint reproduces the record exactly. |
| 38-03 | One CPU mint command, write-once, then verify mode | VERIFIED | Verify mode ran (above). `tests/test_phase38_mint.py` passed. |
| 38-04 | Review before the freeze, >= 2048 per name slot, approval, single-path commit | VERIFIED | 38-REVIEW: WR-01 fixed in d33986c before 7357577. WR-02..04 and IN-01..04 were ruled known limitations. |
| 38-05 | Sizes from the record, legs (a)/(b), caps without prefixes | VERIFIED (with a recorded deviation) | Truth 4 ("imports torch-free") was a false premise. Importing the file puts `torch` in `sys.modules` (measured True) through its caps call. This was recorded in 38-05-SUMMARY, and option 1 was chosen by the orchestrator. The purpose of the truth still holds: `test_phase36_caps.py` exec's the file and passes. |
| 38-06 | Preflight refusals, D-18 gate before minted scoring, one `value_span_nll_mean` call per value | VERIFIED | `gate.passed = true`. 64/64 gate ranks equal the committed ranks, which I read straight from phase19_arm_erased (k0 pre_erasure, k78), erasure_kstar_summary (k8..k64), phase19_arm_retrain (M2) and phase18_arm_adapter-off. |
| 38-07 | crosscheck, build_record, emit, render_report, D-33 audit, D-34 disclosure | VERIFIED | Independent recomputation: all 256 (reading, slot, size) ranks and bits, plus every event flag, first k, rank_0 and relation, match the record. The sidecar SHA-256s (8 NLL + cpu + gate + run) equal `provenance.sidecar_sha256`, and the minted lists equal `cleared[:size-1]`. 0 differences. |
| 38-08 | Second review, preflight, MPS run, crosscheck, emit | VERIFIED | Record: device mps, `head_moved_during_run` false, launch sha = end sha = ccd5d7e. CPU cross-check: 0/256 cells and 0/64 gate cells differ. Second-review DR-01..03 and DI-01..05 were ruled known limitations ("nothing to fix"). |
| 38-09 | Ledger first, then record; full suite green | VERIFIED | Ledger lines 13-14: start, then end with `record: results/phase38_rank.json`. `seconds: null` follows the same convention as the Phase 36/37 lines. |
| 38-10 | Report rendered from the committed record, byte-equal, approved, alone | VERIFIED | `render_report(json.load(results/phase38_rank.json)) == results/phase38_rank_report.md` → True (284 lines). |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/phase38_prereg.py` | Rule, definitions, gate/A2 readers | VERIFIED | 1271 lines. 16 ENTRIES. Frozen at d33986c, before the minting record. |
| `scripts/phase38_mint.py` | CPU mint + verify | VERIFIED | Re-mint reproduces the record. |
| `scripts/phase38_sizes_prereg.py` | e5_set_sizes fill | VERIFIED | One commit, b2416ee (frozen). |
| `scripts/phase38_rank.py` | E5 driver | VERIFIED | Last edit 1e68330 (disclosed under D-34). Its bytes match the record's `module_sha256` (19ed9476…). |
| `results/phase38_minting.json` | Write-once minting record | VERIFIED | Committed alone in 7357577. sha256 b17b8c01… matches the rank record. |
| `results/phase38_rank.json` | Write-once rank record | VERIFIED | Committed alone in d6984f4. status SCORED. |
| `results/phase38_rank_report.md` | Report | VERIFIED | Committed alone in 7043e9c. All sections are present (Status, Approval, Gate, A2, D-33, curves, relation, D-27, D-19, D-34, D-36, Provenance). |
| `ledger/v6_mps_ledger.jsonl` | E5 start/end | VERIFIED | 8ae5994 |
| `tests/test_phase38_{prereg,mint,sizes_prereg,rank}.py` | Guards | VERIFIED | All pass (below). |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| phase38_rank.py | phase18_extraction | `reference_set_for(slot)` in the gate | WIRED |
| phase38_rank.py | phase19_erasure | `value_span_nll_mean(...)` (line 390) | WIRED |
| phase38_rank.py | phase36_probe | `adapted_model(device, k)` / `e1_components()` | WIRED |
| phase38_rank.py | phase38_prereg | `rank_in_prefix`, `relation`, `a2_counts`, `committed_gate_ranks` | WIRED. The independent recompute agrees. |
| phase38_sizes_prereg.py | results/phase38_minting.json | `max_set_size(slots[*].n_cleared)` with a drift check | WIRED |
| phase38_rank.py `scoring_plan` | phase38_sizes_prereg | `E5_SET_SIZES[slot]` (lazy import) | WIRED. The sidecars hold exactly size - 1 minted values. |
| ledger end line | results/phase38_rank.json | `record` field | WIRED |
| report | rank record | `render_report(record)` | WIRED (byte-equal) |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data | Status |
|----------|------|--------|-----------|--------|
| rank record curves | per-reading NLLs | data/phase38_rank_nll_*.json (digests pinned in the record) | Yes. 8 readings x 8 slots, NLL per minted value. | FLOWING |
| relation table | A2 counts | phase18_arm_adapter-on + erasure_kstar_summary + phase19_target_scores | Yes. The first collapse and first damage I recomputed match. | FLOWING |
| gate table | committed ranks | five committed records | Yes. 64/64 match when read independently. | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Minting reproduces the record | `.venv/bin/python scripts/phase38_mint.py` | MINTING VERIFIED, EXIT=0, tree unchanged | PASS |
| Record arithmetic is independent of the driver | scratchpad `v38_recompute.py` (sidecars + minting record only) | 256 ranks checked, BAD [] (0) | PASS |
| Report is byte-equal to its renderer | `render_report(record) == report` | True | PASS |
| Gate ranks against the source records | direct JSON read of 5 records | 64/64 equal | PASS |
| Targeted tests | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase38_{prereg,mint,sizes_prereg,rank}.py tests/test_phase21_sc5.py::test_instruments_unchanged_byte_for_byte tests/test_phase36_caps.py tests/test_phase36_ledger.py tests/test_phase35_prereg.py` | 344 passed in 85.95 s, EXIT=0 | PASS |
| Full suite (not re-run, per instruction) | log `suite38_10_post.log` at 7043e9c | 4103 passed, 4 skipped, EXIT=0. HEAD 8216d11 adds only a SUMMARY. | PASS (cited) |

### Probe Execution

Not applicable. No `scripts/*/tests/probe-*.sh` is declared by the Phase 38 plans. The phase's runnable checks are the spot-checks above.

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| RANK-01 | 38-01..05 | Minting rule pre-registered; sizes declared before scoring | SATISFIED | SC1 row |
| RANK-02 | 38-01, 06..10 | Prefixes re-scored with ans1/mean, reconstruction with SHA-256 verified, report on move-before-collapse against A2 | SATISFIED | SC2 row |
| RANK-03 | 38-06, 38-10 | reference_set_for / phase18_extraction untouched; new module imports them | SATISFIED | SC3 row |

No requirement is orphaned. REQUIREMENTS.md maps exactly RANK-01..03 to Phase 38, and every plan's `requirements:` field draws only on these three. The REQUIREMENTS.md checkboxes are left unticked for the orchestrator.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | — | No TBD/FIXME/XXX/TODO/HACK in the scripts/phase38_*.py or tests/test_phase38_*.py files | — | — |
| tests/test_phase38_*.py | 244/417/767/1599 | The string `pytest.skip("x")` appears | Info | These are planted fixtures inside the zero-skip guard tests, not real skips. |

Known limitations ruled by Rafael (38-REVIEW: WR-02..04, IN-01..04, DR-01..03, DI-01..05) are not gaps. None of them changes a value in the committed records, which the independent recomputation and the re-mint confirm.

### Regression vs Phase 37

Phase 38 touched no file outside `scripts/phase38_*`, `tests/test_phase38_*`, `results/phase38_*` and two appended ledger lines (`git diff --stat 255380f^ HEAD`). Phase 37's records, drivers and tests are byte-unchanged, and the full suite at 7043e9c is green.

### Human Verification Required

None. The judgement calls in this phase (the minting record, the rank record and the report) each already carry Rafael's "approved" in their commit subjects (7357577, d6984f4, 7043e9c). No unverified visual or interactive behaviour remains.

### Gaps Summary

There are no gaps. The phase goal holds in the codebase and the committed records:

- The larger sets are minted by a frozen, pre-registered rule, and anyone can reproduce them with one CPU command (re-mint verified).
- The six ablation prefixes, plus M2 and adapter-off, were re-scored on exactly reconstructed weights. The gate is 64/64 with zero NLL difference, and the CPU cross-check differs in 0 of 256 cells.
- The published report answers per slot and size whether the rank moved before collapse. The rank does move at sizes >= 32 in several slots, and before collapse for sibling_name 128/512, hometown 128/512 and birth_year 32/128/220. It never leaves the top eighth.

All of these answers were re-derived independently of the driver code.

One deviation is recorded and does not break the goal: 38-05's truth 4 ("sizes file imports torch-free") was a false premise. Importing the file does load torch, via `phase36_caps`. The orchestrator chose option 1, and the purpose of the truth (the owner-fill caps test exec's the file) still passes.

---

_Verified: 2026-10-04_
_Verifier: Claude (gsd-verifier)_
