---
phase: 42-dp-sgd-recipe-search-at-large
reviewed: 2026-10-14T07:27:23Z
depth: deep
review_base: 203afa3
files_reviewed: 4
files_reviewed_list:
  - scripts/phase42_prereg.py
  - scripts/phase42_recipes.py
  - tests/test_phase42_prereg.py
  - tests/test_phase42_recipes.py
findings:
  critical: 0
  warning: 5
  info: 2
  total: 7
status: issues_found
---

# Phase 42: Code Review Report

**Reviewed:** 2026-10-14T07:27:23Z
**Depth:** deep (call chains traced into phase25_points.train_stage, teach_persona.train_arm, personacore.training.loop / schedule / checkpoint, phase36_ledger, phase35_prereg._rule_e3_recall_threshold)
**Files Reviewed:** 4
**Status:** issues_found

## Summary

No BLOCKER. The D-05 seam, the take proof, the P22 ordering, the REFUSED-still-runs path and the
float/exact-rational comparison held under every experiment I ran. There are five WARNINGs:

- two gaps in the launch guards: a reconciled unit whose record already exists, and stage-2 entry
  that never executes the threshold fill;
- one wording edge in the frozen prereg: the null lead and the D-17 reading when points are REFUSED;
- two weaknesses in rehearsal enforcement: the device string is trusted, and a rehearsal with zero
  units is accepted.

The prereg finding (WR-03) is the one with a deadline. `scripts/phase42_prereg.py` closes for
good at the first tracked `results/phase42_*` record (42-RESEARCH Pitfall 3). Any change to it
needs Rafael's ruling before stage 1.

Every experiment below wrote only under pytest `tmp_path` or the session scratchpad. I checked
`git status --porcelain` before and after each probe run: it showed only the pre-existing
`.claude/scheduled_tasks.lock` (plus, at the first check, the background suite's transient
`results/phase23_resume_probe_a_dp_n8/`, which was there before my run and gone after).

Probe files (scratchpad, outside the repo):
`/private/tmp/claude-501/-Users-juliorcoelho-PersonaCore/832678fb-db05-4fae-b072-a03196279c5b/scratchpad/p42rev/test_p42_review_probes.py`
and `.../p42rev/test_p42_report_scan.py`. They reuse the committed rigs `_run_rig`, `_plant`,
`_e3_root` and `_counts` from `tests/test_phase42_recipes.py`, which root teach_persona and
phase25_points at `tmp_path`.
Run as: `cd <scratchpad>/p42rev && /Users/juliorcoelho/PersonaCore/.venv/bin/pytest -q -p no:cacheprovider -s --rootdir=. <file>`.

## Required paths: verdicts

