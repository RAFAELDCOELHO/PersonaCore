---
phase: 39-instrument-context-2-2
reviewed: 2026-10-05T14:25:52Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - scripts/phase39_ctx.py
  - tests/test_phase39_ctx.py
findings:
  critical: 0
  warning: 3
  info: 6
  total: 9
status: issues_found
---

# Phase 39: Code Review Report (3): the E6 driver, before its one MPS run

**Reviewed:** 2026-10-05T14:25:52Z
**Depth:** standard
**Files Reviewed:** 2 (diff base d28d802^, HEAD 45599e3)
**Status:** issues_found

## Narrative Findings (AI reviewer)

## Summary

I reviewed `scripts/phase39_ctx.py` (sha256 0a9dbf81…, the same bytes as the rehearsal identity)
and `tests/test_phase39_ctx.py`. I checked them against the frozen `phase39_prereg.py` doors,
39-CONTEXT D-01..D-30a, Rafael's rulings a-j, the 39-08 launch and crash rules, the `phase38_rank.py`
template, and the CPU rehearsal outputs.

Baseline: `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase39_ctx.py` gave
`125 passed in 64.52s`. ruff check and ruff format are both clean.

I ran everything on CPU, with the test module's own fake rigs, tmp roots or the tokenizer. I did not
run `run|crosscheck|emit|report` on the real root and did not load a checkpoint on MPS. Afterwards,
`find data results -name 'phase39_*'` lists only `data/phase39_rehearsal.json`, whose md5
(f3d2bf741598c21d0df6bbe5e17fc19e) is the same before and after the review.

**No BLOCKER under Rafael's rule.** I found nothing that changes a read value, a class or a count,
or that bricks the run or the ledger. Three WARNINGs are on the recovery paths and the cost block.
Results for each requested check:

1. **Gate STOP.** `passed = not unequal and all(row["equal"])` covers both ways the gate can fail:
   a rank mismatch (and `n_references`) through `phase38_rank.gate_reading`, and any copy cell whose
   `nll_sum` or `nll_mean` is not bitwise equal (`float.hex`). The work pass runs only `if passed`.
   GATE_FAILED writes the gate sidecar and the run sidecar (`reading_sha256 == {}`), and
   `build_record` stops at the common fields: gate rows, copy_equality, cells, gate2 and provenance.
   As evidence that condition 1 can hold on MPS, Phase 38's MPS gate reproduced 64/64 committed NLLs
   at `abs_nll_diff == 0.0` (`results/phase38_rank.json`).
2. **Classification through the door.** `_classified` iterates `prereg.cells(event)`, which is
   CELL_READINGS x SLOTS = 48 per event. I measured the full shape on the committed counts: 48 and
   48 cells, `baseline_table` 8 slots, `tie_audit` 48 cells. Each cell goes through
   `prereg.classify_cell(cell, values[r][s], k0[s])` with R_a = gate rank, R_q = n1, G_a = unit and
   G_q = gate-2 count. Counts come only from `class_counts`; the audit comes from `tie_audit`, which
   covers M2. REVERSE_DISAGREEMENT and undecided cells are tallied apart, and M2 is reported
   separately (`counts[RETRAIN_READING]`). adapter_off never reaches the door.
3. **nll_mean only.** `rank_rows`, `_rank_block` (R_q ranks, n1, median, rank_of_mean_nll, (ii)) and
   the gate all read `nll_mean`. `per_token` and `suffix_nll_sum` are read only in
   `_descriptive_block` and `_suffix_check`. I recomputed the rehearsal's ranks, medians and (ii)
   ranks from the raw sidecars with my own rank function: **16/16 blocks match**.
4. **D-30a.** `span_nll_tokens` is the pinned body line for line plus two extra cross-entropies on
   the same logits. The suffix mask starts at `len(context) - 1 + suffix_from`, which is the
   correct target index. `crosscheck` compares the CPU copy against the pinned
   `span_nll_from_ids(prompt_ids, taught[realized:])` per reading and entry. The rehearsal got
   432/432 bitwise.
