---
phase: 36-mps-cost-probes-and-budget-commitment
verified: 2026-10-03T00:14:31Z
status: passed
score: 4/4 roadmap success criteria verified; 2/2 requirements satisfied (COST-01, COST-02)
overrides_applied: 0
---

# Phase 36: MPS Cost Probes and Budget Commitment — Verification Report

**Phase goal:** Every MPS front is priced by a measured probe on the M3, and the v6.0 budget and
its stop line are committed from those probes inside Rafael's 90 h MPS ceiling, or the work halts
and the cut options go to Rafael.
**Verified at:** HEAD 2b8dd82 (the budget record was written at 9a5718a)
**Status:** passed
**Re-verification:** No, this is the initial verification.

Every number below comes from a committed file or a command run during this verification. None is
taken from a SUMMARY alone. Tests run here: `tests/test_phase36_{prereg,caps,budget,ledger}.py`
157 passed; `tests/test_phase36_probe.py` 138 passed; `tests/test_phase35_prereg.py -k
"census or fill_file or ordering or budget"` 11 passed. I did not re-run the full suite. The
orchestrator's run at e72c17a (3782 passed, 4 skipped, EXIT=0) is the only full-suite evidence.
Nothing ran on MPS.

## Goal Achievement

### Roadmap success criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Every MPS front is priced by an M3 probe with its wall-clock on record (E1 exact reading at K=16/48 with fixed and per-draw costs split; M2 retrain plus measurement; one DP config at the longest T; minting-clearance and E5 scoring sample; anchor generation). E1 is priced under ERASE-07. The Phase 31 probe is recorded beside E1 and never extrapolated from (COST-01) | VERIFIED | `results/phase36_probe_{e1,e2,e3,e5,e6}.json` are tracked; each has `device` mps, `reused` False, `gates_nothing` True and repetitions 2/2/2/8/8. **E1:** config A2, `questions` 216, K 48, k16 16, k 78, seed 1337, `pet_name`, greedy. Two runs: totals 3935.18 / 3989.45 s; `fixed_seconds` 177.20 / 179.09 s kept separate (D-18); `draw_seconds` 10368 each; `k16_seconds` 1422.45 / 1437.67 s. **E2:** `train_reps` plus `a2_pass`. **E3:** `t_step_budget` plus `t_max_steps`. **E5:** `clearance` plus `scoring`. **E6:** anchor draws. The E1 formula is `cells x (ordering + checkpoints_per_cell x e1_k16 + k48_confirms x e1_k48) + calibrations x calibration`, which is the ERASE-07 grid shape. `beside_never_extrapolated` = `results/phase31_probe_point.json` with sha256 27c5bdbe…, matching the file (`shasum`). `unit_prices` never reads it, and `comparisons()` skips the row (`probe_field is None`, phase36_budget.py:329) |
| 2 | The budget and stop line are committed from the probe records before the first measured point, inside 90 h, probes included (COST-02) | VERIFIED | `results/phase36_budget.json`: `total_hours` 77.72433149898184, which equals `math.fsum(front_hours)` (I checked this myself). `stop_line_hours` 90 = min(1.5 x 77.72, 90). `e2_seed_count` 5. `front_hours` keys equal `V6_MPS_FRONTS`. `probes` 3.660042732777778 h = 13176.153838 s, which matches `phase36_ledger.py report` `closed_seconds_by_front.probes`. A fresh `committed_derive(...)` from the committed probe blobs plus the fill file's RULING gives the same `front_hours` and `unit_caps`. `V6_BUDGET_AND_STOP_LINE` equals the record. All 17 `sources` sha256 match the HEAD blobs. All 4 `module_sha256` match the working files. `phase35_prereg._budget_record` accepts the record, and `phase36_caps.committed_budget()` accepts it. No `results/phase37_*` record exists, and `git log` since 2026-10-02 touched no `results/phase19_*`/`phase37_*` file |
| 3 | If the fronts do not fit, the work halts and the cut options go to Rafael; nothing is cut unilaterally (COST-02) | VERIFIED | `phase36_budget.py dry` at the defaults, run during this verification and writing nothing: total 97.18944655386002, `stop_line_hours` null, `HALT: 7.189 h over the 90 h ceiling`. The cut table comes out in D-15 order: e4_reserve, e6_anchor_adapters, e2_seeds_to_3 ("never below, D-14"), e3_whole, e1_checkpoints, r1b, e1_core. The record has `cuts_applied` {}, S 5, E4 points 3, E3 recipes 4 / batch 8, E1 checkpoints_per_cell 5. The final numbers come from Rafael's ruling: a pre-registered price alternative plus a reuse cap. No row was cut. See ruling (d) |
| 4 | No record exists before the prereg module and its ancestry test are committed; records are write-once and committed only after Rafael's approved (COST-01, COST-02) | VERIFIED | `scripts/phase36_prereg.py` was committed at 81c75d3 (10:53) and the ancestry test at 9f75933 (10:55). The first `results/phase36_*` commit is 893b3c0 (19:29). `test_phase36_prereg_is_frozen_before_every_phase36_record` PASSED, including its natural-RED leg. `phase36_prereg.py` is unchanged since 81c75d3. Both emits refuse to overwrite (budget `emit` at phase36_budget.py:1070; probe write-once covered in the 138 green probe tests). The probe records were committed without a separate approved, under D-16, where Rafael pre-authorised the commits listed in 36-07-PLAN frontmatter. The budget record was committed only after his approved (see (b)) |

