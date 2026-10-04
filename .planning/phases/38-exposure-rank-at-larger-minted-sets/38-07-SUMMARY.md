---
phase: 38-exposure-rank-at-larger-minted-sets
plan: 07
subsystem: e5-driver
tags: [rank-02, e5, crosscheck, record, report, d-33, d-34, d-36, wr-01, cpu-rehearsal]
requires: [scripts/phase38_rank.py part 1 (38-06), scripts/phase38_prereg.py (frozen), results/phase38_minting.json (7357577)]
provides: [scripts/phase38_rank.py complete (crosscheck, curve_for, record_rehearsal, rehearsal_disclosure, build_record, emit, render_report, report, main), tests/test_phase38_rank.py complete (86 tests)]
affects: [38-08 (the real MPS run, whose launch the D-34 identity gates), 38-09 (rank record pins these bytes), 38-10 (report rendered by this code)]
tech-stack:
  added: []
  patterns: [phase37_r1b build_record/emit/main template, write-once rehearsal identity, signature-derived kwargs for the live rehearsal, GFM table cell-count gate]
key-files:
  created: []
  modified: [scripts/phase38_rank.py, tests/test_phase38_rank.py]
key-decisions:
  - "Any root inside the repo counts as real for the D-34 checks too (preflight identity gate, build_record disclosure), the same `_is_real` rule as 38-06. The plan says 'root resolves to _ROOT'; `_is_real` is a superset of that."
  - "The rehearsal found one driver defect: report tables were not GFM tables because the literal |R| in the headers added cells. Fixed in 1e68330 with a test. That commit lands after the rehearsal identity, so the real record's D-34 disclosure will list it with its subject as the reason."
requirements-completed: []  # the orchestrator owns the RANK-02 tick (hand-edited REQUIREMENTS/STATE/ROADMAP)
duration: ~20 min (13:46 → 14:05 local; rehearsal at 17:00 UTC)
completed: 2026-10-04
---

# Phase 38 Plan 07: E5 driver part 2 (crosscheck, record, report, CLI) and the CPU rehearsal Summary

The E5 driver is complete. The new pieces are the D-19 CPU cross-check, the write-once rank record
and the report renderer. The record's arithmetic all goes through the frozen `phase38_prereg`
definitions. The report gets the D-33 audit, the D-34 disclosure and the D-36 limitation, and the
CLI dispatches each command. The live path then ran once end to end on CPU on the real checkpoints,
into a scratch root with a scratch ledger. It finished SCORED with all 16 gate cells equal and 0 CPU
differences. The real producer record was fed to the report. The rehearsal found one report defect
(tables that do not parse as GFM tables). It is fixed and committed with its reason, and the
rehearsal was re-run into a fresh root, which kept the first identity.

## Commits

| Task | Commit | What |
|------|--------|------|
| 1 | 19c2fa9 | feat: crosscheck, curve_for, build_record (+ _events, _cpu_block, _hours, _load), emit; 6 tests |
| 2 | 632fde8 | feat: D-34 DISCLOSED_MODULES, rehearsal_identity_path, record_rehearsal, rehearsal_disclosure, run(rehearsal_identity=), preflight gate, record disclosure; 8 tests |
| 3 | 91553d9 | feat: render_report (+ helpers), _tracked_and_clean, report, main, `__main__`; 16 tests |
| 4 (rehearsal fix) | 1e68330 | fix: escape pipes in report table cells. The CPU rehearsal report's \|R\| headers broke every GFM table |

## RED outputs (natural, from the file's state before each implementation)