5. **Ledger and crash.** Every refusal comes before the start line. The heartbeat writes a first
   beat at the start line, then a thread beats every 60 s. If the process dies after the start line,
   the start line stays open (no `finally` writes the end line). In that case:
   - Without a run sidecar, crosscheck and emit refuse. A re-run is refused with a misleading
     message (WR-01).
   - With a run sidecar, emit proceeds whatever the ledger's state (WR-02).
   - The operator recovery is plan 39-08's crash rules (i)/(ii), and they work as written.
6. **Preflight before the start line.** The checks run in this order: the I/O-free checks, the MPS
   check, the identity, outputs, open attempt, dirty tree, HEAD, tracked inputs, D-27 prereg drift,
   the disclosure, `require_launch("E6")`, both committed caps, `check_unit_caps` without the raised
   counts, inputs, the D-20 digests, `verify_a2_records` and `gate2`. The checks that run only
   inside `run()` (D-23b premise, the PERS-06 guards, `suffix_from` bounds, `minted_members`) cannot
   be pre-checked by the driver, so I measured them on all 216 entries and 8 anchors with the real
   tokenizer: **0 failures**, and `realized_injection` lies in [1, len-1] for every slot. None of
   them can fire mid-run on today's data.
7. **Cost.** The numbers are what plan 06 specifies, from `adapter_setup_high = 0.6377 s`: extra
   0.0014170 h, so 0.7307738 h ≤ 0.7424222 h. `within_stop` judges the projection, not the run
   (WR-03).
8. **Rehearsal record.** The values are correct. I traced every classification cell by hand
   against the precedence (for example, damage k16 pet_name drops 9/27 > 8/27 → INTERACTION_ONLY,
   and damage k78 birth_year → INSTRUMENT_SUFFICIENT), and they match. The (ii) anchor-side rank
   reads the same members, because Phase 38's main curve uses no `exclude`. Cell counts are correct:
   120 copy cells, 54 entries, 432 R_q/(ii)/suffix comparisons. The only defects in it are
   presentation (IN-03).

## Warnings

### WR-01: After a crash, a re-run refuses with "the E6 scoring has already run", and the driver gives no supported path to the new attempt that plan 08 rule (ii) allows

**File:** `scripts/phase39_ctx.py:600-601` (refusal), `:840` (comment)
**Issue:** Plan 08 crash rule (ii) applies when the run sidecar is missing: reconcile, keep every
partial sidecar as root-cause evidence, and "a new attempt needs Rafael's approved". But
`preflight` refuses while any `outputs(root)` file exists, and the gate sidecar plus earlier
reading sidecars do exist after such a crash. The message also states something false: the run
did not complete. The comment at :840 ("a crash keeps every reading already scored") suggests
those sidecars can be reused, but nothing in the code reads a reading sidecar without a run
sidecar. They are evidence only.

As a result, the operator must move files out of `data/` by hand. Nothing in the driver names that
step, and the refusal reads as "done", which is the wrong cue at exactly the moment rule (ii)
applies. Nothing is bricked: moving the files restores the path.

**Confirmed** (fake rig: the copy dies at the third reading, then reconcile, then preflight):
```
.venv/bin/pytest -q -s -p no:cacheprovider --rootdir=tests -c /dev/null -k test_probe_ <scratchpad>/r3/test_r3_probes.py
rerun refusal: [phase39_ctx] .../test_probe_rerun_after_crash_m0/data/phase39_ctx_gate.json exists: the E6 scoring has already run
```
**Fix:** In preflight, distinguish the two cases and fix the comment:
```python
present = [p for p in outputs(root) if p.exists()]
if present and not run_sidecar(root).exists():
    _prove(False, f"partial sidecars {present} from a crashed attempt (no run sidecar): reconcile the "
           "ledger, keep them as root-cause evidence by moving them to data/phase39_ctx_attempt<N>/, "
           "and relaunch only on Rafael's approved (39-08 crash rule ii)")
for path in present:
    _prove(False, f"{path} exists: the E6 scoring has already run")
```
Change the comment at :840 to "a crash keeps every reading already scored as evidence (nothing
resumes from it)". Add a test that pins both messages.

### WR-02: `emit` (and `crosscheck`) proceed while the run's ledger attempt is still open, so skipping rule (i) leaves a permanent "lost" line for a run that has a record