**Score:** 4/4

### Rulings requested by the orchestrator

**(a) Ordering. VERIFIED.** `git log --reverse` shows 81c75d3 (prereg) and 9f75933 (ancestry
test) before f7b9962 (ledger, outside `results/`) and 893b3c0 (the first `results/phase36_*`). The
ancestry test passes at HEAD.

**(b) Commit shape. VERIFIED.** Each of the six D-16 commits contains exactly one path, and they
form a straight chain on 877b92b:

- f7b9962 `ledger/v6_mps_ledger.jsonl` (the ledger goes first)
- 893b3c0 e5
- 987c86f e6
- d389b53 e3
- 26b6ab0 e2
- 0d59b6d e1

These are exactly the six paths listed in advance in the 36-07-PLAN frontmatter. The fill file
`scripts/phase36_budget_prereg.py` has exactly one commit (9a5718a), a single path.
`git rev-parse 6b57231^` = 9a5718a, so the fill file commit is the parent of the budget commit.
6b57231 is a single path.

**(c) Recompute. VERIFIED.** See criterion 2. The record recomputes from the committed probe records
through `phase36_budget.committed_derive` and equals the fill file's `V6_BUDGET_AND_STOP_LINE`.
`total_hours` == fsum == 77.724 ≤ 90, and `stop_line_hours` = 90. The 25% table in the record has
seven gated rows, all with `exceeds` False. The largest gated row is e3_t800_linearity at 6.45%;
r1b_e1_k48 is 4.37% / 3.05% against 4115.04 s = 68.584 min × 60. So `divergences_investigated` {}
is correct. Spot check of E6: 7 × (0.6377 + 0 + 224 × 8 × 0.046742) + 7 × 8 × 48 × 0.443086 =
1781.8 s = 0.4949 h, which matches.

**(d) The HALT, Rafael's ruling and commit 84af553. VERIFIED, consistent with D-09 and COST-02.**

- **The defaults halted.** They gave 97.19 h, confirmed by the live dry run. No cut was applied:
  `cuts_applied` is {} and every unit cap is at its D-09 proposal except the one Rafael ruled.
- **Item 1 (`spread_scaled`) is a pre-registered alternative.** `high_bound_rule.ruling_alternatives.single_run_draw_loop
  = ("within_run", "spread_scaled")` was already in 81c75d3, before any record. The alternative
  replaces exactly `e2_a2_pass_high` and `e3_score_high` (phase36_budget.py:460-465), which are
  the two prices Rafael named.
- **Item 2 (E6 reuse) is a resource decision of Rafael's, not a cut.** No scientific question is
  dropped: the A2-context readings for the seven adapters already exist. His precondition holds.
  I measured it myself: all seven records are tracked and clean, their sha256 match the cap-ruling
  text, and each holds the same 216 A2 entries (identical family/slot/fact_id/prefix/seed_index
  keys) × 48 completions at `config.k` 48, seed 1337. `phase18_arm_adapter-on.json` has 216 A2 rows
  among its 976.
