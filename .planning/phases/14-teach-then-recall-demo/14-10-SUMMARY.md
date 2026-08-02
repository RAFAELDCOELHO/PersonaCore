---
phase: 14-teach-then-recall-demo
plan: 10
subsystem: evidence
tags: [controls, report, pre-registration, d-11, d-20, d-12, d-22]
requires:
  - personacore.dialogue.build_recall_prompt
  - personacore.evaluation.masked_perplexity
  - personacore.lora.adapter_disabled
  - personacore.lora.set_adapter_enabled
  - teach_persona.COLLAPSE_PPL_TRIGGER
  - phase14_factset.SLOT_FORMS
provides:
  - scripts/phase14_recall.py::run_fairness_control
  - scripts/phase14_recall.py::run_collapse_control
  - scripts/phase14_recall.py::run_bit_identity_control
  - scripts/phase14_recall.py::write_recall_report
  - scripts/phase14_recall.py::assert_report_not_clobbered
  - scripts/phase14_recall.py::draw_all
affects:
  - 14-11 (runs this harness end to end and records the verdict)
tech-stack:
  added: []
  patterns:
    - "framing committed as module-level string constants BEFORE the run it frames (D-20)"
    - "AST-parsed structural guard on a dangerous keyword argument"
    - "report writer exercised on synthetic records so it cannot first fail after a long run"
key-files:
  created: []
  modified:
    - scripts/phase14_recall.py
    - tests/test_phase14_scoring.py
decisions:
  - "The fairness control runs with the adapter DISABLED — the inference it qualifies is about the base"
  - "Fairness runs on the CORE tier only; the soft tier feeds no gate, so its question validity is not load-bearing"
  - "The bit-identity control builds its own CPU pair rather than reusing the caller's device-resident model"
metrics:
  duration: ~50 min
  completed: 2026-08-02
---

# Phase 14 Plan 10: D-11 Controls + Recall Report Writer Summary

The three D-11 controls and `write_recall_report` land in `scripts/phase14_recall.py`, with D-20's
three-part reconciliation and its pre-registered failure branch committed as report text before the
run that will produce the numbers they frame.

## What Was Built

**`run_fairness_control(model, tok, device, forbid, questions, statements)` — D-11.1.**
Places each fact's own first-person taught statement (`SLOT_FORMS[slot].ans1`) in the `<|system|>`
persona span and asks the same recall question **with the adapter disabled**, greedy plus
`N_SEEDED_SAMPLES`, scored by `contains_value`. It is the only call site in the file that passes
`persona=`. It runs adapter-off deliberately: D-11.1 exists to qualify the *closed-book* (adapter-off)
arm, so measuring the adapted model — which already has the fact in its weights — would answer a
different question. `_prove`s that each fairness prompt actually carries its value, so a
misconstructed persona span cannot silently produce a meaningless zero.

**`run_collapse_control(model, tok, device, forbid, values)` — D-11.2.**
`masked_perplexity` on `data/dialog_val.bin` + `data/dialog_val_mask.bin` with the adapter on, then
again inside `adapter_disabled`; denominators are `_prove`d equal so the delta measures the adapter
and not the corpus. Six `UNRELATED_QUESTIONS` (touching no locked or soft slot, `_prove`d value-free)
run greedy through both arms for paired transcripts. `COLLAPSE_PPL_TRIGGER` and `replay_required` are
imported lazily from `teach_persona` — one definition, so this control and D-15's calibration verdict
stay on one scale.

**`run_bit_identity_control(tok, questions)` — D-11.3.**
Builds its own CPU-pinned pair via `RuntimeConfig(device="cpu")`: an un-injected model A from
`convbase_slim.pt`, and a model B with the adapter injected, loaded, and `set_adapter_enabled(..., False)`.
Full logits compared with `torch.equal` over several held-out questions plus the empty-question
scaffold; the max absolute difference is recorded alongside the boolean so the report states a
measured number rather than only an assertion.