**File:** `scripts/phase39_ctx.py:1383-1424` (emit), `:914-981` (crosscheck)
**Issue:** The run sidecar is written before `phase36_ledger.append("end")`, so a death in between
leaves a complete run sidecar and an open start line. Neither `emit` nor `crosscheck` reads the
ledger. If the operator emits without first applying rule (i), or runs `reconcile` as rule (ii)
says for the other crash case, then:
- the ledger closes the attempt as `lost` (counted to its last beat);
- `append("end")` is refused from then on ("no open attempt");
- `_closed_row` therefore never reads the record's clock;
- the record names a run that the append-only ledger says produced nothing.

Rule (i) prevents this only if the operator classifies the crash correctly. Phase 38 has the same
gap (`phase38_rank.emit` also makes no ledger call).

**Confirmed** (fake rig: the end line raises after the run sidecar):
```
.venv/bin/pytest -q -s -p no:cacheprovider --rootdir=tests -c /dev/null -k test_probe_ <scratchpad>/r3/test_r3_probes.py
open runs after death: ['v6/39/E6/ctx']
EMITTED SCORED .../test_probe_emit_with_open_ledg0/results/phase39_ctx.json
record written: True | ledger still open: True
after reconcile: [('start', None), ('lost', 'sem registro de resultado')]
end after reconcile: [phase36_ledger] run v6/39/E6/ctx has no open attempt to end
```
**Fix:** Make `emit` refuse while RUN_ID is open on the root's ledger. `emit` is not on the ledger-call
census's allowed list, so the census must be widened explicitly to admit `open_runs` / `read_ledger`
in `emit`:
```python
_prove(
    RUN_ID not in phase36_ledger.open_runs(phase36_ledger.read_ledger(ledger_path)),
    f"the ledger attempt {RUN_ID} is still open: apply 39-08 crash rule (i) (append the end line) "
    "before emit; never reconcile a run whose run sidecar exists",
)
```
`emit` then needs a `ledger_path=None` keyword, which the fake chain passes. Optionally, also make
the rule (ii) message from WR-01 tell the operator never to reconcile when the run sidecar exists.

### WR-03: `cost.within_stop` judges the projection, not the run, so the record can say True for a run that overran stop (a)

**File:** `scripts/phase39_ctx.py:1271-1291`
**Issue:** `within_stop` is `projection_with_double_load_hours <= E6_STOP_HOURS`, which is a
constant 0.7308 ≤ 0.7424 for the full shape. It never reads `run_hours`. Stop (a) is about spent
hours: the ledger counts the record's `provenance.run` span against `1.5 x front_hours.E6`. So a
2 h run would publish `within_stop: True`, and the report renders it as `cost within_stop: True`.
Plan 08 Task 4 step 5 has to check `cost.run_hours <= E6_STOP_HOURS` by hand because the record
does not. This is a descriptive field and no class depends on it, but the label reads as a verdict
on the run.

**Confirmed:**
```
.venv/bin/python -c "...; run={'readings': list(p.READINGS), 'started_utc': '2026-10-06T00:00:00+00:00', 'finished_utc': '2026-10-06T02:00:00+00:00'}; x=c._cost(run); print(...)"
{'run_hours': 2.0, 'e6_stop_hours': 0.7424221732238463, 'within_stop': True}
```
**Fix:** Rename the field to `projection_within_stop`, and add
`"run_within_stop": run_hours <= prereg.E6_STOP_HOURS` next to it, still descriptive (D-03: the
committed stop is require_launch's). Update the plan-06 test that recomputes the cost block.

## Info

### IN-01: The heartbeat never names a shape

**File:** `scripts/phase39_ctx.py:749, 475, 550`
**Issue:** `state["shape"]` stays None for the whole run. Phase 38's `score_values` set it to the
slot, but `gate_cells`, `score_question` and `anchor_draws` set only `draw_index`, which also stays
stale through the 48 x 8 anchor draws of each reading. The rehearsal heartbeat shows
`"shape": null` in every beat. Liveness and reconcile seconds are unaffected, but a stall cannot
be located below the reading.
**Fix:** Call `state.update(shape=slot)` in `gate_cells` and `anchor_draws`, and
`state.update(shape=f"{entry['slot']}/{entry['seed_index']}")` in `score_question`.

### IN-02: The gate certifies the gate-pass load only, and the work pass scores a second load it never compares against

**File:** `scripts/phase39_ctx.py:759-772, 803-805`
**Issue:** D-18 / D-30 condition 1 are proved on the model loaded for the gate pass. The work pass
reloads each reading from the same files (I1), and nothing ties the two loads together beyond the
preflight file digests (and the base checkpoint, which is not hashed). The risk is low, since a
deterministic load of unchanged files gives the same weights, but the record's "gate passed" does
not literally cover the scored model.
**Fix (optional):** In the work pass, rescore the taught gate cell of the first slot with the
pinned function and `_prove` it bitwise equal to the gate sidecar's value. That costs one NLL per
reading and needs no pricing change.

### IN-03: The report uses "gate cells" for two different denominators

**File:** `scripts/phase39_ctx.py:1880-1885` vs `:1976-1977`
**Issue:** In the same report, "Copy equality … cells compared 120" counts candidates, while the
CPU section's "0 of 16 gate cells" counts (reading, slot) rows (the rehearsal report shows both).
The "Common unit" sentence also prints "Unit: draw" right after "The common unit (some hit in K
draws)".
**Fix:** Render the CPU figure as "gate rows (reading x slot)". Label the rate unit as "per-draw
rate unit: draw".