- **84af553 is a mechanism change, not a rule change.** D-09 leaves the cap mechanism to the
  planner. The commit adds the field `E6.a2_regenerated_entries`.
  - Its default is `entries` (priced in full).
  - `_prove_caps` refuses a value above `entries`.
  - `_prove_caps` also refuses any value below `entries` unless `cap_rulings['E6.a2_regenerated_entries']`
    is present.
  - The probe records do not pin `phase36_budget.py` or `phase36_caps.py`. Their pinned modules
    are unchanged since the run sha 877b92b. The budget record pins the post-change versions.
  - `phase35_prereg.py` and `phase36_prereg.py` were not touched.
- **Tests.** `test_derive_cap_ruling_lowers_e6_a2_regenerated_entries` covers three legs: refusal
  without the ruling, acceptance with it (exact E6 hours), and refusal above entries. All three
  are green. Owner-side enforcement goes through the generic `check_unit_caps`. I ran it:
  `a2_regenerated_entries=0` passes, and `=1` refuses with "exceeds the committed cap 0 … needs
  Rafael's approved".
- **Approved text.** `RULING['approved']` matches the 36-08-SUMMARY quote character for character,
  and the record's `approved` equals the fill file's. Caveat (Info): the fill file's `cap_rulings`
  text is a structured restatement of item 2 with the SHA list added. It is not Rafael's words
  verbatim, and item 1 is recorded only as a key. His full ruling is verbatim only in
  36-08-SUMMARY, so the fill file docstring's word "verbatim" overstates it for the rulings
  (the approved reply really is verbatim).

**(e) D-01 / D-18 readings. VERIFIED.**

- A recursive key scan of the five records found only timing keys: `score_*_seconds`/draw counts in
  E3, the `module_sha256` names, and the Phase 31 beside-stage seconds. The same scan found no
  reading-like keys in the five `data/probe36_*_run.json` sidecars, and the ledger keys are
  {event, flag, front, phase, record, ruling, run_id, seconds, stop, utc}.
- `find data -name 'probe36*'` shows no `*_rep*_arm.json`, so the pin draw files are absent.
- The pattern `[0-9]+/[0-9]+ = |per_fact|hits|recall=|rank=` matches 0 lines in `logs/phase36_probe.out`
  (6 lines) and in `logs/phase36_probe.err` (0 lines).
- The training `run.csv` files under `data/` carry train/val loss. That is a training-loop log of
  already-published configurations, not a recall reading, and it is gitignored.

**(f) IN-01 / IN-02. Known limitations, not gaps.**

- **IN-01** (`PINNED_MODULES` omits phase16/17/25_record/src modules). `git diff 877b92b HEAD -- scripts/
  src/` touches only `phase36_budget.py`, `phase36_budget_prereg.py` and `phase36_caps.py`. So no
  unpinned module changed between the probe run (all five sidecars `run_git_sha` 877b92b) and
  emit, and the realised risk to these five records is nil. Re-probes are refused once a record
  exists (CR-01). This would matter only if the driver were reused for a fresh probe; fix it then.
- **IN-02** (plist comment says bootstrap/kickstart/bootout, the 36-07 plan says load/start/unload).
  This is cosmetic, the run is over, and both verb sets work.

**(g) Phase 31 beside E1. VERIFIED.** `beside_never_extrapolated` carries the path, sha256 (it
matches), `stage_seconds` {train, draw, measure, recall, score} and `total_seconds` 7422.87. No price
or comparison consumes it.

### Required artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `scripts/phase36_prereg.py` | VERIFIED | 17 four-field entries, each kind derived or preference. Covers every D-17 item (0.25 tolerance, T ≤ 800, E4 3 points, the 1.5 factors, the projection rule, S ≥ 3, cut_order) plus D-19 `e4_first_point_check` and the Q5/calibration price sources |
| `scripts/phase36_caps.py` | VERIFIED | `CAP_FIELDS`, `check_unit_caps`, `owner_overruns`, `committed_budget` |
| `scripts/phase36_ledger.py` + `ledger/v6_mps_ledger.jsonl` | VERIFIED | 10 lines (5 start/end pairs, no lost runs). `require_launch` for R1b/E1/E6 reads the committed budget and passes, with spent probes 13176.153838 s |
| `scripts/phase36_probe.py` + 5 probe records | VERIFIED | See criterion 1 and (e) |
| `scripts/phase36_budget.py` | VERIFIED | The dry run reproduces the HALT. `emit` re-derives and refuses a mismatch with the fill file |
| `scripts/phase36_budget_prereg.py` | VERIFIED | The only `fill("v6_budget_and_stop_line", ...)` site. Single commit |
| `results/phase36_budget.json` | VERIFIED | See (c) |
| `artifacts/com.personacore.phase36.probe.plist` | VERIFIED | Present. RunAtLoad and KeepAlive are false per its comment |