- Task 1: `6 failed, 56 passed in 9.15s`. The new tests hit `AttributeError: module 'phase38_rank' has no attribute 'emit'` (and crosscheck/curve_for). After implementing, the every-function census was red on `['_cpu_block', '_events', '_hours', '_load', 'build_record']`. I added direct calls to each.
- Task 2: `10 failed, 60 passed in 11.48s`. That is 8 new D-34 tests, plus the two Task 1 tests that now assert `rehearsal_disclosure == {"this_is_the_rehearsal": True}`.
- Task 3: `15 failed, 70 passed in 15.66s`. Among them, `test_the_cli_exits_non_zero_on_a_bogus_command` was red because `python scripts/phase38_rank.py bogus` exited 0 (no `__main__`). The first GREEN attempt had 3 failures. (a) The rows came out in JSON-sorted slot and size order ("128" < "32"), so the render now orders by SLOTS and int(size). (b) A local named `prefixes` tripped the 38-06 census `\bprefixes\s*=` (it guards check_unit_caps), so it was renamed `ks`. (c) Five render helpers were untested and now have direct tests.
- Rehearsal fix: `_assert_gfm_tables` failed on the current code with `assert 10 == 8` on the header `| reading | slot | |R| | rank | ...`. The escaped `_table` assertion also failed (`'| |R| |' != '| \\|R\\| |'`).

## Verify (real output, committed tree)

- `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase38_rank.py tests/test_phase38_prereg.py tests/test_phase21_sc5.py tests/test_lora_inject.py tests/test_phase35_prereg.py` → `244 passed in 53.67s` (after 1e68330)
- `tests/test_phase36_ledger.py tests/test_phase35_prereg.py` → `133 passed in 23.34s` (Task 3, before commit)
- `tests/test_phase25_driver.py` (after each of the last two commits) → `24 passed in 1.71s` / `24 passed in 1.72s`
- `ruff check .` → `All checks passed!`; `ruff format --check .` → `354 files already formatted`
- `.venv/bin/python scripts/phase38_rank.py bogus; echo $?` → `exit=1`
- `.venv/bin/python -c "...import phase38_rank as r; print(r.RUN_ID, r.FRONT, 'torch' in sys.modules)"` → `v6/38/E5/rank E5 False`
- `test_every_phase38_rank_function_has_a_cpu_test` passes with no exclusion (every def, private helpers included, is called by a test). `test_no_skips_in_this_file` passes.
- `== 10` in both files: 0. In the driver: no `os.replace`, `train_arm(`, `inject_lora(` or `LoRAConfig` (`inject_lora` appears only in the 38-06 docstring).
- `find results -maxdepth 1 -name 'phase38_rank*'` → nothing. `find data -maxdepth 1 -name 'phase38_rehearsal.json'` → nothing before Task 4 and after every test run. The tests never create the real identity, and the `_real_tree_untouched` fixture now also asserts that it exists in the same state after each test as before.

## What the tests prove (86 tests)