**`write_recall_report(records, controls, provenance_lines)`.**
Fourteen sections in fixed order, carrying the `measure_inflation.py:66-75` clobber guard (also called
at the top of `main()` so a multi-hour run cannot discover the refusal at the end). Every framing
string is a module-level constant — `REPORT_OPENER`, `FAIRNESS_OPENER`, `RECONCILIATION_A/B/C`,
`FAILURE_BRANCH`, `COLLAPSE_OPENER`, `BIT_IDENTITY_OPENER`, `SOFT_TIER_SECTION`,
`THREATS_TO_VALIDITY`, `SHIP_DECISION_HEADER` — so a reviewer can diff the framing independently of
the numbers, and `git log -S` shows it predates the run (verified: `48d557a`).

**`main()` wiring:** scored recall → closed-book control → the three D-11 controls → `write_transcripts`
→ `write_recall_report`.

## D-11.1's `persona=` trap, closed

14-01 flagged that nothing enforced the ordinary recall path omitting `persona=`. Two changes close it:

1. `complete_question` was split — the seeded draw loop moved to `draw_all(model, tok, prompt_ids, ...)`,
   which takes prompt IDS. The fairness control shares that loop instead of copying it, and
   `complete_question` keeps a two-positional-argument `build_recall_prompt(tok, question)` and nothing else.
2. `tests/test_phase14_scoring.py::test_persona_argument_is_scoped_to_the_fairness_control` parses the
   module's **AST** (not its source text — the docstrings discuss `persona=` at length precisely because
   it is the dangerous argument), collects every `build_recall_prompt` call site tagged with its
   enclosing function, and asserts exactly one passes `persona` and that it is `run_fairness_control`.
   Every other call site must pass zero keywords.

`tests/test_phase14_demo.py` already pins the demo half (`persona=` absent from that source entirely);
this is the harness half, where the argument legitimately appears exactly once.

## D-20 reconciliation — consistency with the committed record

Part (a) quotes 14-RESEARCH §F4's probe list verbatim as a list rather than the plan's summary line.
The plan and 14-CONTEXT D-20 both cite `i have a dog named zorp.` → `i have a dog named rose.` as a
single probe; the underlying measurements are two — F4's warm-turn probe returned
`i have a dog named my name is cuddling.` (frame copied, value substituted), and `rose` is the
dog-name slot's measured **closed-book** prior from D-01. The report states both and notes explicitly
that D-20's one-liner compresses them, so the reconciliation neither contradicts nor silently
"corrects" the committed decision record.

Part (c) names D-13's held-out families as the evidence distinguishing (i) knowledge-then-extraction
from (ii) stimulus-response completion, and cross-references `## Recall Results — Core Tier` by
section name rather than leaving the link implicit.

## Deviations from Plan

**1. [Rule 3 — blocking] `estimate_loss` removed from the collapse control's docstring**

