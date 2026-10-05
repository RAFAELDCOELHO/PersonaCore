---
phase: 39-instrument-context-2-2
plan: 04
subsystem: E6 driver part 1 (CTX-02)
tags: [driver, nll-copy, d-30, anchor-draws, preflight, ledger]
requirements-completed: []
dependency-graph:
  requires: [39-03 (prereg frozen at 9366134)]
  provides: [scripts/phase39_ctx.py part 1 (constants, sidecars, inputs, reading_model, span_nll_tokens, anchor_ids, anchor_draws, gate_cells, score_question, preflight)]
  affects: [39-05 run() + rehearsal identity, 39-06 cross-check + record, 39-07 report + census]
key-files:
  created:
    - scripts/phase39_ctx.py
    - tests/test_phase39_ctx.py
  modified: []
decisions:
  - "Refusal regex widened with [phase36_caps]: the natural check_unit_caps refusal (prereg.K patched to 49) carries that prefix"
  - "anchor_draws runs draw_all under phase36_probe.silenced() (stage_e6 parity) and proves K completions"
metrics:
  completed: 2026-10-05
  tasks: 3
  files: 2
---

# Phase 39 Plan 04: E6 driver part 1 Summary

The first third of the E6 driver: a torch-free-at-import skeleton, the D-30 copy of
`span_nll_from_ids` (per-token values plus the D-30a suffix sum, proved float.hex-equal to the pinned
function on fake_lm and a seeded tiny GPT), the anchor ids/draws, the gate cells, the question
scoring on `_guarded_span(entry)`, and a preflight that refuses every unsafe launch before the
ledger start line.

Requirements: this plan contributes to CTX-02; the orchestrator ticks requirements at phase close.

## Commits

| Task | Commit | What |
|------|--------|------|
| 1 | 783b9be | constants, sidecars, inputs, digests, reading_model keeping forbid, test rig |
| 2 | 52f144c | span_nll_tokens (D-30/D-30a), _same_bits, anchor_ids, gate_cells, anchor_draws, score_question |
| 3 | 6740ec5 | preflight with every refusal before the ledger start line, gate 2 included |

## RED, then GREEN (as printed)

- Task 1 RED: `E   ModuleNotFoundError: No module named 'phase39_ctx'` / `1 error in 0.95s`.
  GREEN: `7 passed in 2.85s`.
- Task 2 RED: `14 failed, 7 passed in 3.90s` (`AttributeError: module 'phase39_ctx' has no
  attribute ...`). GREEN: `21 passed in 4.26s`.
- Task 3 RED: `38 failed, 22 passed in 6.06s`. GREEN: `60 passed in 12.04s`.

## Acceptance lines (as printed)

- Task 1: `.venv/bin/python -c "import sys; sys.path[:0]=['scripts','src']; import phase39_ctx as c; print(c.RUN_ID, c.FRONT, c.LAUNCH_PATHSPEC, 'torch' in sys.modules, 'phase39_prereg' in sys.modules)"`
  printed `v6/39/E6/ctx E6 ('scripts', 'src', 'results', 'artifacts') False False`.
- Task 2 verify: `-k "copy or equality or per_token or suffix"` `8 passed, 13 deselected in 1.67s`;
  `-k "anchor or gate or question or minted"` `7 passed, 14 deselected in 1.25s`;
  `tests/test_phase14_scoring.py -k draw_all` `1 passed, 42 deselected in 1.82s` (the census
  lists `('scripts/phase39_ctx.py', 'anchor_draws')` as a call site, asserting, not decorated);
  `tests/test_phase21_sc5.py::test_instruments_unchanged_byte_for_byte` `1 passed in 0.51s`.
- Task 3 verify: `-k "preflight or refus or caps"` `43 passed, 17 deselected in 9.61s`;
  `tests/test_phase39_ctx.py tests/test_phase39_prereg.py tests/test_phase36_ledger.py
  tests/test_phase21_sc5.py tests/test_lora_inject.py` `189 passed in 27.13s`;
  `ruff check .` `All checks passed!`; `ruff format --check .` `358 files already formatted`.
