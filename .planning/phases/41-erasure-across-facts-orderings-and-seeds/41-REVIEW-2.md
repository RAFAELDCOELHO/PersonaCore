---
phase: 41-erasure-across-facts-orderings-and-seeds
reviewed: 2026-10-08T23:48:24Z
review_base: 52536b4
depth: deep
files_reviewed: 2
files_reviewed_list:
  - scripts/phase41_erasure.py
  - tests/test_phase41_erasure.py
findings:
  critical: 0
  warning: 2
  info: 5
  total: 7
status: issues_found
---

# Phase 41: Code Review Report (E1 driver, before any MPS time)

**Reviewed:** 2026-10-08T23:48:24Z, at REVIEW_BASE 52536b4 (the driver is byte-identical to the rehearsed 075f5ea)
**Depth:** deep (the run path traced into phase19_erasure, phase18_extraction, phase40_noise / phase40_prereg, phase36_ledger, phase25_run, teach_persona and personacore.checkpoint)
**Files Reviewed:** 2
**Status:** issues_found

## Summary

No finding meets Rafael's stopping rule for a BLOCKER. None changes a read value or an emitted verdict in a real fill. None can lose or brick ledger hours with a probability above a millisecond kill window. So there are 0 critical findings.

There are two WARNINGs:
- **WR-01** is a recovery-path defect of the Phase 40 class. The dropped-attempt comparison runs unguarded at the very end of a re-run prep unit. If a dropped attempt kept an unloadable adapter, every re-run of that unit does all of its MPS work and then crashes before writing its record.
- **WR-02** is open item 4(a). The erasure record and the report never surface a re-run unit's dropped attempts.

Both open items from 41-11 are confirmed by experiment. 4(a) is WR-02. 4(b) is IN-01: `d02_cpu_equality` is None by construction on any MPS record.

The rest of the brief checks out. Each item below was examined, with its evidence:

| # | Item | Outcome |
|---|---|---|
| 1 | Launch path, every dereferenced kwarg | An AST pass bound all **178** calls the driver makes into phase19_erasure, phase14_recall, teach_persona, phase18_extraction, phase37_routes, phase40_noise / phase40_prereg, phase35_prereg, phase36_ledger, phase25_run and phase41_prereg against `inspect.signature` of the real functions: `bound calls: 178, failures: []`. Every module the run path imports lazily is loaded by `_import_modules()` before `module_sha256()`. The only exception is `phase37_prereg`, which only phase40's emit imports and the E1 run path never does. The live path main → preflight → run → run_prep_unit / write_cell → start / beat / end was exercised end to end on CPU in 41-11. The real-root branches (identity, disclosure, `_launch_pathspec`, STAGE 1 DONE) are covered by `test_run_with_no_arguments_resolves_the_real_defaults` and `test_run_stage2_on_the_real_root`. |
| 2 | Crash / recovery, R-3 b | Three cases are correct: a record written but no end line (preflight says append the end line, NEVER reconcile; tested); a STOP (open attempt, then reconcile and a lost line); a crash at each step of a prep unit or a cell (`_output_roots` lists the band record, cal_erased, adapter, checkpoint, bins, csv dirs, ordering, K = 16 / K = 48 records, M1 and the atomic temps). The driver writes the ledger only through `phase36_ledger.append`, which refuses to append onto a torn tail. No path writes two end lines for one record, so hours are not double-counted (`unit_outcomes` refuses a later attempt of a whole unit). Pause and resume are checked between attempts only, against the 52.78 h share, and tested. Defects found: WR-01, IN-03. |
| 3 | MPS specifics | D-02 runs at every gradient: `taylor_scores` is the only gradient path, and it serves the smoke, the gradient calibration and the gradient cells. The committed control gap comes from the same `load_adapted_model` + `dialogue_ppl_pair` path on mps. The committed Phase 40 records show mps cross-process determinism: `adapter_off` is 4.573349214207799 in both seeds' runs, and pre equals post. The base runs `attn_impl` "manual" (the slim config has no `attn_impl` key, so the default applies), so the MPS SDPA grad / no-grad backend split does not apply to D-02. Memory is not a concern: the base has 17,037,312 parameters (about 68 MB fp32), so 2-3 resident models at K = 48 / D-13 are small. `_release` is called after every model drop. The driver never touches caffeinate: the plist wraps `caffeinate -dims`, the driver is ppid 1 and caffeinate is its child (41-12 interfaces). |
| 4 | Open items 4(a) / 4(b) | WR-02 / IN-01 |
| 5 | 41-11 readings | Read and recorded correctly, as descriptions only. `greedy_1337_phase19_prefix`: observed = `applied_ordering[:len(ordered_prefix)]`, held = list equality. The element types match: the suite's producer test reads held True for a prefix-first ordering, and the rehearsal reads False with 76/78 positional matches. D-11: held = `adapter_identity(...)["tensors_identical"]`, with per-key `max_abs_diff` recorded. No `_prove` reads either value, so a False never fails a unit. |
| 6 | build_record / emit / report on the real root | Five points: (1) `refuse_if_dirty` runs before build and `_tracked_and_clean(FLOORS_FILE, *inputs)` after; (2) `phase41_floors_prereg` is imported at :2169 only, inside build_record, on the real root; (3) the record and the report are write-once; (4) the K = 16 and K = 48 records are proved by their producer's sha256; (5) the cell, calibration and band records are pinned by digest in `inputs`, plus the clean check. Gaps: IN-05. |
| 7 | Exact counts (CR-01) | AST census of the driver: its only non-path divisions are `/ 3600` and a timing ratio, and its only ordering comparisons are structural (`ctx_len >= 1`, rerank indices, a set inclusion). It never compares an n/27 value. Every condition goes through the prereg. |