| # | Path | Verdict | Evidence |
|---|------|---------|----------|
| 1 | D-05 rebinding: restore on every exception path and on a resumed run; any other reader during the call | **No defect** | `phase42_recipes.py:267-272`: the RHS is evaluated before any global is set, and `finally` restores. Only `_resume_guard` (before the rebind) and `expected_train_config` (after the restore) call `warmup_for`. `grep -rn "tp\.MAX_STEPS\s*=\|tp\.LR\s*=\|tp\.WARMUP_STEPS\s*="` finds no other rebinding in the call chain. phase25_run / phase36_ledger / phase14_recall / phase25_condition_c read none of the three (grep empty). The heartbeat thread reads none. `warmup_for` is ratio-invariant under the rebind: `(1e-3,20,200)`, `(3e-4,80,800)` and `(1e-3,80,800)` each give `warmup_for(200)= 20 warmup_for(800)= 80`. Existing tests `-k "warmup or take_proof or resume_guard"` pass (in the 11-passed run below). |
| 2 | Take proof vs sidecar train_config / live_mechanism: can it pass while the recipe did NOT take? | **No defect** | loop.py:575 builds AdamW with `train_config.lr`. loop.py:577 `build_scheduler(optimizer, train_config)` reads `warmup_steps`/`max_steps` (schedule.py:48-51). DPSGD owns no lr (grep of dpsgd.py). `live.composed_steps = resumed_from_step + len(composed)` with `len(composed) == tp.MAX_STEPS - resumed_from_step` (phase25_points.py:447-461). `live.clip_norm = float(seam.C)`, proved equal to `plan.dp_clip_norm` (:443). The real `tp.asdict(TrainConfig(...))` equals the v4.0 record's train_config key-for-key: `equal True set() {}`, so the faked blobs in the tests do not hide a shape mismatch. Resume: checkpoint.py:135 stores `asdict(train_config)`, the dict `_resume_guard` reads. |
| 3 | Crash between record write and end line; crash mid-training then relaunch (resume guard, lost attempts, NEVER reconcile) | **Finding WR-01** | Open attempt + record → refused "NEVER reconcile" (existing test). Mid-training crash → reconcile → relaunch resumes and lists the lost line (PROBE3b: `whole ['point_lr3e-04_t200_sigma0p500000'] lost_attempts ['lost']`). Gap: a record whose attempt was ALREADY reconciled lost passes preflight silently, and an end line can no longer be appended (WR-01). |
| 4 | Stage-2 entry with the threshold file untracked or dirty | **Finding WR-02** | Untracked → stage 1 (real repo now: `real stage = 1 threshold tracked&clean = False`). Dirty → `refuse_if_dirty` over `scripts` refuses first, and `_tracked_and_clean` is False. Gap: tracked-and-clean alone enters stage 2; the fill is never executed (WR-02). |
| 5 | P22 re-assert before any stage-2 training | **No defect** | `preflight` (`:595-596`) runs `p22_check()` at stage 2 before the `units` subset, `_stale_outputs`, `require_launch` and the first start line. `run` calls `preflight` before its loop. `test_stage_2_runs_p22_before_any_training` passes: a planted crossing leaves `calls["train"] == []` and an empty ledger. |
| 6 | REFUSED points still run, labelled only at emit | **No defect** | `preflight` `pending` (`:597-601`) depends only on record existence, never on a threshold. The threshold is read only in `build_record` → `_thresholds` (`:726-747`). `test_refused_still_runs` and the end-to-end test (2 REFUSED of 8, all 8 ran) pass. |
| 7 | Float comparison in point_verdict; exact_disagreements | **No defect** | `exact_disagreements(F_Y*ck/cn, (ck,cn), cn)` for every `ck` in `0..1008` (cn 1008) and `0..648` (cn 648): `1008 controls with a disagreement: 0 []`, `648 controls with a disagreement: 0 []`. `point_verdict` uses the fill's float as given (`:915`). REFUSED is checked after `_rate` validates both pairs, which is intended. |
| 8 | Null lead and the forbidden words / hedge scan | **Finding WR-03** | Hedge scan of a fully rendered scratch report (regex over ainda / possivelmente / talvez / provavelmente / possível / pode / poderia / may / might / could / likely / probably / perhaps / outra(s) receita(s)): the only hit is `'may'` in the dp_clip declared limit ("the norm distribution may differ"). That is a declared limit, not a hedge on the null. Gap: the null lead and D-17 "confirmada" are printed when points are REFUSED (WR-03). |
| 9 | Census of 42-RESEARCH Item 7 #1-#13 | **No defect** | `grep -F` over the 4 files for `train_arm(`, `os.replace`, `inject_lora`, `retention_perplexity`, `mitigation_point_verdict`, `!= 10`, `phase35_prereg._`, `floors_prereg`, `import phase35_prereg as`: all empty. One `== 10` substring hit, `tests/test_phase42_recipes.py:325 == 1008`, is not matched by the census regex `(?:==\|!=)\s*10(?![0-9_])` (test_phase21_sc5.py:196). #8: the prereg writes nothing at import (test_importing_the_prereg_opens_no_checkpoint). #9: unit records carry `provenance.run`; the E3 record carries emit provenance only. #10 / #11: `git check-ignore -v` gives `results/phase42e3_*/`, `results/phase42rh_*/`, `data/`, `checkpoints/` for every training output, and `results/phase42_point_x.json` is NOT ignored. #12: the last commits touching teach_persona / phase25_points / phase35_prereg are all Phase 35 (`3805beb`, `1e1e1c5`, `d850d0c`). #13: no `phase42_floors_prereg.py`. |