- Plan verification: `tests/test_phase39_ctx.py tests/test_phase14_scoring.py
  tests/test_phase21_sc5.py tests/test_lora_inject.py tests/test_phase25_driver.py`
  `143 passed in 17.41s`.
- Other repo-wide script censuses (test_phase17_stats, test_phase20_correction,
  test_phase21_unit_continuation, test_phase23_ctrl, test_phase25_prereg, test_phase30_calibration,
  test_phase35_prereg, test_tokenizer_oracle, test_phase19_erasure): `314 passed in 69.25s (0:01:09)`.
- `git status --porcelain -- scripts tests results ledger`: empty. `find data -maxdepth 1 -name
  'phase39_ctx_*'`: nothing. `git diff --quiet 9366134 -- scripts/phase39_prereg.py
  tests/test_phase39_prereg.py`: unchanged; `shasum -a 256 scripts/phase39_prereg.py`
  `4355b88024b41463daef9b17285246e74b7577988cd95c01e33d293594858297`.
- Full suite not run (orchestrator override).

## What exists now

- `span_nll_tokens(model, context_ids, value_ids, device, *, suffix_from=None)` returns
  `{n_scored, nll_sum, nll_mean, per_token, suffix_from, suffix_nll_sum}`. It is the pinned body
  line for line, with a third `cross_entropy(reduction="none")` on the same logits and, for
  `suffix_from`, its own `reduction="sum"` call over a suffix-only mask.
- `gate_cells(model, tok, device, slot, state)` -> `{candidate: {pinned, copy, equal}}` over
  `reference_set_for(slot)`, under `silenced()`.
- `anchor_draws(model, tok, device, forbid, slot, reading)`: checks the forbid digest, then
  `assert_no_value_in_prompt(prompt_ids=ids)`, then `draw_all(..., anchor_seed_index(slot),
  n_samples=K - 1)`. Returns a DRAW_RECORD_KEYS record plus `stopped` and `prompt_ids`.
- `score_question(model, tok, device, entry, candidates, *, taught, state)`: checks the D-23b
  premise and guards the context, then makes one copy call per candidate. Only the taught value
  gets `suffix_from = realized_injection`.
- `preflight(*, root, ledger_path, device, readings, slots)` returns `{git_sha, module_sha256,
  device, gate, reconstruction, readings, slots, gate2}`.

## Deviations from Plan

### Auto-fixed / adjusted

**1. [Rule 3 - Lint] `os` not imported at module level.** The plan lists `os` among the module
imports, but nothing in part 1 uses it (ruff F401). Plan 05 can add it when `run()` needs it.
`subprocess` arrived with Task 3, where preflight first uses it.

**2. [Rule 1 - Test premise] Refusal regex includes `phase36_caps`.** The plan's regex covers
`phase39_ctx|phase39_prereg|phase36_ledger|phase38_rank`. The natural `check_unit_caps` refusal
(prereg.K patched to 49, message `max_k = 49 exceeds the committed cap 48`) raises with the
`[phase36_caps]` prefix, so the regex adds it instead of planting a fake message.

**3. [Rule 2 - Correctness] anchor_draws checks the draw count and silences stdout.** It runs
`draw_all` under `phase36_probe.silenced()`, as stage_e6 does. It also requires `len(completions)
== len(stopped) == K`, mirroring phase19_erasure's budget check. `score_question` updates
`state["draw_index"]` per candidate, as gate_cells does.

**4. Transient lint in the intermediate commits.** Commits 783b9be and 52f144c had ruff F401 on
`phase36_caps`, `git_sha` and `refuse_if_dirty`. The plan requires these module-level imports
(the rig monkeypatches `phase39_ctx.refuse_if_dirty`), but only preflight uses them, and it
arrived in Task 3. `ruff check .` is clean at 6740ec5.

Prereg untouched; no gsd-sdk mutation handler called; STATE/ROADMAP/REQUIREMENTS/PLAN files not
edited.

## Known Stubs

None. The usage docstring names `run|crosscheck|emit|report`, which plans 05-07 add. There is no
`__main__` dispatcher yet.

## Self-Check: PASSED

- FOUND: scripts/phase39_ctx.py, tests/test_phase39_ctx.py
- FOUND: 783b9be, 52f144c, 6740ec5
