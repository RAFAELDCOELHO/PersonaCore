---
phase: 30-replay-bearing-adversarial-recipe-and-its-own-control
plan: 04
subsystem: v5.0 calibration record (results/phase30_calibration.json)
tags: [ARECIPE-02, D-08, D-09, D-11]
requires: [scripts/phase30_calibration.py (30-03), scripts/phase30_points.require_calibrated_recipe (30-02)]
provides: [results/phase30_calibration.json — the first committed v5.0 result]
affects: [Phase 31-34 (every later v5.0 result must descend from 4339f2b; phase29_prereg.py, phase25_record.py, phase20_gate_coverage.py, phase30_calibration.py now correctable only by dated continuation)]
tech-stack:
  added: []
  patterns: [write-once emitter run once from a clean tree, single-file record commit, developer checkpoint before an irreversible result]
key-files:
  created:
    - results/phase30_calibration.json
  modified:
    - tests/test_phase29_prereg.py
decisions:
  - "Developer approved the record at the D-08 checkpoint (verbatim below)."
  - "Developer ruling (option 1): test_paths_are_distinct_from_every_v4_path reads the v4 set at tag v4.0, not HEAD."
requirements-completed: []
metrics:
  duration: ~45 min (incl. one 27-min phase-gate suite)
  completed: 2026-09-25
---

# Phase 30 Plan 04: commit the ARECIPE-02 calibration record — Summary

The orchestrator executed this plan inline, because Task 1 is a single command. The emitter ran once on the clean committed tree at `53a62b2` and exited 0. The developer approved the record at the checkpoint. It was committed alone as `4339f2b`, and it is the first v5.0 result.

Requirement ticks: the orchestrator/verifier rules on ARECIPE-02. This plan marks nothing complete.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1+3 | `4339f2b` | data(30-04): commit ARECIPE-02 calibration record (MIN_REFUSAL_SCORED_TOKENS re-derived = 15) |
| fix | `094fe97` | test(30-04): anchor the v4-path disjointness check at tag v4.0, not HEAD (dated continuation, developer ruling) |

## Evidence

- Preconditions before the emit:
  - `git status --porcelain scripts src tests results` was empty.
  - `git diff --stat 7d29d51 HEAD -- scripts src tests results` was empty (only `.planning/` changed since 30-03's commit).
  - `results/phase30_calibration.json` was absent.
  - `git ls-files 'results/phase3*'` was empty.
- Emitter output: `.venv/bin/python scripts/phase30_calibration.py` exited 0 and printed `[phase30_calibration] derived floor 15 at target 0.2 — wrote results/phase30_calibration.json`.
- The plan's verify one-liner printed `ok {'attack_pool_episodes': 336, 'clean_scored_tokens': 2719, 'clean_tokens': 7581, 'pool_prompt_tokens': 26054}`.
- Mask fraction at the floor: 0.20062055591467357; one token below it: 0.19361485693419234.
- `bins_identical_advr_vs_adv`: true.
- `recipe.n8` and `recipe.n64` share seed 1337, max_steps 200, min_refusal_scored_tokens 15, and replay_source `data/dialog_train.bin` + `data/dialog_train_mask.bin`. They differ in n_facts (8 vs 64) and replay_windows (32 vs 256).
- `descriptive_step_mix` is marked `gates_nothing: true`. Each step has 8 teaching windows (2048 tokens) against 32 replay windows (8192 tokens) at n8 and 256 replay windows (65536 tokens) at n64.
- Provenance: `provenance.git_sha == provenance.head_at_write == HEAD` (`53a62b2`) at the time of writing.
- The commit holds exactly one file: `git show --name-only --format= 4339f2b` prints `results/phase30_calibration.json`, and `git ls-files 'results/phase3*'` lists only that file.

## Checkpoint (D-08) — developer approval, verbatim

> Confirma opção 1: commita results/phase30_calibration.json sozinho, mensagem data(30-04): .... Roda os guards de ancestralidade invertidos e a suíte completa como gate da fase. derived_floor=15 medido ao vivo confirma exatamente a explicação estrutural já prevista em Calibration — replay fora do bin de ensino — fechando a pergunta que motivou a rodada de pesquisa desta fase com resposta empírica, não presumida.

## Deviation: a latent Phase 29 test went red on the first v5.0 record

After the commit, the flipped guards (`tests/test_phase30_calibration.py`, `tests/test_phase29_prereg.py` and `tests/test_phase30_points.py`) gave 1 failed, 115 passed. The failure was `test_paths_are_distinct_from_every_v4_path`. It read the "v4" set as every file tracked under `results/` at HEAD, so the new v5.0 record matched its own declared V5 path. Neither the record nor `phase29_prereg.py` was at fault. The developer ruled, verbatim:

> Confirma opção 1: conjunto v4 lido de `git ls-files results` na tag v4.0 (fixa, imutável), não em HEAD (móvel, continuará mudando durante v5.0 inteira). Nota de docstring datada 2026-09-25 explicando a correção. Checagem permanece genuinamente real — ainda detectaria um caminho V5 colidindo com qualquer arquivo real de v4.0 — só corrigida para ancorar contra referência fixa, mesma disciplina que RPT-03's teste de dependências já aplicou na Phase 28 comparando contra tags, não contra HEAD móvel.

Fix `094fe97`: the test reads `git ls-tree -r --name-only v4.0 results`, and its docstring carries a dated 2026-09-25 paragraph.

- **The check still bites:** among the 210 v4.0 files, a fake V5 pattern `results/phase25_point_*.json` hits 44, and the real calibration path hits 0.
- **The tag reaches CI:** `v4.0` is on origin (`git ls-remote --tags origin`), and CI checks out with `fetch-depth: 0`.

## Phase gate

- Flipped guards after the fix: 116 passed.
- Full suite at `094fe97`: **3071 passed, 4 skipped, 0 failed** in 26:49 (`EXIT=0`).