The targeted existing tests: `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase42_recipes.py -k "p22 or refused_still or warmup or take_proof or resume_guard or open_run or lost_attempts"` gives `11 passed, 26 deselected in 3.08s`.

## Structural Findings (fallow)

None provided.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: A unit record whose attempt was already reconciled lost passes preflight, and can never get its end line

- **File:** `scripts/phase42_recipes.py:582-594` (the `still` / NEVER-reconcile checks), `:597-601` (`pending`)
- **Claim:** preflight refuses only the case "attempt OPEN and record exists". Suppose the operator
  runs `phase36_ledger.py reconcile` on a run that crashed between `_write_once` and the end line,
  which the crash_rule forbids but nothing prevents. The record then exists with a `lost` line and
  no `end` line. Preflight passes, `pending` silently drops the unit, and the run continues. The
  ledger refuses an end line after `lost`, so the record can never be named by an end line. Census
  #9 (`tests/test_phase36_ledger.py:722`, every tracked MPS `results/phase4[0-3]_*` named by an end
  line) would then go red once the record is committed, with no in-driver warning beforehand.
- **Experiment:** `test_probe_reconciled_record_passes_preflight` in the probe file. It plants start +
  lost (NO_BEAT_FLAG) for `control_lr3e-04_t800`, writes its record under the scratch root, calls
  `preflight`, then `phase36_ledger.append("end", ...)`.
- **Observed:**
  ```
  PROBE3 preflight OK, pending = ('control_lr1e-03_t200', 'control_lr1e-03_t800')
  PROBE3 end-after-lost REFUSED: [phase36_ledger] run v6/42/E3/control_lr3e-04_t800 has no open attempt to end
  ```
- **Verdict:** CONFIRMED
- **Fix:** in `preflight`, refuse any unit whose record exists under `root` unless the ledger holds
  an `end` line with `record == unit_record(unit)` for its run id, naming the reconciled-with-record
  case explicitly.

### WR-02: Stage 2 is entered on "tracked and clean" alone; the threshold fill is never executed before the noised points train

- **File:** `scripts/phase42_recipes.py:481-488` (`stage`), `:595-596`
- **Claim:** at the real root, `stage()` returns 2 as soon as `THRESHOLD_FILE` and the three
  controls are tracked and unmodified. Nothing in preflight imports `phase42_threshold_prereg`.
  So a committed threshold file whose `fill("e3_recall_threshold", ...)` refuses or raises lets
  about 3.9 h of priced stage-2 MPS training run (4 x 0.4118 h + 4 x 0.5519 h, 42-RESEARCH Item 8). Its failure then
  surfaces only at `emit` (`_thresholds`, `:740`), when the hours are already spent. D-19 orders
  "threshold filled and committed" before stage 2; the driver proves "committed" but not "filled".
- **Experiment:** `test_probe_stage2_does_not_execute_the_threshold_fill`. It sets `_tracked_and_clean`
  to True, calls `stage(tmp_path)`, then checks `sys.modules`.
- **Observed:** `PROBE4 stage = 2 threshold module imported: False`
- **Verdict:** CONFIRMED
- **Fix:** at stage 2 in `preflight`, before `p22_check` / `require_launch`, import
  `phase42_threshold_prereg` and prove `set(E3_RECALL_THRESHOLD) == {recipe_key(r) for r in RECIPES}`.