- Record arithmetic: the test recomputes every curve (rank_in_prefix / exposure_bits on minted[: size - 1]), every event (moved / left_top_eighth / first_event), and both relations against first_collapse / first_damage from `a2_counts()`, with `reachable=moved_reachable(rank_0, size)` for moved. All of it goes through `phase38_prereg` and matches the emitted record exactly. The flags are keyed by exactly the six PREFIXES, never M2 or adapter_off. WR-01: cat_name at k0 is forced to rank_0 = |R|, which gives `UNREACHABLE_AT_SIZE` (moved) and `ALREADY_AT_K0` (left the top eighth). Both render by name with `(rank_0 = N)`. The reachable path is also exercised.
- D-27: birth_year and house_number carry the sensitivity curves with reduced effective sizes. D-33: `drop_formula_audit == prereg.drop_formula_audit(a2_counts())`, with flips `[]` and exact_ties `[["person_name", 8]]`. D-19: 0 differing cells when CPU equals MPS. One perturbed CPU NLL is counted as `[["k0", "pet_name", 8]]`.
- emit refuses an existing record ("REFUSING to overwrite"), a missing run sidecar, a missing CPU sidecar on SCORED, a tampered gate sidecar or NLL sidecar ("not the bytes the run wrote"), a dirty tree, and a partial shape on the real root. A GATE_FAILED run emits gate rows only, with no curves and no CPU sidecar needed.
- D-34: the identity path is computed from `_ROOT` at call time. record_rehearsal writes once, and a second call returns `kept` with the bytes unchanged. B-1: a crash on the very first score (`len(rig.log) == 1`) leaves the identity, no sidecar and an open start line. A preflight refusal writes no identity. A rerun into a fresh root and ledger keeps the first identity. The real root refuses `rehearsal_identity` before any ledger line. The disclosure check runs against git itself: each listed commit is the `git log first..HEAD -- DISCLOSED_MODULES` list, carries its own subject, and touched the modules it lists. Equal digests give `commits == []` and `driver_changed False`. One drifted digest with no commit raises SystemExit. On the real root (with `_ROOT` patched to the rig), preflight refuses without the identity, and SCORED and GATE_FAILED records carry the disclosure.
- Report: the 13 sections appear in order. The curves table is parsed back cell by cell against the record. The relation table has 2 rows per slot × size. The D-21 ruling is verbatim. The tests cover both D-33 branches, both D-34 branches plus the rehearsal-record statement, and both D-36 sentences on the SCORED and GATE_FAILED records. Every table has equal header, delimiter and body cell counts. report() writes once. With the real-root branch and `_tracked_and_clean` stubbed False it refuses and writes nothing. The full fake chain produces 4 artifacts, and the report equals `render_report(json.load(record))`. main dispatches each of the 5 commands with no arguments from `_REPO` (`inspect.signature(real).bind()`); `[]`, `["bogus"]` and `["run", "x"]` raise `SystemExit(__doc__)`.

## CPU rehearsal (Task 4), values read from the files

Root `/private/tmp/claude-501/-Users-juliorcoelho-PersonaCore/3c094aa2-b238-4ac9-a025-7ab670fd2b62/scratchpad/rehearsal38`
(the second run is under `rehearsal38b`), tmp ledger and heartbeat in the root. Kwargs came from
`inspect.signature` of each function. The script asserts that every supplied name is a `run`
parameter: `run(['device', 'heartbeat_path', 'ledger_path', 'max_size', 'rehearsal_identity', 'root', 'slots'])`,
`crosscheck(['device', 'root'])`, `emit(['root'])`, `report(['root'])`. All eight readings were
read, on slots pet_name and birth_year, at |R| 8, on the real checkpoints. HEAD at launch was
91553d9, with porcelain of scripts/src/results/tests/ledger/artifacts at 0.

### Rehearsal identity (D-34)

Tracked copy of the gitignored `data/phase38_rehearsal.json` (sha256 `cdda60d0b5bf115fd7e67a6aba28012c22377d987288092a6dab6e51ac564289`, the same before and after the second rehearsal):

```
{"git_sha": "91553d96845701012a3fa0352d4223e8466b2b93", "max_size": 8, "module_sha256": {"scripts/phase38_rank.py": "f887d4374aba17552d7873b090e867d7d9a1dfc7dfd1c0f738f59afc2f66381d", "scripts/phase38_sizes_prereg.py": "18f37b0b50fbbd8f0f43797113ce64d3c162e1eb0bedda887e35cf52f045991c"}, "readings": ["k0", "k8", "k16", "k32", "k64", "k78", "M2", "adapter_off"], "slots": ["pet_name", "birth_year"], "started_utc": "2026-10-04T17:00:06.230664+00:00"}
```

### Log and ledger (first rehearsal)