Baseline: `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase41_erasure.py` → `134 passed in 29.78s`. Every experiment below is in `<scratchpad>/rv41/test_review_exp.py`, which reuses the suite's rigs (fakes behind the real signatures, tmp roots, and the suite's `_real_tree_untouched` autouse guard imported). The run was `.venv/bin/pytest -q -p no:cacheprovider -s test_review_exp.py` → `7 passed in 3.78s`. Nothing ran on MPS. `git status --porcelain -- scripts src results tests ledger artifacts` was empty before and after.

## Warnings

### WR-01: An unloadable kept adapter crashes every re-run of a seed's first prep unit after all its MPS work

**File:** `scripts/phase41_erasure.py:1360-1387` (`_compared_attempts`), called at `:1765-1767` inside the calibration record's dict literal, after training, D-11, the calibration and cal_erase. The trigger is the non-atomic `torch.save` in `src/personacore/checkpoint.py:276` (`export_adapter`), reached from `teach_persona.py:2080`.

**Issue:** When a seed's first prep unit is re-run, `_compared_attempts` loads every dropped attempt's kept adapter through `phase40_noise.adapter_identity`, which calls `load_adapter` and then `torch.load`. Nothing guards that load, and it runs only after the unit has finished all of its work. Suppose an attempt is killed inside `export_adapter`'s plain `torch.save` (a 1.35 MB file, a millisecond window; jetsam, power, `bootout`). drop_attempt keeps the torn adapter. Then:
- each re-run trains again, calibrates and runs cal_erase, then raises before the calibration record is written;
- because `_dropped_attempts` lists every lost attempt's manifest, every later re-run hits the same torn file.

The unit cannot become whole without a code change. This is the Phase 40 class: a step after the paid-for work that is outside any catch, like 40-REVIEW-2 WR-03.

The suite never runs the real `adapter_identity` on a re-run. `test_rerun_needs_the_manifest_and_compares_attempts` patches it, and 41-11's prep leg reached only the NOT_PRODUCED branch. The control E7 shows that the real path works for a whole kept adapter.

Experiment (`-k "e1 or e7"`; the trainer writes a real `export_adapter` file, and the first attempt truncates it to half and raises):
```
E1 attempt 2: RuntimeError: PytorchStreamReader failed reading zip archive: failed finding central directory | steps ['require_launch', 'require_launch', 'start', 'gap', 'record', 'train', 'd11', 'load', 'calibration', 'cal_erase'] | calibration record False | last ledger event start
E1 attempt 3: RuntimeError: PytorchStreamReader failed reading zip archive: failed finding central directory | steps [... same ...] | calibration record False | last ledger event start
E1 lost attempts: 3
E7 whole; adapter_identity.tensors_identical=True
```

**Fix:** Make the comparison descriptive and never fatal, following ruling c's pattern in `d13_at_stop`:
```python
for attempt in attempts:
    item = next((i for i in attempt["kept"] if i["from"] == rel), None)
    try:
        if item is None:
            value = NOT_PRODUCED
        elif kind == "prep":
            value = phase40_noise.adapter_identity(new, root / item["path"])
        else:
            value = (_load(root / item["path"])["ordering"]["ordered"]
                     == _load(new)["ordering"]["ordered"])
    except Exception as exc:  # descriptive: a dropped attempt's leftovers never cost the re-run
        value = {"not_compared": f"{type(exc).__name__}: {exc}"}
    compared.append({**attempt, field: value})
```
Add a regression test from E1 (the RED is the PytorchStreamReader error above). This is on the run path, so per 41-12 it needs a CPU re-rehearsal with a new suffix. Alternatively, rule it a known limitation: the window is milliseconds, and after a first occurrence R-3 b already allows an approved fix committed before drop_attempt, which bounds the loss to one re-run.