### WR-03: The null lead and the D-17 reading present REFUSED points as "did not pass" (frozen prereg; needs a ruling before stage 1)

- **File:** `scripts/phase42_prereg.py:1025-1032` (`report_lead`), `:1131-1147` (`d17_reading`),
  ENTRIES `null_line` `:444-457`
- **Claim:** `report_lead` returns the null sentence whenever no label is PASSA, REFUSED included.
  When every point is REFUSED, line 1 of the report reads "nenhuma receita manteve o recall onde a
  garantia é vazia (0 de 8 pontos)". That is a negative answer about recipes whose question was
  refused. The REFUSED count first appears in the summary line, after the 8-line block. D-18 asks
  for REFUSED to be "reported with the same weight". `d17_reading` likewise reports the prediction
  as "confirmada" even though no threshold existed for the REFUSED recipes. This is the literal
  D-15 text ("If no point passes ..."), so the code follows the decision as written. The defect is
  the decision's edge case. Because the prereg closes at the first tracked `results/phase42_*`
  record, it can only be changed before stage 1.
- **Experiment:** `test_probe_all_refused_lead`: `report_lead`, `summary_line` and `d17_reading`
  with every point REFUSED.
- **Observed:**
  ```
  PROBE8 lead   : nenhuma receita manteve o recall onde a garantia é vazia (0 de 8 pontos)
  PROBE8 summary: 0 de 8 pontos passam; 8 REFUSED
  PROBE8 d17    : previsão D-17 confirmada: nenhum ponto passa
  ```
  The end-to-end test shows the same shape with 2 REFUSED: lead = null sentence, summary
  "0 de 8 pontos passam; 2 REFUSED".
- **Verdict:** CONFIRMED
- **Fix:** Rafael's ruling before stage 1. Options: the null lead only when no point is REFUSED (or
  the denominator counts only labelled points, plus the REFUSED count in the same line), and D-17
  read only over non-REFUSED recipes.

### WR-04: The rehearsal's "runs on CPU" check trusts the passed string; training resolves its own device