```
PREFLIGHT OK 91553d96845701012a3fa0352d4223e8466b2b93 device=cpu readings=8 projection_h=0.467956566879681 stop_h=0.5418565110509128 spent_E5_s=0.0
REHEARSAL RECORDED 91553d96845701012a3fa0352d4223e8466b2b93
RUN SCORED — next: crosscheck, then emit
WALL run 8.2s
CROSSCHECK DONE .../rehearsal38/data/phase38_rank_cpu.json
WALL crosscheck 12.4s
EMITTED SCORED .../rehearsal38/results/phase38_rank.json
REPORT .../rehearsal38/results/phase38_rank_report.md
WALL report 12.5s
```
```
{"event": "start", ..., "front": "E5", "phase": 38, "record": null, "run_id": "v6/38/E5/rank", ..., "utc": "2026-10-04T17:00:06.214083+00:00"}
{"event": "end", ..., "front": "E5", "phase": 38, "record": "results/phase38_rank.json", "run_id": "v6/38/E5/rank", ..., "utc": "2026-10-04T17:00:13.634309+00:00"}
```
Record `cost.run_hours` 0.0020561052777777777 (7.4 s of run clock). Total wall time was 12.5 s. The
heartbeat file holds 1 beat (the run was shorter than one thread period). The reconstruction
digests are persona 226f2ae5…, components a7cc2271…, M2 22e66552…, the committed ones.

### Gate rows (rank / committed rank / |R| / equal), all 16 equal, `passed: True`

```
k0          birth_year (1, 1, 7, True)  pet_name (1, 1, 8, True)
k8          birth_year (1, 1, 7, True)  pet_name (1, 1, 8, True)
k16         birth_year (1, 1, 7, True)  pet_name (1, 1, 8, True)
k32         birth_year (1, 1, 7, True)  pet_name (1, 1, 8, True)
k64         birth_year (1, 1, 7, True)  pet_name (1, 1, 8, True)
k78         birth_year (1, 1, 7, True)  pet_name (2, 2, 8, True)
M2          birth_year (1, 1, 7, True)  pet_name (2, 2, 8, True)
adapter_off birth_year (3, 3, 7, True)  pet_name (4, 4, 8, True)
```
These match the plan's expectations: pet_name ranks 2 at k78 and M2 and 4 adapter-off, and
birth_year ranks 3 adapter-off. The largest |taught NLL − committed NLL| is 2.06e-05 (k0 pet_name).

### Curves at |R| 8 (from the report, rank (bits))

```
| pet_name   | 8 | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) |
| birth_year | 8 | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 5 (0.6780719051126378) |
```
Columns: k0 k8 k16 k32 k64 k78, M2 (descriptive), adapter-off (descriptive). Events at |R| 8 have
rank_0 = 1, every flag False and first = never for both events in both slots. Relations: pet_name
NEVER vs collapse (k = 64) and NEVER vs damage (k = 16). birth_year is "never collapsed within
the grid" vs collapse, and NEVER vs damage (k = 78). The D-27 sensitivity reads birth_year at
|R| 8 → 6 without neighbours: rank 1 (2.584962500721156) under the six prefixes and M2, and 5
(0.2630344058337939) adapter-off. CPU cross-check: 0 of 16 cells, 0 of 16 gate cells (cpu,
torch 2.7.1). D-33: 7 differing cells, flips [], exact tie person_name k = 8. Rehearsal disclosure:
`{"this_is_the_rehearsal": True}`.

One thing in this slice, stated as read and not interpreted: on the minted set, pet_name is rank
1 under adapter-off, against 4 on the committed reference set. This is the situation the D-36
limitation describes.

### Report section headers (rendered from the real record)

`# Phase 38 — E5 exposure rank at larger minted sets`, `## Status`, `## Approval and cost (D-21/D-22/D-23)`,
`## Gate: committed reference sets (D-18, D-11a)`, `## A2 counts, collapse and damage (D-13, D-14)`,
`## Drop formula audit (D-33)`, `## Rank curves (D-15)`, `## Did the rank move before generation collapsed? (D-12, D-29, D-30)`,
`## Numeric neighbour sensitivity (D-27, descriptive)`, `## CPU cross-check (D-19, descriptive)`,
`## Rehearsal disclosure (D-34)`, `## Limitations (D-36)`, `## Provenance`.

### The defect found and the second rehearsal