### IN-04: `report()` writes non-atomically, and a torn file blocks its own re-run

**File:** `scripts/phase39_ctx.py:2072`
**Issue:** `out.write_text(...)` with a crash mid-write leaves a partial report that the
write-once check then refuses to overwrite. The report is derived and cheap to regenerate (delete
it and rerun), and the os.replace census forbids the usual fix inside the driver.
**Fix:** Optionally, add a `phase25_run` text twin of `atomic_write_json`, or document "delete a
torn report and rerun".

### IN-05: The CPU sidecar records no git sha or module digests

**File:** `scripts/phase39_ctx.py:963-979`
**Issue:** `crosscheck` can run from a different tree than the MPS run, for example after a
driver fix that is reverted before emit, and leaves no trace. `emit` only sees the tree at emit
time. This needs a deliberate bypass, so it is a known limitation.
**Fix:** Add `git_sha()` and `module_sha256()` to the CPU sidecar, and add
`modules_changed_since_launch` for the cross-check to the cpu block.

### IN-06: `_classified` silently drops cells outside the scored shape

**File:** `scripts/phase39_ctx.py:1183-1192`
**Issue:** The filter is correct for rehearsal slices. On the real root, `emit`'s shape check
guarantees 48 cells per event, but `_decomposition` itself never asserts it. A later change to the
shape check would silently shrink the denominators.
**Fix:** In `_decomposition`, when `set(slots) == set(SLOTS)` and every CELL_READING is scored,
`_prove(len(classified[event]) == len(prereg.cells(event)))`.

---

_Reviewed: 2026-10-05T14:25:52Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

## Resolution (2026-10-05)

Rafael's rulings, pasted as his reply to the plan 39-08 Task 1 checkpoint, recorded verbatim:

- WR-01: corrigir.
- WR-02: corrigir (emit recusa com a tentativa aberta no livro-caixa). A mesma lacuna na Fase 38 fica registrada como limitação conhecida de lá; a rodada dela fechou com início e fim, então nada a refazer.
- WR-03: corrigir (projection_within_stop e run_within_stop).
- IN-06: corrigir.
- IN-05: corrigir.
- IN-01 e IN-03: corrigir.
- IN-02: corrigir, não limitação. Na passada de trabalho, repontuar com a função fixada a célula ensinada do portão (primeiro slot) em cada leitura e exigir igualdade bit a bit com o valor do sidecar do portão. Se diferir, PARE. Confirme que a projeção com essas 8 pontuações continua abaixo da parada (a).
- IN-04: limitação conhecida.

No novo ensaio: a mesma fatia do primeiro, em raiz nova. A divulgação do ensaio lista cada commit de correção com o motivo.

Traga para o "reviewed": a lista de commits, o resultado do novo ensaio (portão, igualdade bit a bit, checagem do IN-02), a projeção final e o resultado da suíte.

Orchestrator note (2026-10-05): the full suite launched at 45599e3 was stopped at 61% (no failure so far, EXIT=143 by kill) because these fixes supersede that HEAD; it reruns on the fixed, committed state.

Status: fixes pending; "reviewed" not yet given.