### WR-02: The erasure record and the report do not surface a re-run unit's dropped attempts (open item 4(a))

**File:** `scripts/phase41_erasure.py:2250-2259` (the cell block that `build_record` builds), `:2363-2374` (calibrations), `:2471-2644` (`_cell_section`).

**Issue:** Each re-run unit's own record carries `dropped_attempts`: each manifest, the kept files with their sha256, the relaunch declarations, and `ordering_equal` / `adapter_identity`. build_record copies none of that into `cells[unit]` or `calibrations`, and render_report never mentions them. A reader of the published record or report cannot tell that a whole cell was re-run after a crash, what the cause note said, or whether the orderings agreed. The data is reachable only by opening the cell record, which `inputs` pins by sha256. 41-11's plan expected emit to list the dropped attempt.

This does not change any verdict or reading. It is a disclosure gap in the published artifact.

Experiment (`-k e3`: a pet_name/greedy/1337 cell crashes at K = 16, is reconciled and dropped, re-runs through the real `k48_confirm`, then `emit` runs with the real fills):
```
E3 cell record dropped_attempts=1 ordering_equal=False | erasure cell block has dropped_attempts: False | keys mentioning 'drop': [] | report mentions lost_utc: False | ... | cell outcome whole
```
(The report's only "dropped" is the boilerplate "NOT_RUN: … dropped and not re-run".)

**Fix:** In build_record, for each whole cell and each prep unit, carry a summary of each attempt, read from the sha-pinned unit record:
```python
dropped_attempts=[{k: a[k] for k in ("lost_utc", "cause_note", "manifest", "manifest_sha256",
                                     "relaunch_git_sha", "head_change_declared")}
                  | {"n_kept": len(a["kept"]),
                     "compared": a.get("ordering_equal", a.get("adapter_identity"))}
                  for a in rec["dropped_attempts"]],
```
Then `_cell_section` prints one line per attempt, and the calibrations section gets the same for prep. This is on the emit path, not the run path, so 41-12 asks for no re-rehearsal. The commit is disclosed through `rehearsal_disclosure`: `driver_changed` becomes True in every record of the launch. Land it before stage 1, so that stage-1 and stage-2 records do not carry different disclosures for one fix.

## Info

### IN-01: `d02_cpu_equality` reads None in any real (MPS) erasure record, by construction (open item 4(b))

**File:** `scripts/phase41_erasure.py:2319-2321`, `:2343`

**Issue:** The frozen prediction reads "bit for bit **on CPU**". On the real root, preflight forces mps, so `devices == {"cpu"}` is never true and `held` is None. The report row is a bare `| d02_cpu_equality | None |` with no reason.

The CPU evidence exists, but only outside committed artifacts: 41-11's scratch roots hold 5 smoke + 12 calibration + 5 cell gradients, all equal. The identity carries seconds and ratios only. `observed.d02` also lists only the calibration gradients. It omits the smoke's 5, which live in the gitignored variant.json, and the gradient cells' own D-02 values.

On mps every listed value is `equal: True` necessarily, since an inequality stops the run. So the MPS record is strong evidence for the device that matters. It is just not evidence for this prediction.

Experiment (`-k e4`, real-root rig with the device resolved to mps):
```
E4 devices=['mps'] n_d02=2 all_equal=True held=None | report row: | d02_cpu_equality | None |
```

**Fix options and cost:**
- (a) **Recommended, cheapest.** Rule it a known limitation and add an emit-only `reason` field plus a report sentence: "CPU-scoped prediction; this record holds mps gradients only (all equal by the D-02 stop); measured on CPU in the 41-11 rehearsal". No re-rehearsal is needed; the commit is disclosed.
- (b) Write the smoke's CPU d02 list into the identity and from there into `rehearsal_disclosure`, so it reaches committed records. This is a run-path change: `ordering_smoke`, `record_rehearsal_seconds`, `_IDENTITY_KEYS`, and preflight's identity check all change. It needs a fresh identity, and so a full CPU re-rehearsal (~5 h 20 m in 41-11).
- (c) Changing the prediction's wording is a prereg edit. That is Rafael's ruling, not a fix.

### IN-02: Preflight does not require variant.json when a pending unit needs it and the smoke will not run

**File:** `scripts/phase41_erasure.py:1510` (preflight only prints `variant=unset`), `:1547-1549`, `:1817`

**Issue:** At stage 2 (or for a gradient prep unit when PREP_UNITS[0] is whole), a missing `data/phase41_e1/variant.json` is found only inside the unit, after its start line. That leaves an open attempt, which means a lost line and an R-3 b approval cycle. On the real run the file persists on local disk from stage 1, and the first gradient cell is CELL_UNITS[8], so this is unlikely and costs about 0 MPS seconds.

Experiment (`-k e2`):
```
E2 preflight stage=2 variant=unset | run: [phase41_erasure] …/data/phase41_e1/variant.json is missing … | last ledger line start v6/41/E1/cell_pet_name_gradient_seed1337
```

**Fix:** In preflight, refuse before the first start line when a pending unit is a gradient one, the variant file is absent, and the smoke is not scheduled: `_prove(_variant_path(root).exists() or <smoke scheduled>, ...)`. This is on the run path, so batch it with WR-01 if that is fixed.

### IN-03: A failure in the middle of drop_attempt's moves leaves the unit without any way to get a manifest

**File:** `scripts/phase41_erasure.py:1231`, `:1251-1256`

**Issue:** The moves happen before the manifest is written, and the write-once guard is on the attempt directory. If one `shutil.move` fails, some files are already under `rel_dir` and no manifest exists. A retry then refuses on write-once, `rerun_units` never lists the unit, and the remaining partial outputs stay in place. drop_attempt is a CPU step run by Claude, so this is rare and recoverable by a reviewed step.

Experiment (`-k e5`, the second move planted to fail):
```
E5 second drop_attempt: …_2026-10-08T234650.179024+0000 exists: write-once | rerun_units=[] | still in place: 4
```

**Fix:** Write-once on the manifest only. Let a retry continue into an existing `rel_dir` that has no manifest, moving the files still in place and keeping the sha256 checks. Alternatively, write a `moving.json` intent file first and finish from it. This is not on the run path.

### IN-04: emit's dirty check refuses a declined dropped unit's in-place partial outputs

**File:** `scripts/phase41_erasure.py:2427-2436` (`pathspec=LAUNCH_PATHSPEC`), versus preflight's `_launch_pathspec(outcomes)` at `:1471`

**Issue:** R-3 b keeps a crashed unit's partial outputs in place until Rafael rules. If he declines both a re-run and a move, the untracked `results/phase41_k16_*` / `k48_*` files make emit refuse indefinitely. 41-15 handles this by asking whether they move under drop_attempt. That move, however, writes a valid manifest, which `rerun_units` (:1287-1303) reads as an approved re-run. A later `run` would therefore re-run the unit. This is harmless after the last launch, but it conflates two of Rafael's rulings (same residual as 40-REVIEW-2's IN-03 note).

Experiment (`-k e6`, in a fresh scratch git repo):
```
E6 emit's pathspec (LAUNCH_PATHSPEC) with an untracked results/phase41_k16_pet_name_greedy_seed1337_k016.json: REFUSES; with preflight's :(exclude) form: passes
```

**Fix:** Either use `_launch_pathspec(outcomes)` in emit and list the dropped units' in-place outputs in the record (as Phase 40's `dropped_seed_outputs.in_place` did), or have the move-only use of drop_attempt record that it is not a re-run approval. Both are emit / R-3 b tooling, not the run path.

### IN-05: Provenance pieces that live only in gitignored files, or are not rendered

**File:** `scripts/phase41_erasure.py:1602-1616`, `:1757-1758`, `:2404`, `:2729`

**Issue (unverified impact; read from the code):**
- (1) The measurements that decided the variant (`cpu_seconds`, `mps_seconds`, the smoke's d02 and timings) exist only in the gitignored `data/phase41_e1/variant.json`. The calibration and cell records carry only `variant` / `variant_decided_by`, and 41-12 copies variant.json into the SUMMARY by hand.
- (2) `inputs` and `module_sha256` omit `scripts/phase41_floors_prereg.py`. Its content is pinned only through `git_sha` plus the clean check.
- (3) render_report shows only `tensors_identical` for D-11. `calibration_identity`'s `finding` (reference sha256 ≠ the D11_REFERENCE_RECORD digest), which the prediction calls "a reported finding", is never rendered.

**Fix:**
- (1) Copy the variant blob into the gradient calibration records. This is on the run path.
- (2) and (3) Add `inputs[FLOORS_FILE] = _sha256(_REPO / FLOORS_FILE)` on the real root, and render `reference_sha256_matches_record` / `finding` beside D-11. Both are on the emit path.

## Not verified

- Nothing ran on MPS:
  - D-02 equality on mps (grad-enabled forward vs `span_nll_from_ids`' no-grad forward) is argued from the shared op sequence and the manual attention path, not measured.
  - The same holds for control-gap equality on mps: argued from Phase 40's committed cross-process determinism, not measured.
  - The 41-12 smoke is the measurement.
- I did not run preflight against the real root: it reads the milestone ledger and the identity, and `_device()` would probe MPS. 41-12 Task 2 step 10 runs it.
- The WR-01 trigger (a kill inside `torch.save`) is simulated by truncating the file, not by a real SIGKILL.
- The full suite was not run. Only `tests/test_phase41_erasure.py` was run (134 passed), plus the 7 scratch experiments.

---

_Reviewed: 2026-10-08T23:48:24Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_

## Resolution (2026-10-09)

Rafael's reply at the 41-12 review checkpoint, 2026-10-09 (verbatim):

> WR-01: limitação conhecida, como recomendado. Se acontecer, segue a R-3 b: correção aprovada por mim antes do drop_attempt.
>
> WR-02: corrigir como recomendado, só no emit, antes do estágio 1.
>
> IN-01: opção (a). A frase no relatório diz: a igualdade do D-02 em CPU foi estabelecida no ensaio CPU (citar o registro do ensaio), e em MPS ela é verificada em cada gradiente da rodada; o campo d02_cpu_equality fica None porque nenhum gradiente da rodada roda em CPU.
>
> IN-02: limitação conhecida. No portão de lançamento do estágio 2, conferir à mão que variant.json existe e citar o conteúdo dele no aviso de lançamento.
>
> IN-03, IN-04: limitações conhecidas.
>
> IN-05: corrigir os três como recomendado, só no emit, no mesmo commit do WR-02: variant.json copiado para o registro, sha do arquivo de pisos em inputs, e o resultado do D-11 impresso no relatório.

- **WR-01** — known limitation. If it happens, R-3 b applies: a fix approved by Rafael and committed before drop_attempt.
- **WR-02** — fixed in 4d521a8 (emit only). build_record copies each re-run unit's dropped-attempt summary (lost_utc, cause note, manifest and its sha256, relaunch sha, head change declared, n_kept, ordering_equal / adapter_identity) into the cell block and `calibrations.dropped_attempts`; the report prints one line per dropped attempt.
- **IN-01** — option (a), fixed in 4d521a8 (emit only). `d02_cpu_equality.held` stays None on a non-CPU record, with a `reason`: D-02 equality on CPU was established in the CPU rehearsal (cited as `.planning/phases/41-erasure-across-facts-orderings-and-seeds/41-11-SUMMARY.md:172-176`, commit 2098294, bound as the driver constant `D02_CPU_REHEARSAL_RECORD`), and on the run's device it is verified at every gradient of the run; the field is None because no gradient of the run runs on CPU. The report prints the sentence. The rehearsal's own records (scratch roots, gitignored `data/phase41_rehearsal.json`) are not committed, hence the SUMMARY citation.
- **IN-02** — known limitation. At the stage-2 launch gate, check by hand that `data/phase41_e1/variant.json` exists and cite its content in the launch notice.
- **IN-03** — known limitation.
- **IN-04** — known limitation.
- **IN-05** — fixed in 4d521a8 (emit only, same commit as WR-02): (i) variant.json's path, sha256 and content copied into the record as `variant_record` (proved equal to the gradient calibration records' variant), and the report prints the variant, the deciding measurement and its seconds; (ii) `inputs["scripts/phase41_floors_prereg.py"]` = the floors file's sha256 on the real root; (iii) the report's D-11 row prints reference_sha256_matches_record, tensors_identical, max abs diff and finding.

Verification of 4d521a8: tests first (5 RED: KeyError `dropped_attempts` x2, `reason`, `variant_record`, D-11 row absent), then `tests/test_phase41_erasure.py` 139 passed; census on the committed tree, batch 1 `1373 passed` (1368 + 5), batch 2 `226 passed, 3 skipped`; `ruff check .` and `ruff format --check .` clean. An AST diff against 52536b4 changes only build_record, _cell_section and render_report and adds D02_CPU_REHEARSAL_RECORD, _DROPPED_SUMMARY_KEYS, _dropped_summary and _dropped_lines; no run-path function changed, so no CPU re-rehearsal is needed. The commit changes the driver's digest, so `rehearsal_disclosure.driver_changed` is True in every record of the launch. Driver sha256 `a5ee8d45619b36db4018906c4419d5be998ac4a2ac162786e0bcab100bccbf56`.