The rendered report showed `| slot | |R| | k0 | ...`. The unescaped pipes give the header 2 more
cells than the delimiter row (10 against 8 in the gate table), so GFM would show the gate,
curves, relation and sensitivity tables as plain text. Fixed in 1e68330, with the reason in the
subject. A second rehearsal into the fresh root `rehearsal38b` at HEAD 1e68330 printed
`REHEARSAL KEPT 91553d96845701012a3fa0352d4223e8466b2b93`. The identity's sha256 was unchanged.
The ledger had one start and one end line. The `readings` and `gate` blocks were identical to the
first rehearsal. The report differs from the first only in run_hours and the escaped `\|R\|`
headers.

The disclosure the real run will compute was read with
`rehearsal_disclosure(identity, launch_git_sha=HEAD, launch_module_sha256=module_sha256())` at
1e68330:
changed `{"scripts/phase38_rank.py": true, "scripts/phase38_sizes_prereg.py": false}`,
driver_changed true, commits `[{"sha": "1e683306155b9316eb1a3fd8343f998d428c9f9c", "reason": "fix(38-07): escape pipes in report table cells — the CPU rehearsal report's |R| headers broke every GFM table (header cells != delimiter cells)", "modules": ["scripts/phase38_rank.py"]}]`.

### Real tree untouched

`git status --porcelain` → only the pre-existing ` D .claude/scheduled_tasks.lock`. `git status
--porcelain -- scripts src results tests ledger | wc -l` → 0. `find data -maxdepth 1 -name
'phase38_rank_*'` → nothing. `find results -maxdepth 1 -name 'phase38_rank*'` → nothing. The
real ledger sha256 is `d0d0c2b4…aa464` before and after. `data/phase38_rehearsal.json` is the one
intended real-tree file, and it is gitignored (`.gitignore:17:data/`).

## Deviations from Plan

**1. [Rule 1 - Bug, found by the rehearsal] Report tables did not parse as GFM tables.** `|R|` in a
header cell split into extra cells. `_table` now escapes `|` in every cell, and
`_assert_gfm_tables` checks every table in the SCORED and GATE_FAILED reports. Commit 1e68330,
disclosed by D-34 with its subject.

**2. [Rule 1] Render order.** `atomic_write_json` sorts keys, so the record's slots come out
alphabetical and its sizes in string order ("128" before "32"). The report orders slots by SLOTS
and sizes and prefixes by int (`_slots`, `_sizes`). This was caught in the Task 3 GREEN attempt,
before that commit.

**3. Small additions.** These are not in the plan text. The record carries `gate` (the gate
sidecar) in both statuses as well as `committed_reference_sets`. Each event carries `reachable`.
The record has `events_reason` when the readings are a subset, and `provenance.sidecar_sha256`
(run, gate, nll, cpu). `cpu_crosscheck` adds `device`, `torch_version` and
`gate_differing_cells`. build_record proves that each NLL sidecar's minted list is the minting
record's prefix. record_rehearsal prints `REHEARSAL KEPT <sha>` when it keeps the identity. No
plist (per the plan).

**4. Retrofit (Task 2).** No plan-06 test needed a stand-in identity. The only plan-06 test that
patches `_ROOT` and calls preflight (`_refuse_cpu_on_the_real_root`) refuses at the D-17 I/O-free
check, which runs before the D-34 check. The new real-root tests write their stand-in identity
with `record_rehearsal` into `rig/data/`.

## Known Stubs
None.

## Threat Flags
None beyond the plan's register: no new network, auth or schema surface. T-38-28..32 and T-38-44
are mitigated as the plan specifies. `report` writes markdown with `write_text`, write-once.

## Self-Check: PASSED
- FOUND: scripts/phase38_rank.py, tests/test_phase38_rank.py, data/phase38_rehearsal.json (gitignored), the scratch record, report and ledger
- FOUND: 19c2fa9, 632fde8, 91553d9, 1e68330
- Untouched: phase38_prereg.py, phase38_mint.py, phase38_sizes_prereg.py, results/phase38_minting.json, phase36_ledger.py, phase36_caps.py, the real ledger, STATE/ROADMAP/REQUIREMENTS. No gsd-sdk mutation handler was called. ` D .claude/scheduled_tasks.lock` was left alone.