- **Found during:** Task 2
- **Issue:** The plan's action text asks the comment to name `estimate_loss` as the disallowed
  metric, but its own acceptance criterion and Task 1's require `grep -c "estimate_loss"
  scripts/phase14_recall.py` to return 0. Both cannot hold.
- **Fix:** The mechanical criterion wins. The docstring says "the training loop's 20-random-batch
  mean loss estimator is DISALLOWED for gates (Phase 12 12-02)" — same content, no identifier.
- **Commit:** `3558e30`

**2. [Rule 2 — missing critical functionality] The fairness control runs adapter-OFF**

- **Found during:** Task 1
- **Issue:** The plan's action text does not state the adapter state. D-11.1's text does: the control
  establishes that *the base* can answer when the fact is in context, which is what makes an
  adapter-off closed-book failure readable as "no memory".
- **Fix:** Wrapped in `adapter_disabled(model)`, with the reason in the docstring.
- **Commit:** `121efb8`

**3. [Rule 2] Signature and scope choices the plan left open**

- `run_fairness_control`'s sixth parameter is a `{fact_id: statement}` mapping (named `statements`,
  not `facts`), built in `main()` from the lazily-imported fact set — the control never reaches for
  fact strings itself.
- `run_collapse_control` takes `values` so its `_prove` has something to check, per the plan's own
  "values passed in as an argument".
- Fairness runs on the core tier (`core_taught + core_held_out`, 216 questions) rather than all 270:
  it qualifies the questions feeding the two GATED numbers, and the soft tier feeds neither.
- **Commits:** `121efb8`, `3558e30`, `48d557a`

**4. [Rule 2] A runnable check for the report writer**

- **Issue:** `write_recall_report` would otherwise first execute at the END of a multi-hour scored
  run — a `KeyError` in one table row would cost the whole run rather than a red test.
- **Fix:** `test_recall_report_carries_every_preregistered_section` renders it end to end on
  synthetic records into `tmp_path` and asserts every required heading, the section ordering, the
  D-20 parts, the `2309.12288` citation, `no bearing`, D-12's non-amendment clause, `331,776`, and
  the `PENDING — user decision at checkpoint.` line.
  `test_recall_report_refuses_to_clobber_a_recorded_verdict` pins the guard, the PENDING pass-through,
  and `--force`.
- **Commit:** `48d557a`

## Run-Shape Impact (for 14-11)

| arm | questions | completions |
| --- | --- | --- |
| scored recall + closed-book (14-06) | 270 | 4,860 |
| fairness control (core tier, greedy + 8) | 216 | 1,944 |
| collapse transcripts (6 questions × 2 arms, greedy) | 6 | 12 |
| bit identity (forward passes, no generation) | 5 | — |
| **total** | | **6,816 completions** at `RECALL_MAX_NEW_TOKENS = 48` |

The collapse control additionally sweeps `data/dialog_val.bin` twice (~270,203 scored targets per
sweep) and the bit-identity control loads two extra CPU copies of the 13.9M base.

## What Was NOT Touched

- `TAUGHT_THRESHOLD = 0.2486` / `HELDOUT_THRESHOLD = 0.2000` — unchanged, `grep`-verified.
- `SAMPLE_TEMPERATURE` / `SAMPLE_TOP_P` — unchanged, so
  `test_decode_settings_match_the_scoring_harness` stays green.
- `TAUGHT_FAMILY_IDS` / `HELDOUT_FAMILY_IDS`, `REAL_RUN_SECOND_PERSON`, `REAL_RUN_REPLAY_RATIO`.
- No shared orchestrator artifact (`STATE.md`, `ROADMAP.md`) was modified.
- No `results/` file was written — the harness's report path is produced by 14-11's run.

## Adapter Absence

`checkpoints/persona_adapter.pt` does not exist yet (14-11 produces it). `run_bit_identity_control`
and `load_adapted_model` are the only code paths that read it, both are reachable only from `main()`,
and the whole test suite (381 passed, 6 skipped) runs green without it.

## Artifacts

Nothing gitignored was produced. No checkpoint, bin, or `results/` file was created — this plan is
code and tests only, and the sample report rendered during development went to the scratchpad.

## Verification

| Check | Result |
| --- | --- |
| Task 1 automated verify (fairness + bit identity) | PASS |
| Task 2 automated verify (collapse, lazy edge) | PASS |
| Task 3 automated verify (sections + `main()` wiring) | PASS |
| `grep -c "estimate_loss" scripts/phase14_recall.py` | 0 |
| `grep -c "COLLAPSE_PPL_TRIGGER = " scripts/phase14_recall.py` | 0 |
| `.venv/bin/pytest -q` | 381 passed, 6 skipped |
| `.venv/bin/ruff check . && ruff format --check .` | clean |
| `git log -S "Pre-Registered Failure Branch" -- scripts/phase14_recall.py` | `48d557a` |
| `teach_persona` / `phase14_factset` absent from `sys.modules` after import | PASS |

## Commits

| Commit | Task |
| --- | --- |
| `121efb8` | Task 1 — D-11.1 fairness + D-11.3 bit identity, `draw_all` extraction, AST guard |
| `3558e30` | Task 2 — D-11.2 no-collateral-collapse |
| `48d557a` | Task 3 — `write_recall_report`, pre-registered framing constants, `main()` wiring |

## Self-Check: PASSED

- `scripts/phase14_recall.py` — FOUND
- `tests/test_phase14_scoring.py` — FOUND
- `121efb8` — FOUND
- `3558e30` — FOUND
- `48d557a` — FOUND
