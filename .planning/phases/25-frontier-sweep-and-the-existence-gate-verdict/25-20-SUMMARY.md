---
phase: 25
plan: 20
subsystem: phase-close
tags: [D-13, D-37, D-40, D-43, SS-O1, CTRL-01, CTRL-02, FRONT-01, FRONT-04, ADVT-01, RPT-02, revert, close-guard]
requires:
  - results/phase25_frontier.json (4030d0e, read only)
  - results/phase25_promotion.json, results/phase25_recall.json, results/phase25_interior_log.json
  - scripts/phase25_venue.py (PMSET_REVERT, prove_reverted, read_assertions)
  - scripts/phase25_prereg.py (CANARY_RESERVATIONS, PUBLICATION_OBLIGATION, GIT_SURFACE_EXCEPTION)
  - the Task 1 operator transcript (2026-09-09)
provides:
  - results/phase25_operational_note.md §13 (the close)
  - .planning/REQUIREMENTS.md — eight evidenced ticks, two *(continued)* rows
  - .planning/ROADMAP.md — 25-19/25-20 ticked, the phase-status row filled
  - tests/test_phase25_close.py (26 tests)
affects: [phase-verification, phase-complete, Phase 26 (audit target dp_n8_sigma0p000000), Phase 28 (PUBLICATION_OBLIGATION)]
tech-stack:
  added: []
  patterns:
    - "a privileged system change is reverted from a committed argv tuple printed from the module and verified by a committed function — never from memory"
    - "a diff audit over planning files classifies every deleted line into one of two enumerated buckets (toggle / declared modification) against a pinned pre-edit commit, with its RED probes kept as tests"
    - "a requirement tick names the artifact field, the guard test and the plan; superseded phrasings stay visible behind SUPERSEDED: and are checked positionally"
decisions:
  - "The two-bucket counts are MEASURED at the pre-edit commit df100ca (5 toggles + 4 declared rows in REQUIREMENTS, 2 toggles + 1 declared row in ROADMAP), not copied from the plan's plan-time 7/23; the four placeholder traceability rows are declared modifications because the plan's own acceptance regex requires the evidence inside the original-ID rows."
  - "The milestone checkbox and the Status=Complete cell are left to the orchestrator's phase-complete step per its explicit instruction; the status row reads 22/22 with verification pending."
  - "§7b's polymarket keep-awake was restored by this session (Rule 2): the Task 1 transcript reverted pmset without it, and D-25-20-RESTORE binds the restore to the same step."
  - "Zero gsd-sdk mutation handlers were called; STATE/ROADMAP/REQUIREMENTS were hand-edited additively."
metrics:
  duration: "~1.5 h on CPU after the operator's Task 1 (03:30–17:16 UTC); full suite 25:43"
  completed: 2026-09-09
---

# Phase 25 Plan 20: The Revert, the Discharged Reservations and the Eight Evidenced Ticks Summary

**The machine is back at its measured prior state and that is proved, not remembered:**
`prove_reverted()` returned `{'sleep': 1, 'disksleep': 10, 'powernap': 1}` after the operator ran
`sudo pmset -a sleep 1 disksleep 10 powernap 1` printed from `phase25_venue.PMSET_REVERT`; all five
Phase-25 LaunchAgents are booted out; `KeepAlive` is false in every committed plist; the phase's
measured MPS spend is **97.17 h** (81.40 h sweep + 15.77 h recall) inside the 87.86–149.45 h
envelope; D-37's three reservations are facts on disk (44 adapter digests from bytes, n=8-only
canaries in the data, audit target `dp_n8_sigma0p000000` by lookup); D-40 is handed to Phase 28;
§O1's `{add, commit}` exception is closed as phase-only; and eight requirements are ticked by hand
against named artifact fields and guard tests, with both measured corrections kept visible behind
`SUPERSEDED:`.

## Task 1 — the human-action checkpoint (operator, 2026-09-09; no tracked file changed)

Transcribed verbatim into note §13.1. The lines that matter:

```
$ .venv/bin/python -c "import sys;sys.path.insert(0,'scripts');import phase25_venue as v;print(' '.join(v.PMSET_REVERT))"
sudo pmset -a sleep 1 disksleep 10 powernap 1
$ .venv/bin/python -c "import sys;sys.path.insert(0,'scripts');import phase25_venue as v;v.prove_reverted();print('reverted:', v.read_power_settings())"
reverted: {'sleep': 1, 'disksleep': 10, 'powernap': 1}
exit=0
$ launchctl list | grep personacore
(empty)
$ pgrep -x caffeinate
13226
$ ps -o pid,ppid,args -p 13226
13226 95011 caffeinate -i -t 300
```

The revert command was read from the module, not retyped. **Five** agents were booted out, not the
plan's two (`sweep`, `watch`, `recall`, `rehearsal`, `n64floor` — the recall agent was added
mid-phase by 25-18). `pgrep -x caffeinate` is not empty: the one process is the Claude Code
harness's own 300 s keep-awake (parent 95011), re-spawned per tool call and self-expiring; D-43's
by-owning-process method is what identifies it, and the run's own `-dims` wrapper is gone. The
three `SoftwareUpdate` flags were written to §6b's declared target and read back `1`
(`ConfigDataInstall` untouched at `1`).

## Task 2 — the operational note closed (`df100ca`)

§13 appended to `results/phase25_operational_note.md`, every figure a quoted command output:

- **§13.1** the transcript above; **§13.1b** §7b's restore, which the transcript had *not* done:
  the collector `collect_negrisk_books.py --service` was live (pid 7584) with nothing watching it,
  so the committed procedure ran from this session — `nohup caffeinate -s -i -w 7584` → pid
  **15665**, reparented to launchd, holding `PreventUserIdleSystemSleep` + `PreventSystemSleep`
  *on behalf of Process ID 7584*, quoted from `pmset -g assertions` by owner.
- **§13.2** `KeepAlive False RunAtLoad False` in all five committed plists (`plistlib`, never the
  installed copies).
- **§13.3** spend: 81.40 h sweep (`sweep_hours_44_points: 81.39631890805556`), 68.76 h interior,
  15.77 h recall (`total_scoring_hours: 15.771100948585405`) → **97.17 h**; **2** jetsam kills,
  largest loss **10.17 min** (`dp_n64_sigma0p500000` A1-mild; the other 5.75), **3** one-stage
  halts, **6** launches, **8** stall records at emission (1 / 1 / 6 by phase) and **395** at
  bootout, all `action_taken: "none"`. Against the envelope — throughput schedule **87.86 h floor /
  149.45 h ceiling**, 25-CONTEXT ~107 h / ~150 h, the plan's ~101 h — the sweep proper came in
  6.46 h *below the floor*; with the recall leg the total is inside the envelope and under both
  measured figures. The envelope held as an upper bound and was pessimistic as a point estimate.