- **File:** `scripts/phase42_recipes.py:513-518` (`_launch_requirements`), `:559`; records `:336-341`
- **Claim:** for a scratch root, `_launch_requirements` checks only that the caller passed
  `device="cpu"`. Training never sees that value: `teach_persona.train_arm` resolves
  `preflight_device(strict=True)` / `RuntimeConfig()` itself (teach_persona.py:1818-1820), which
  gives MPS on this host. If the rehearsal script does not hide MPS (rehearsal_shape: "CPU with MPS
  hidden"), the rehearsal trains on MPS, scores on CPU, and publishes
  `provenance.run.device == "cpu"`. The D-21 "CPU rehearsal" would then rest on prose.
- **Experiment:** `.venv/bin/python -c "...preflight_device(strict=True)['device']; r._launch_requirements(real=False, device='cpu', identity=None, digests={})"`
- **Observed:**
  ```
  [preflight] device=mps cc=n/a torch=2.7.1
  resolved mps
  rehearsal check with device=cpu: accepted
  ```
- **Verdict:** CONFIRMED
- **Fix:** on a scratch root, prove `_device() == "cpu"` (the resolver `train_arm` uses), not just
  the passed `device` argument.

### WR-05: A zero-unit rehearsal identity satisfies the real launch, and no real record discloses the rehearsal

- **File:** `scripts/phase42_recipes.py:449-473` (`record_rehearsal`), `:513-525`
  (`_launch_requirements`), `:401-402` (disclosure only when not real)
- **Claim:** the real-root gate accepts any well-formed identity at the current driver and prereg
  digests, including `units == []` and `cpu_seconds == 0.0`, so it proves no D-21 leg ran. Real unit
  records also carry no rehearsal disclosure (`rehearsal_disclosure` is set only when
  `not pf["real"]`). The Phase 41 precedent publishes "The CPU rehearsal ran units ..." with the
  rehearsal git sha in each real record (`scripts/phase41_erasure.py:1033-1045`).
- **Experiment:** `test_probe_rehearsal_identity_with_no_units`: `record_rehearsal(path, units=(), seconds=0.0)`,
  then `_launch_requirements(real=True, device="mps", identity=..., digests=_disclosed_digests())`.
- **Observed:** `PROBE21 accepted identity units = [] cpu_seconds = 0.0`
- **Verdict:** CONFIRMED
- **Fix:** require a non-empty `identity["units"]` (or the D-21 leg set), and publish
  `{rehearsal_git_sha, units_read, rehearsal_module_sha256}` in every real unit record and in the
  E3 record.

## Info

### IN-01: `module_sha256` does not pin the code that implements D-05 or the threshold fill

- **File:** `scripts/phase42_recipes.py:53-67` (`MODULES`)
- **Claim:** the records' `module_sha256_at_launch` / emit `module_sha256` omit
  `src/personacore/training/schedule.py` (the warmup + cosine the take proof stands for),
  `loop.py`, `scripts/mitigation_budget.py`, `phase25_record.py`, `phase14_factset.py` and the
  threshold file whose fill sets every label. A clean tree at launch and `git_sha` keep the run
  regenerable, so this is provenance convenience only.
- **Experiment:** `python -c "... print(m, m in r.MODULES)"` for each path.
- **Observed:** all six print `in MODULES: False`.
- **Verdict:** CONFIRMED
- **Fix:** add these paths to `MODULES` (the threshold file at stage 2 / emit only, since it does
  not exist before 42-09).

### IN-02: `report()` writes non-atomically, after its write-once check

- **File:** `scripts/phase42_recipes.py:1120`
- **Claim:** `out.write_text(...)` is not atomic. A crash mid-write leaves a partial
  `results/phase42_recipes_report.md`, which the write-once check (`:1115-1119`) then refuses to
  overwrite. `emit` uses `_write_once` → `atomic_write_json`; the report has no atomic text
  counterpart.
- **Experiment:** `sed -n 1120p scripts/phase42_recipes.py` gives
  `out.write_text(render_report(_load(record_path)), encoding="utf-8")`. I did not test a crash
  mid-write.
- **Verdict:** CONFIRMED (non-atomic write); crash effect inferred
- **Fix:** write through a phase25_run atomic helper (census #2 allows `os.replace` only there).

## Refuted hypotheses (checked, no defect)

| Hypothesis | Experiment | Observed | Verdict |
|---|---|---|---|
| The take proof compares against a v4.0 train_config shape that the real `tp.asdict(cfg)` no longer has (tests fake the blob from the rebound globals) | `.venv/bin/python -` building `tp.TrainConfig(lr=tp.LR, warmup_steps=..., max_steps=..., batch_size=8, weight_decay=0.0, seed=1337, grad_accum_steps=8)` and comparing with the record | `equal True set() {}` | REFUTED |
| `warmup_for` reads teach_persona globals live, so a call inside the rebinding window returns a wrong warmup | rebound to three schedules, then `warmup_for(200)` / `warmup_for(800)` | `20` / `80` under every rebind | REFUTED (fragile but ratio-invariant) |
| The float verdict disagrees with the exact rational for some reachable control | full enumeration, all `ck` | 0 disagreements at cn 1008 and 648 | REFUTED |
| The rendered report carries a hedge on the null | regex scan of a scratch report | one `may`, inside the dp_clip declared limit | REFUTED |
| A new phase42 file trips an Item 7 census | greps and `git check-ignore` above | none | REFUTED |
| v4.0 `point_retention_ppl` and the new controls' `retention_ppl` come from different instruments (D-18 row) | `grep -n point_retention_ppl scripts/phase25_record.py` | `:718 "point_retention_ppl": capability["retention_ppl"]` (same `measure_condition_c` output) | REFUTED |

## Untested

- A REAL `phase25_points.train_stage` call under the D-05 rebinding (CPU or MPS). The tests fake
  train_stage. The structural trace (path 2) and the TrainConfig shape check cover the logic, but
  only the D-21 rehearsal exercises a real call. Not run: hours of compute, and it would write
  under `checkpoints/` and `data/` of the real tree.
- ε at T = 800 on glibc (42-RESEARCH Pitfall 4). This host is macOS; `build_record` already uses
  `isclose(rel_tol=1e-12)`.
- `phase36_ledger.py reconcile` against a live (heartbeating) Phase 42 run. Not exercised: it would
  need the milestone ledger or a long-running process.

---

_Reviewed: 2026-10-14T07:27:23Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_

## Resolution

**2026-10-14: Rafael's rulings.** Provenance: Rafael pasted this text into the execute-phase session as his reply to checkpoint 42-06. It may be a claude.ai draft that he adopted. It is quoted verbatim:

> Rulings 42-06 (Rafael, 2026-10-14):
>
> Achados:
> - WR-01: corrigir como proposto (preflight recusa todo unit com registro sem linha end que o nomeie).
> - WR-02: corrigir como proposto (no estágio 2, antes do p22_check, importar phase42_threshold_prereg e provar que o limiar cobre as 4 receitas).
> - WR-03: corrigir, com esta redação, antes do estágio 1. Seja R o número de pontos REFUSED e M = 8 − R os pontos julgados.
>   • R = 0 e nenhum PASSA: a primeira linha é a null_line literal de hoje.
>   • 0 < R < 8 e nenhum PASSA: "nenhuma receita manteve o recall onde a garantia é vazia (0 de M pontos julgados; R pontos REFUSED, sem limiar porque o controle da receita não aprendeu)".
>   • R = 8: "nenhum ponto foi julgado: os 8 pontos são REFUSED porque os controles não aprenderam; a pergunta do RECIPE-03 fica sem resposta nesta grade".
>   • D-17 lida só sobre os pontos julgados: "previsão D-17 confirmada nos M pontos julgados; R pontos REFUSED fora da leitura", ou, se M = 0, "previsão D-17 não lida: nenhum ponto julgado".
>   • Se algum ponto PASSA, a linha de resumo continua a primeira e já carrega a contagem de REFUSED. A redação da D-15 que não previa REFUSED foi falha da decisão original, não do código.
> - WR-04: corrigir como proposto (provar _device() == "cpu" no ensaio).
> - WR-05: corrigir como proposto (identidade de ensaio com units não vazio; rehearsal_git_sha, units_read e rehearsal_module_sha256 em cada registro real e no registro E3, como na Fase 41).
> - IN-01: corrigir (os seis caminhos no MODULES; o arquivo do limiar só no estágio 2 e no emit).
> - IN-02: corrigir (relatório escrito pelo helper atômico de phase25_run).
>
> Defaults: confirmo os cinco como estão: record_layout, unit_order, crash_rule, rehearsal_shape, d05_seam.
>
> Linha D-05: aceita.

**Orchestrator: premises measured before acting**
- WR-05: the Phase 41 field names `units_read`, `rehearsal_git_sha` and `rehearsal_module_sha256` exist as named (`scripts/phase41_erasure.py:1038-1040`). Holds.
- WR-03 "a linha de resumo continua a primeira" when a point passes: `report_lead` returns `summary_line(verdicts)` when PASSA is present (`scripts/phase42_prereg.py:1025-1033`). Holds.
- IN-02 "helper atômico de phase25_run": **does not hold for text.** `phase25_run` has only `atomic_write_json` (`scripts/phase25_run.py:118`), which serialises JSON. The Phase 39, 40 and 41 reports are all written by bare `write_text` (`phase39_ctx.py:2247`, `phase40_noise.py:2019`, `phase41_erasure.py:2955`). Census #2 allows `os.replace` only in phase25_run and phase25_record. Returned to Rafael for a ruling.
- O-01 (ε 1840.30 → 1840.29 in the `vacuous` text) is not ruled. Returned to Rafael.
- WR-03 with R = 1 or M = 1 renders "1 pontos". Applying his wording literally gives that plural; returned to Rafael.

**2026-10-14: Rafael's follow-up rulings.** He answered the orchestrator's AskUserQuestion in the session; the answers are quoted verbatim:

> IN-02: não corrigir. Fica o write_text, como nas Fases 39–41. O docstring de report() ganha o procedimento: um relatório parcial (não commitado) é apagado e gerado de novo a partir de results/phase42_recipes.json, que é escrito atomicamente. Minha regra anterior ("helper atômico de phase25_run") estava errada: esse helper não existe para texto.

> O-01: corrigir para 1840.29 antes do congelamento, num commit só de texto, com o teste que confere os quatro ε escritos nessa entrada contra point_epsilon arredondado em 2 casas.

> WR-03 gramática: escolher pela contagem ("1 ponto julgado", "1 ponto REFUSED"; plural nos demais), o resto da redação como escrito. Nota: na grade real R e M são sempre pares, porque o REFUSED vem do controle e atinge os dois pontos da receita juntos.

Premise measured: there are 4 recipes × 2 noised σ, and REFUSED is decided per recipe by the threshold fill. So R ∈ {0, 2, 4, 6, 8}. Holds.

**2026-10-14: Rafael's second follow-up.** These answer the two edge cases the executor raised after WR-03 was applied. He answered the orchestrator's AskUserQuestion; quoted verbatim:

> D-17 com R = 0: manter "previsão D-17 confirmada: nenhum ponto passa", espelhando a linha principal, que mantém a null_line com R = 0. Minha frase vale só para R > 0. Um ramo, commit próprio.

> M = 1: concordar pela contagem ("no 1 ponto julgado"), commit próprio, coerente com a regra de singular e plural da WR-03.

**Status per ruling: all applied.** Each was written test first, with the RED taken from the file's natural pre-fix state.

| Ruling | Commit | Outcome |
|---|---|---|
| WR-01 | `c81b483` | fixed: preflight refuses a unit record that no end line names |
| WR-02 | `a1ab8f1` | fixed: stage 2 executes the threshold fill (`E3_RECALL_THRESHOLD` covers the 4 recipes) before P22 and any ledger line. Real root only; the rehearsal passes its scratch fill per the confirmed rehearsal_shape |
| WR-04 | `4ba7a65` | fixed: a scratch root proves `_device() == "cpu"` |
| WR-05 | `0df9258` | fixed: a zero-unit identity is refused; real unit and E3 records carry `rehearsal_disclosure {units_read, rehearsal_git_sha, rehearsal_module_sha256}` |
| IN-01 | `5c9fa6c` | fixed: the five modules are in MODULES; the threshold file is pinned at real stage 2 and at emit |
| defaults | `f6472c3` | the five relabelled "confirmed by Rafael 2026-10-14"; no `_DEFAULT` label remains |
| WR-03 | `e7a2f66`, `147af58`, `e45fa99` | fixed with Rafael's wording: the lead and D-17 read judged points; D-17 at R = 0 keeps "confirmada: nenhum ponto passa"; singular or plural, and "no" or "nos", chosen by count |
| O-01 | `784fdc0` | fixed: 1840.29, the four ε values pinned by a test |
| IN-02 | `d54bc88` | not fixed (Rafael); `report()` documents the regenerate-from-JSON procedure |
| D-05 line | none | accepted |

Summary: `42-06-SUMMARY.md` (`b2bef6e`, amended `ec8dea4`). Quick run 93 passed; census subset 13 + 109 passed; ruff clean. The full suite and the frozen digests are recorded in the SUMMARY.
