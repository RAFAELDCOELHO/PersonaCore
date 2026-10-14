---
phase: 42-dp-sgd-recipe-search-at-large
plan: 06
subsystem: prereg-and-driver-review
tags: [e3, code-review, d-21, wr-01, wr-02, wr-03, wr-04, wr-05, in-01, in-02, o-01, defaults-confirmed]
requires:
  - .planning/phases/42-dp-sgd-recipe-search-at-large/42-REVIEW.md (findings and Rafael's dated Resolution; orchestrator-owned)
  - scripts/phase42_prereg.py, scripts/phase42_recipes.py (42-01..05)
provides:
  - "scripts/phase42_recipes.py: the end-line proof for existing records (WR-01), _threshold_fill run at real-root stage 2 before P22 (WR-02), the trainer-resolver CPU proof on a scratch root (WR-04), the non-empty rehearsal identity and _rehearsal_disclosure in every real unit record and the E3 record (WR-05), MODULES + the threshold-file pin (IN-01), the report() regenerate procedure (IN-02)"
  - "scripts/phase42_prereg.py: _CONFIRMED and the five confirmed defaults, ENTRIES refused_lead / d17_judged with _count, report_lead and d17_reading over judged points (WR-03), vacuous ε 1840.29 (O-01)"
affects: [42-07, 42-08, 42-09, 42-10, 42-11, 42-12]
tech-stack:
  added: []
  patterns: [stand-in fill module on a tmp sys.path with sys.modules restored, phase41 rehearsal-disclosure field names, phase41 _CONFIRMED label]
key-files:
  created: []
  modified:
    - scripts/phase42_prereg.py
    - scripts/phase42_recipes.py
    - tests/test_phase42_prereg.py
    - tests/test_phase42_recipes.py
decisions:
  - "WR-02 and the IN-01 threshold pin apply on the real root only: the confirmed rehearsal_shape runs scratch stage 2 with thresholds passed in, and no fill module exists before 42-09"
  - "The threshold pin is the sha256 of the executed module's __file__ (the bytes that ran); stage() already proves THRESHOLD_FILE tracked and clean"
  - "WR-03 d17_reading: Rafael's 'confirmada nos M pontos julgados' wording applies at R = 0 too (his ruling gave the R = 0 exemption only to the lead); held is None when M = 0; the PASSA branch is unchanged"
requirements-completed: []
metrics:
  duration: ~3 h (two executor passes)
  completed: 2026-10-14
  tasks: 1 (Task 2; Task 1 and Task 3 are the orchestrator's)
  files: 4
---

# Phase 42 Plan 06: review rulings applied Summary

Every finding in 42-REVIEW.md now has the ruling Rafael gave it. There are nine commits, one per ruling. Each fix was written test first, and its RED comes from the file's natural pre-fix state:

- **Fixed:** WR-01, WR-02, WR-03, WR-04, WR-05, IN-01 and O-01. WR-03 uses Rafael's exact wording.
- **Not fixed, by his ruling:** IN-02. `report()` keeps `write_text`; its docstring now documents the regeneration procedure.
- **Defaults confirmed:** the five planner defaults now carry his 2026-10-14 confirmation.
- **D-05 line:** accepted. No code change was needed.

Requirements are contributed to, not closed, by this plan; the orchestrator owns traceability.

## Rafael's replies (verbatim)

Provenance, as tagged in 42-REVIEW.md Resolution: Rafael pasted the first block into the execute-phase session as his reply to checkpoint 42-06. It may be a claude.ai draft that he adopted. The second block holds his answers to the orchestrator's AskUserQuestion in the same session.

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

> IN-02: não corrigir. Fica o write_text, como nas Fases 39–41. O docstring de report() ganha o procedimento: um relatório parcial (não commitado) é apagado e gerado de novo a partir de results/phase42_recipes.json, que é escrito atomicamente. Minha regra anterior ("helper atômico de phase25_run") estava errada: esse helper não existe para texto.

> O-01: corrigir para 1840.29 antes do congelamento, num commit só de texto, com o teste que confere os quatro ε escritos nessa entrada contra point_epsilon arredondado em 2 casas.

> WR-03 gramática: escolher pela contagem ("1 ponto julgado", "1 ponto REFUSED"; plural nos demais), o resto da redação como escrito. Nota: na grade real R e M são sempre pares, porque o REFUSED vem do controle e atinge os dois pontos da receita juntos.

## Commits, RED and GREEN

The REVIEW_BASE is 203afa3. RED is the first failure from the natural pre-fix state; GREEN is the same test after the fix.

| Commit | Ruling | Test | RED | GREEN |
|---|---|---|---|---|
| c81b483 | WR-01 | `test_a_record_no_end_line_names_is_refused` | `Failed: DID NOT RAISE <class 'SystemExit'>` | passed |
| a1ab8f1 | WR-02 | `test_stage_2_executes_the_threshold_fill_before_p22` | `DID NOT RAISE` (missing-module leg) | passed |
| 4ba7a65 | WR-04 | `test_a_rehearsal_trains_where_train_arm_resolves` | `DID NOT RAISE` | passed |
| 0df9258 | WR-05 | `test_real_records_disclose_the_rehearsal` + 3 updated tests | `KeyError: 'rehearsal_disclosure'` ×3; `DID NOT RAISE` (units == []) | 4 passed |
| 5c9fa6c | IN-01 | `test_module_digests_pin_the_schedule_and_the_fill` | `Extra items in the left set: scripts/phase14_factset.py, scripts/mitigation_budget.py ...` | passed |
| f6472c3 | defaults | `test_defaults_are_labelled` (updated) | `AttributeError: module 'phase42_prereg' has no attribute '_CONFIRMED'` | passed |
| e7a2f66 | WR-03 | `test_report_lead_and_d17_read_only_judged_points` + `test_report_lead_null_case` + end-to-end | lead `'... (0 de 8 pontos)'` where `'... não aprendeu)'` was expected; d17 `'confirmada: nenhum ponto passa'`; ENTRIES missing `refused_lead`/`d17_judged` | 91 passed |
| 784fdc0 | O-01 | `test_vacuous_text_carries_the_grid_epsilons` | `('800', ['1840.30', '519.70'], ['1840.29', '519.70'])` | passed |
| d54bc88 | IN-02 (not fixed) | `test_report_documents_the_regenerate_procedure` | `AssertionError: partial (uncommitted) ... not in 'Write results/phase42_recipes_report.md ONCE ...'` | passed |

What each fix does:

- **WR-01.** Preflight refuses every existing unit record that no end line of its own run_id names. The message names the case where an attempt was reconciled lost after the record was written. `_plant` in the recipes tests now writes start and end lines for the controls it plants.
- **WR-02.** `_threshold_fill()` imports `phase42_threshold_prereg` and proves that `set(E3_RECALL_THRESHOLD) == {recipe_key(r) for r in RECIPES}`. Any Exception raised inside it becomes a SystemExit naming the file.
  - It runs at real-root stage 2, before `p22_check`, `require_launch` and any ledger line.
  - emit's `_thresholds` calls the same helper.
  - The module attribute is `E3_RECALL_THRESHOLD`, per 42-09-PLAN.md lines 20, 27 and 111.
  - The test plants four stand-in modules on a tmp `sys.path`: missing, raising, three recipes, and the real 42-09 body.
- **WR-04.** On a scratch root, `_launch_requirements` proves that `_device() == "cpu"`. `_device()` is `preflight_device(strict=True)`, the same function object `teach_persona.train_arm` calls; the test asserts this.
- **WR-05.** The real launch and the real `build_record` refuse an identity with `units == []`.
  - Every real unit record and the E3 record publish `rehearsal_disclosure = {units_read, rehearsal_git_sha, rehearsal_module_sha256}`. These are the field names at scripts/phase41_erasure.py:1038-1040.
  - Records on a scratch root keep `{"this_is_the_rehearsal": True}`.
- **IN-01.** These five paths are added to `MODULES`:
  - `src/personacore/training/schedule.py`
  - `src/personacore/training/loop.py`
  - `scripts/mitigation_budget.py`
  - `scripts/phase25_record.py`
  - `scripts/phase14_factset.py`

  `THRESHOLD_FILE` stays out of `MODULES`. It is pinned only in the real root's stage-2 `module_sha256_at_launch` and in the E3 record's `provenance.module_sha256`.
- **Defaults.** `_CONFIRMED = "confirmed by Rafael 2026-10-14"` sits beside `_DEFAULT`. The label is swapped in the five entries only. An exec of the HEAD prereg against the new one shows exactly those five ENTRIES changed, and only by the label (`only label swapped: True`). After the swap, no entry carries `_DEFAULT`.
- **WR-03.** Two new ENTRIES, `refused_lead` and `d17_judged`, carry Rafael's wording. Their derivations cite "42-REVIEW.md Resolution, Rafael 2026-10-14", and `_count` chooses singular or plural by count.
  - The tests cover R ∈ {0, 2, 4, 6, 8}, the singular legs R = 1 and R = 7 (M = 1), and a PASSA leg with R = 2.
  - A word-bounded hedge scan covers every new text and has a non-vacuity check.
  - The end-to-end report's line 1 is now `... (0 de 6 pontos julgados; 2 pontos REFUSED, sem limiar porque o controle da receita não aprendeu)`.
- **O-01.** `point_epsilon(0.5, 800) = 1840.2946450499012`, which rounds to 1840.29. The commit changes only the text.
- **IN-02.** Not fixed. The docstring of `report()` gains the regeneration procedure.

After every commit, the quick run, the two census calls and ruff were green. The last gate, after d54bc88, gave:

- quick run: `93 passed`
- census call 1: `13 passed, 75 deselected`
- census call 2: `109 passed`
- ruff check: `All checks passed!`
- ruff format: `4 files already formatted`

The reviewer's probe file in the scratchpad was rerun but not edited:

- **PROBE3 (WR-01) and PROBE21 (WR-05)** now fail on the new refusals, which is expected: the defects are fixed.
- **PROBE3b** fails with `TypeError` because `_plant` now takes `ledger`. A copy with the new signature passes and prints the same `whole [...] lost_attempts ['lost']`.
- **PROBE4** still prints `imported: False`. That probe calls `stage()` alone, which did not change; the WR-02 fix lives in preflight.
- **PROBE8** now prints the R = 8 lead and `previsão D-17 não lida: nenhum ponto julgado`.

## Deviations from Plan

1. **WR-02 and the IN-01 threshold pin run on the real root only.** The orchestrator accepted this. The confirmed `rehearsal_shape` passes the real fill's thresholds into scratch stage 2, and `scripts/phase42_threshold_prereg.py` does not exist until 42-09. Requiring the import on a scratch root would break the D-21 rehearsal.
2. **The threshold pin hashes the executed module's `__file__`, not `_REPO/THRESHOLD_FILE`.** The orchestrator accepted this. In production both are the same file: `scripts/` is first on `sys.path`, and `stage()` proves the file is tracked and clean. The tests cannot plant a file inside the repository.
3. **WR-03 D-17 at R = 0.** Rafael's D-17 sentence carries no R = 0 exemption; only the lead does. So at R = 0, D-17 now reads "previsão D-17 confirmada nos 8 pontos julgados; 0 pontos REFUSED fora da leitura", where it used to read "previsão D-17 confirmada: nenhum ponto passa". If he wants the old sentence kept at R = 0, the change is one branch.
4. **WR-03 PASSA branch.** It is unchanged ("previsão D-17 não confirmada: <cells>; ..."). The cells it names are judged points by definition, because a REFUSED point never passes. `held` is now `None` when M = 0.
5. **WR-03 singular with "nos".** "o resto da redação como escrito" keeps "nos" in "confirmada nos 1 ponto julgado", which is ungrammatical in Portuguese. That case is unreachable on the real grid, where M is always even.
6. **WR-05 disclosure fields.** It publishes the three fields he named. It does not copy Phase 41's other keys: statement, launch sha, changed, commits.
7. **Test-only mechanics.**
   - The rigs stand `_device` in with `"cpu"`.
   - `_plant(root, ledger, unlearnable=None)` writes end lines.
   - The stage-2 tests compare against the planted ledger lines instead of `[]`.
   - `_untested_functions` requires the call `phase42_prereg._count(...)`, so the test calls it through the module name.
8. **IN-01 test bug.** It surfaced after the fix and was corrected before the commit: the test had read point records at stage 1.

## Threat Flags

None. No new endpoint, network path or file-write path. The driver still writes only through `_write_once` / `atomic_write_json`, plus `report()`'s documented `write_text`.

## Frozen digests

Pending orchestrator full suite (Task 3: HEAD, suite line and `shasum -a 256 scripts/phase42_prereg.py scripts/phase42_recipes.py` at the committed tree).

## Self-Check: PASSED

The nine commits c81b483, a1ab8f1, 4ba7a65, 0df9258, 5c9fa6c, f6472c3, e7a2f66, 784fdc0 and d54bc88 are all in `git log 203afa3..HEAD`. All four modified files exist.