### Key links

| From | To | Status | Details |
|------|----|--------|---------|
| probe records | budget | WIRED | `probe_record_paths` reads the HEAD blobs, and `sources` sha256 match |
| ledger | probes front | WIRED | 3.660042732777778 h equals the ledger report |
| budget | `phase35_prereg._budget_record` / `fill` | WIRED | Accepted. Census and ordering legs green (11) |
| budget | `phase36_caps.check_unit_caps` / `phase36_ledger.require_launch` | WIRED | Live calls pass and refuse as expected |

### Requirements coverage

| Requirement | Plans | Status | Evidence |
|-------------|-------|--------|----------|
| COST-01 | 36-01, 36-03, 36-04, 36-05, 36-07 | SATISFIED | Criteria 1 and 4, (a), (e), (g) |
| COST-02 | 36-02, 36-04, 36-06, 36-08 | SATISFIED | Criteria 2, 3 and 4, (b), (c), (d) |

REQUIREMENTS.md maps only COST-01 and COST-02 to Phase 36 (rows :818-819), so no requirement is
orphaned. Every plan's `requirements:` field is a subset of {COST-01, COST-02}.

### Anti-patterns

`grep TBD|FIXME|XXX` over `scripts/phase36_*.py` and `tests/test_phase36_*.py` finds nothing, so
there are no debt-marker blockers.

### Behavioral spot-checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Defaults halt with the D-15 cut table | `phase36_budget.py dry` | total 97.189, HALT 7.189 h, 7 rows in order; tree unchanged | PASS |
| Budget recomputes | `committed_derive` + fill RULING | equal front_hours/caps | PASS |
| Cap refuses over-run | `check_unit_caps("E6", a2_regenerated_entries=1)` | SystemExit "exceeds the committed cap 0" | PASS |
| Ledger seconds read by script | `phase36_ledger.py report` | probes 13176.153838 s | PASS |
| Ancestry | `pytest -k frozen_before` | 1 passed | PASS |

### Probe execution (Step 7c)

There are no `scripts/*/tests/probe-*.sh` probes in this repo. The phase's "probes" are the M3
timing runs, which I verified through their committed records and did not re-run (the MPS
prohibition).

### Info / carry-forward (non-blocking)

1. **Phase 39 must call the new cap itself.** `owner_overruns` counts only `entries` for
   `e6_entry_subset` (`counts_for`, phase36_caps.py:196), so a Phase 39 fill that regenerates A2
   entries is not caught by the automatic owner scan. Phase 39 must call
   `check_unit_caps("E6", a2_regenerated_entries=N)` and pause rather than regenerate. This is
   recorded in the 36-08-SUMMARY reminder and in the cap-ruling text.
2. **Some sub-stage prices are read from records, not probed.** The E1 ordering (Q5), the E1
   calibration and the E4 canary scoring (D-19) come from historical records and are labelled
   "NOT re-measured" in `formula`. D-19 is Rafael's own ruling. Q5 and the calibration price were
   surfaced in the dry run and covered by his approved ("total e frentes como na tabela do dry").
3. **The probe LaunchAgent is still loaded.** `com.personacore.phase36.probe` shows PID `-` and
   status 0. RunAtLoad and KeepAlive are false, so it cannot relaunch, but Rafael may want to
   `launchctl bootout` it.
4. **`36-VALIDATION.md` is unsigned.** It still reads `status: draft` and `nyquist_compliant: false`.
5. **SUMMARY inaccuracies.** 36-07-SUMMARY says the err log "holds only ledger-report lines", but
   it has 0 lines. The fill file docstring's "verbatim" applies to `approved` only (see (d)).

### Human verification required

None. Rafael's ruling and approval were gathered at the 36-08 checkpoint, and their recorded text
is consistent across the fill file, the record and the SUMMARY.

### Gaps summary

No gaps. All five probes are on record from the M3. The defaults halted at 97.19 h with the cut
table in D-15 order. The committed budget, 77.724 h with a 90 h stop line and S = 5, follows from a
pre-registered price alternative plus Rafael's reuse cap, with no front cut. It recomputes exactly
from the committed records and was committed in the required order after his approved.

---

_Verified: 2026-10-03T00:14:31Z_
_Verifier: Claude (gsd-verifier)_