- **§13.4** D-37: `44 adapters verified from bytes`, 59,498,056 B (each 1,352,147–1,352,303 B —
  §3's 1,352,069 was one file); 44 resume checkpoints 2,626,493,400 B, retention total
  **2,685,991,456 B** against the derivation's 2,685,921,568 B (+69,888 B); a 45th `latest.pt` on
  disk is 25-13's `phase25_calibration_seam_off_comparator_n64`. Canaries: 22 n=8 points all
  `out_of_corpus: 56` / `in_corpus: 8`; 22 n=64 all `0` / `64` — the plan's command names the
  field `out`; the schema's name is `out_of_corpus`, and the check passes against the real names.
  Audit target: no n=8 PASS → the pre-registered null branch → **`dp_n8_sigma0p000000`**, the σ=0
  control, and the note says what that means for Phase 26 (an adapter with no privacy claim).
- **§13.5** the seven `PUBLICATION_OBLIGATION` fields quoted with their close values; Phase 25
  writes no report. **§13.6** the exception closed: for this phase only, 44 one-path commits under
  the AST guard, the read-only discipline resumes; a later driver may not cite this exception.

Task 2's automated verify: `{'sleep': 1, 'disksleep': 10, 'powernap': 1} 44 adapters verified from bytes`.
`git diff --exit-code -- results/phase25_frontier.json` → 0; `git log --oneline -- results/phase25_frontier.json | wc -l` → `1`.

## Task 3 — eight ticks, two corrections, the close guard (`69f488e`)

**The two-bucket audit, run once per file against the `/tmp/25-20-*.pre` snapshots taken before any
edit** (the test re-runs the same audit against the blob at `df100ca` so it survives `/tmp`):

```
TOGGLE  : - [ ] **ADVT-01**: The adapter trained against the Phase 18 attack sui
TOGGLE  : - [ ] **CTRL-01**: A **retrained unmitigated control** at identical bu
TOGGLE  : - [ ] **CTRL-02**: The control is realised as a **sweep point** (`clip
TOGGLE  : - [ ] **FRONT-01**: A privacy/utility curve for both arms at **both ca
TOGGLE  : - [ ] **FRONT-04**: The verdict is computed by **importing** the GATE
DECLARED: | CTRL-01 | Phase 25 | run first, as a sweep point |
DECLARED: | CTRL-02 | Phase 25 | run first, as a sweep point |
DECLARED: | FRONT-01 | Phase 25 | |
DECLARED: | FRONT-04 | Phase 25 | |
audit ok: 5 toggles, 4 declared modification(s)
---
TOGGLE  : - [ ] 25-19-PLAN.md — the write-once assembly of `results/phase25_fron
TOGGLE  : - [ ] 25-20-PLAN.md — D-13's committed revert executed and verified, D
DECLARED: | 25. Frontier Sweep and the Existence-Gate Verdict | v4.0 | 21/22 | I
audit ok: 2 toggles, 1 declared modification(s)
```

**12 classified lines, residue 0** — not the plan's 31, because the plan's 7 / 23 were measured
at plan time: 25-19 had since ticked FRONT-02/FRONT-03 and every closed plan's ROADMAP line was
already `[x]`. The four placeholder rows are declared modifications with the originals' words kept
at the head of each cell (`run first, as a sweep point — **SATISFIED …**`); ADVT-01 and RPT-02 got
`*(continued)*` rows in the RPT02-ROW register because their originals carry substantive prose.

`git diff --numstat` for the Task 3 commit: **`11 9 .planning/REQUIREMENTS.md`** and
**`3 3 .planning/ROADMAP.md`**. **Zero `gsd-sdk` mutation handlers were called** on any planning
file; STATE.md was hand-edited (`5 5 .planning/STATE.md`).

**The two corrections carried into the traceability, one sentence each:** condition (a) is **ZERO
TOLERANCE**, not "at most 2 of 416" — X = `wilson_upper_bound(0, 416)` + `MARGIN_K × 0.0` = 0.006462
and one leaked question already exceeds it, and `tolerance_report` renders that sentence into all 38
points that reached (a) (FRONT-04's row). And **the gate never reads the control's extraction**, so
D-01 is justified by CTRL-02 + FRONT-03 — `extraction_ceiling` proves the floor's arm is
`NEVER_TAUGHT_ARM`, and every control record carries the corrected `scoring_justification`
(CTRL-01's and CTRL-02's rows). The acceptance check: `3 superseded phrasings present, every one
behind a SUPERSEDED: marker` (the control phrasing appears in both control rows).

**FRONT-04 is satisfied in a weaker form than its text implies, and the row says so:** the
existential is answered as 0 of 32 DP and 0 of 6 adversarial with 6 `adv_n64` points refused by the
sanctioned route — not 0 of 44.

**`tests/test_phase25_close.py`** — `.venv/bin/python -m pytest tests/test_phase25_close.py -v` →
**`26 passed in 0.52s`**, 0 skipped; `-k "is_ticked or names_an_artifact"` → `16 passed, 10
deselected`; `-k audit_target` → 1 passed; `-k corrections` → 1 passed. Every cited `results/` and
`tests/test_phase25_*.py` path is asserted to exist on disk (the test collects *every* such path in
a row, not just one). The three RED probes are kept as parametrized cases and pass by raising
exactly `('UNDECLARED DELETION', ['## Out of Scope'])`,
`('UNDECLARED DELETION', ['**Depends on**: Phases 20, 21, 22, 23, 24'])` and `('TOGGLE COUNT', 5, 4)`.
`test_the_pmset_state_is_reverted` calls `prove_reverted()` live on darwin and on any other host
asserts `pmset` is absent — a pass, not a skip, so the venue's pinned skip literals are untouched.

## Deviations from Plan

1. **[measured] Toggle counts 5 / 2, declared 4 / 1.** Above. The plan's `DECL=()` for
   REQUIREMENTS was unsatisfiable together with its own acceptance regex, which requires both
   superseded phrasings *inside the eight original-ID rows* (`len(rows)==8`) — filling an empty cell
   is a line modification. Declared and enumerated rather than worked around.
2. **[orchestrator instruction] The milestone checkbox and Status=Complete are not written.** The
   phase-status row reads `22/22 | Plans complete — verification pending`; the orchestrator's
   phase-complete step owns the rest. `roadmap.update-plan-progress` was not called — the plan
   forbids handlers, and the orchestrator's criterion (the row carrying 22/22) is met by hand.
3. **[Rule 2] §7b's restore performed** (note §13.1b) — the Task 1 transcript did not include it.
4. **Five agents, not two**, booted out; `pgrep -x caffeinate` non-empty by the harness's own
   assertion — both recorded as facts with owners, not as failures.
5. **The canary acceptance command names `out`;** the schema names `out_of_corpus`. Re-run against
   the real names; passes. Likewise `clip_bind_count` sits at the point's top level, not under
   `training`.
6. **The audit test's comparator is the git blob at `df100ca`**, resolved against the first later
   commit touching each file, so it stays green after `/tmp` is gone and after later phases edit
   the same files; the plan's `/tmp` snapshot audit was also run and is quoted above.
7. **The suite line** — see Verification; the plan's `0 failed, 1 skipped` / `1647/1` baseline
   predates the three artifact-gated promotion skips 25-18 recorded.

No auth gates beyond the checkpoint itself. No package installs. The five frozen modules,
`results/phase25_frontier.json` and `pyproject.toml`: `git diff --exit-code` → 0.

## Verification

- `prove_reverted()` live → `{'sleep': 1, 'disksleep': 10, 'powernap': 1}`, exit 0 (Task 2 verify and the close test).
- `launchctl list | grep personacore` → empty; `pgrep -x caffeinate` → the harness's `-i -t 300` and the restored `-s -i -w 7584`, both owned.
- `KeepAlive still false at close`; `44 adapters verified from bytes`; `only n=8 points have out-of-corpus canaries`.
- `tests/test_phase25_close.py -v` → `26 passed in 0.52s`, 0 skipped. `tests/test_phase25_correction.py` → 23 passed.
- Two-bucket audits: `audit ok: 5 toggles, 4 declared modification(s)` / `audit ok: 2 toggles, 1 declared modification(s)`.
- `git log --oneline -- results/phase25_frontier.json | wc -l` → `1`.
- `make lint` → `All checks passed!`, 275 files already formatted.
- Full suite `.venv/bin/python -m pytest tests/ -q -rs` → `2743 passed, 4 skipped, 83 warnings in 1544.00s (0:25:43)`, exit 0 — the same four skips 25-18 recorded (three `test_phase25_promotion.py` empty-candidate skips and the CUDA AMP smoke), so `tests/test_phase25_venue.py`'s literals (39/4) are unchanged and were not continued. Delta: **+26 passed / +0 skipped** over 25-19's 2717/4 (this file's 26 tests); **+1096 / +3** over the plan-time 1647/1 baseline, whose `1 skipped` predates 25-18's three artifact-gated skips.

## Commits

`df100ca` docs (note §13) · `69f488e` feat (REQUIREMENTS/ROADMAP ticks + `tests/test_phase25_close.py`) · this commit (SUMMARY + STATE.md).

## Self-Check: PASSED

`results/phase25_operational_note.md`, `tests/test_phase25_close.py` and this SUMMARY: FOUND. Commits `df100ca`, `69f488e`: FOUND in `git log`.
