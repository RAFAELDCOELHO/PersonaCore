---
phase: 14
plan: 07
subsystem: LoRA teaching driver + calibration decision rule
tags: [D-09, D-14, D-15, D-21, D-22, W-02, W-03, B-02, LORA-02, PITFALLS-P5, PITFALLS-P7, DEMO-05, DEMO-06]
requires:
  - scripts/teach_persona.build_bins
  - scripts/teach_persona.render_episodes
  - scripts/teach_persona.arm_outputs
  - scripts/teach_persona.arm_spec
  - scripts/teach_persona._require_go_verdict
  - scripts/phase14_factset.PARAPHRASES_PER_FACT_TARGET
  - scripts/phase14_factset.render_family
  - scripts/phase14_factset.FAMILIES
  - personacore.training.train
  - personacore.lora.inject_lora
  - personacore.lora.mark_only_lora_trainable
  - personacore.lora.snapshot_params
  - personacore.lora.lora_state_dict
  - personacore.lora.adapter_disabled
  - personacore.checkpoint.export_adapter
  - personacore.evaluation.masked_perplexity
  - personacore.preflight.preflight_device
  - checkpoints/convbase_best.pt
  - data/dialog_val.bin
provides:
  - scripts/teach_persona.train_arm
  - scripts/teach_persona.build_arm_bins
  - scripts/teach_persona.CALIBRATION_DECISION_RULE
  - scripts/teach_persona.lock_thresholds
  - scripts/teach_persona.lock_family_allocation
  - scripts/teach_persona.replay_required
  - scripts/teach_persona.first_person_wins
  - scripts/teach_persona.CAL_MARGIN_K
  - scripts/teach_persona.THRESHOLD_DISCOUNT
  - scripts/teach_persona.THRESHOLD_FLOOR
  - scripts/teach_persona.SATURATION_DELTA
  - scripts/teach_persona.HELDOUT_VARIANCE_TRIGGER
  - scripts/teach_persona.COLLAPSE_PPL_TRIGGER
  - scripts/teach_persona.REGISTER_WIN_MARGIN
  - scripts/teach_persona.RATIO_DECIMALS
  - scripts/teach_persona.LORA_CFG
  - scripts/teach_persona.CALIBRATION_REPORT
  - checkpoints/persona_adapter.pt (the real arm's export path, now wired)
affects:
  - "plan 14-09 (runs the three calibration arms through train_arm; applies CALIBRATION_DECISION_RULE to their numbers)"
  - "plan 14-11 (runs `teach_persona.py real`, which now exports checkpoints/persona_adapter.pt)"
  - "scripts/phase14_recall.py (unblocked — its ADAPTER_PATH is now produced)"
  - "plan 14-08 (the Gradio demo loads the same persona_adapter.pt)"
tech-stack:
  added: []
  patterns:
    - "the whole bins half behind one seam (build_arm_bins), so no arm can train on bins built by a different code path"
    - "arm-conditional verdict gating: the real arm gates on the calibration verdict, the calibration arms cannot (they produce it)"
    - "decision-rule boundaries round the measured ratio before comparing, so 'exactly on the boundary' means the decimal value and not whichever double brackets it"
    - "allocation invariants live in a _refuse_move contract function; the policy function reads as policy"
    - "refusals printed rather than returned, keeping the (taught, heldout) shape while the calibration report captures the reason"
key-files:
  created: []
  modified:
    - scripts/teach_persona.py
    - tests/test_phase14_teaching.py
key-decisions:
  - "The real arm's adapter exports to checkpoints/persona_adapter.pt, breaking the phase14_{arm} naming on purpose — that is the path 14-06's harness and 14-08's demo already hardcode"
  - "main() delegates to train_arm rather than duplicating the bins path, so `teach_persona.py real` is one command that teaches and exports"
  - "seed_everything runs twice: once before the bins (preserving 14-04's determinism) and again immediately before the GPT build, which is the seed that owns training data order"
  - "RATIO_DECIMALS = 10 added beyond the plan's seven literals — without it replay_required(2.0, 2.2) returns True, contradicting the rule's own stated boundary semantics"
  - "MAX_STEPS = 200 is committed but deliberately NOT pinned by a test: it is one of the numbers calibration measures (A3)"
patterns-established:
  - "Cross-plan artifact-path contracts get their own test naming both consumers, instead of being discovered at runtime by the consumer"
  - "A boundary test asserts BOTH the exactness premise and the trap the premise defends against, so deleting the defense turns the test red"
requirements-completed: [DEMO-05, DEMO-06]
duration: 32min
completed: 2026-08-02
---

# Phase 14 Plan 07: LoRA Teaching Driver + Calibration Decision Rule Summary

**`train_arm` teaches a persona into 331,776 LoRA parameters with the frozen base proven bit-identical, and all four calibration derivations are committed as pure functions before a single calibration number exists.**

## Performance

- **Duration:** ~32 min
- **Started:** 2026-08-02T04:44Z
- **Completed:** 2026-08-02T05:00Z
- **Tasks:** 3/3
- **Files modified:** 2

## Accomplishments

### Task 1 — the LoRA training half (`e61a184`)

`train_arm(arm, *, facts, family_ids, second_person, replay_ratio)` runs the full chain:
verdict gate → refuse-to-rerun → preflight → bins → load-before-inject → LoRA-only freeze →
masked `train()` → canary → `export_adapter` → adapter-ON/OFF PPL pair → provenance echo.

The load order is the load-bearing part and is asserted by the plan's own source-inspection
check: `load_state_dict` precedes `inject_lora` (injecting first would wrap parameters that the
base state dict cannot then address), and `model.to(device)` precedes `snapshot_params`
(`torch.equal` raises on cross-device tensors, so the canary would crash instead of proving
anything).

Two comments carry decisions that would otherwise read as drift:

- beside `train_mask_bin` — Phase 14 REVERSES Phase 12's unmasked verdict by design. Phase 12
  trained a model *of a dialogue*; personalization/QA teaching must cover ANSWER tokens only or
  the model learns to imitate questions (PITFALLS-14).
- beside `penalty_fn=None` — this is **structurally forced**, not preferable, for two independent
  reasons: (a) with the base frozen the EWC quadratic anchor is a constant, contributing zero
  gradient to A/B while crediting EWC with retention frozen-base LoRA produces by construction
  (PITFALLS P7); (b) `inject_lora` renames base params with a `.base.` infix while the Fisher
  keys are vanilla-GPT names, and `EWCPenalty.__call__` raises `ValueError` on any missing key —
  a hard crash, not a silent no-op.

### Task 2 — `CALIBRATION_DECISION_RULE` (`d7d7917`)

Seven pre-registered literals plus four pure functions, under a banner stating that the block is
committed BEFORE the calibration run produces a number and that git history order is the proof
(D-09 condition 2). `git log -S CALIBRATION_DECISION_RULE -- scripts/teach_persona.py` will show
this commit predating every calibration output, which is what plan 14-09's review step checks.

`lock_family_allocation` MOVES families and never drops one (B-02), with the four invariants
enforced through a `_refuse_move` contract function: F4 stays taught (D-22), two families minimum
per side, and every locked fact's taught-instance count stays inside DEMO-05's `[20, 50]` band
(W-03).

### Task 3 — CI pins (`0e32744`)

31 tests in `tests/test_phase14_teaching.py` (10 from plan 14-04, 21 added here), zero skips,
CPU-only. Every literal, every boundary, the four allocation invariants in both directions
(a band-breaking move refused, a legal move taken), the recipe constants, arm-path disjointness,
the persona-adapter cross-plan contract, and the verdict gate across GO/ADAPT/PENDING/STOP/missing.

## Key Findings

### The W-03 invariant is live, not hypothetical — no family can move today

At the committed allocation every locked fact has exactly **22** taught paraphrases against a
`[20, 50]` band, and the smallest taught family carries **4**. So *every* candidate move currently
drops a fact to 17 or 18 and is refused:

```
REFUSED moving F1 — fact 'cand_person_quillon' would drop to 17 taught paraphrases, outside [20, 50]
REFUSED moving F2 — ... 17 ...
REFUSED moving F4 — D-22 keeps F4 on the taught side
REFUSED moving F5 — ... 18 ...
REFUSED moving F6 — ... 18 ...
```

The upstream note that "at most one family (F6, 4 instances) can move before tripping proof 5" is
off by one step of arithmetic: 22 − 4 = 18, which is already below the floor. **Plan 14-09 should
expect a saturation result to produce an UNCHANGED allocation and a printed refusal, not a
reallocation.** If calibration genuinely demands more held-out families, the remedy is to add
paraphrase instances to the taught families first (raising the per-fact count above 24 so a
4-instance family can leave) — that is a fact-set change, not a threshold to relax.

### The plan's own verify assertion was unsatisfiable as literally specified

`replay_required(2.0, 2.2) is False` cannot hold under the naive formula: a 10% PPL increase in
decimal reconstructs in binary as `0.10000000000000009`, strictly greater than
`COLLAPSE_PPL_TRIGGER`, so the boundary case TRIPS a rule whose stated semantics are "the boundary
does not trigger". Fixed by rounding the measured ratio to `RATIO_DECIMALS = 10` before comparing
— six orders of magnitude coarser than double noise and six finer than any effect these gates can
resolve, so it decides only exactly-on-the-line cases. `test_decision_rule_replay_boundary`
asserts both the premise and the trap, so deleting the rounding turns the test red.

### Wiring smoke on real weights (throwaway, not committed)

A 3-step run of `train_arm("cal_first_person", ...)` on MPS with the real `convbase_best.pt`:

- 36 wrappers injected, **331,776** trainable parameters — exactly `r * n_layer * 18 * n_embd`
- **canary passed**: every trainable moved, every frozen base parameter bit-untouched — the MPS
  silent-freeze class (PITFALLS P5) is not present on this path
- adapter written at **1.35 MB** with `base_fingerprint` read from the base
  (`git_sha=04e724c…`, `step=4000`, `val_loss=1.5235939979553224`) — the trio plan 14-11 expects
- masked dialogue-val PPL, adapter OFF **4.5737** / ON **4.5796** (+0.13% over 270,203 scored
  targets). The OFF value matching Phase 12's recorded 4.5733 is independent confirmation the
  frozen base is intact.
- teaching corpus measured at 9,065 tokens (F5 estimated ~8,200), mask fraction 0.3426

All smoke artifacts were **deleted** — they are throwaway and nothing was copied back to the main
repo. Plan 14-11 must produce the real `persona_adapter.pt`; a smoke adapter must never be the one
that gets scored.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The real arm's adapter path did not match what the harness loads**

- **Found during:** Task 1
- **Issue:** `arm_outputs("real")["adapter"]` returned `checkpoints/phase14_real_adapter.pt`, but
  `scripts/phase14_recall.py` (14-06) and plan 14-08's demo both hardcode
  `checkpoints/persona_adapter.pt`. Plan 14-11 states `teach_persona.py real` must produce that
  file. Left alone, the harness would exit with "missing adapter" after a successful teaching run,
  pointing at the wrong cause.
- **Fix:** `arm_outputs` returns `persona_adapter.pt` for the `real` arm only, with the exception
  documented in its docstring; calibration arms keep their scoped names (disposable evidence).
  Pairwise disjointness is preserved and `test_real_arm_adapter_is_the_shippable_path` pins the
  contract naming both consumers.
- **Files modified:** `scripts/teach_persona.py`, `tests/test_phase14_teaching.py`
- **Commit:** `e61a184`, `0e32744`

**2. [Rule 1 - Bug] `replay_required`'s pre-registered boundary was float-unsatisfiable**

- **Found during:** Task 2
- **Issue:** see Key Findings above — the plan's own verify block asserted a result the naive
  formula cannot produce.
- **Fix:** `RATIO_DECIMALS = 10`, applied in both `replay_required` and `first_person_wins`, with
  the reasoning in the constant's comment and both halves pinned by tests.
- **Files modified:** `scripts/teach_persona.py`, `tests/test_phase14_teaching.py`
- **Commit:** `d7d7917`, `0e32744`

**3. [Rule 3 - Blocking] `main()` would have built every arm's bins twice**

- **Found during:** Task 1
- **Issue:** the plan gives `train_arm` its own bins step (step 4) while `main()` already built
  bins itself. Running both would trip `refuse_if_exists` on the second build.
- **Fix:** the bins body moved into `build_arm_bins` (one seam, in the bins half where it
  belongs); `train_arm` calls it and `main()` delegates entirely to `train_arm`. One code path,
  no duplication, and `teach_persona.py real` is a single command that teaches and exports as
  plan 14-11 assumes.
- **Files modified:** `scripts/teach_persona.py`
- **Commit:** `e61a184`

### Ordering deviation

The plan sequences `seed_everything` (step 3) before the bins build (step 4) while also requiring
it "immediately before the GPT build" (step 5) — mutually exclusive as written. Resolved by
seeding twice: once before the bins (preserving 14-04's determinism, since `sanity_check`'s smoke
draw consumes numpy RNG) and again immediately before the GPT build, which is the seed that
actually owns training data order. Commented in place.

### Added beyond the plan

Existence guards with actionable messages for `convbase_best.pt` and the `dialog_val` bin pair
(Rule 2). Without them, a missing val bin surfaces as a `ValueError` from `train()`'s
`val_mask_bin` guard rather than as "run `prepare_dialog_corpus.py`". Also a `SystemExit` if the
adapter-ON and adapter-OFF sweeps score different target counts — the pair is only a valid
comparison if it covers the identical target set.

## Verification

- `.venv/bin/pytest -q tests/test_phase14_teaching.py -x` — **31 passed**
- `.venv/bin/pytest -q` (full suite) — **359 passed, 4 skipped** (skips are pre-existing, all
  outside this module; `grep -c "skipif\|importorskip"` on this test file returns 0)
- `.venv/bin/ruff check . && .venv/bin/ruff format --check .` — clean
- `.venv/bin/python scripts/teach_persona.py bogus_arm` — exit 1, message lists all four `ARMS`
- `grep -c "assert " scripts/teach_persona.py` — **0** (every proof is a `raise SystemExit`,
  never `-O`-strippable)
- `git_sha()` does not appear inside the `export_adapter` call — the fingerprint is read from the
  base checkpoint blob
- Both plan-supplied verify blocks (Task 1 source inspection, Task 2 decision-rule assertions)
  pass verbatim

## Threat Model Coverage

| Threat ID | Mitigation as shipped |
|-----------|----------------------|
| T-14-04 | `torch.load(CONVBASE_BEST, weights_only=False)` is a trusted-own-file read, stated in the module `SECURITY:` paragraph; the exported adapter goes out through `export_adapter`, so consumers read it under `weights_only=True` |
| T-14-25 | `snapshot_params` before training plus a three-branch canary: non-finite loss, a trainable that did not move (P5), a frozen param that did (LORA-02). Verified passing on real 13.9M weights |
| T-14-23 | `base_fingerprint` built from `blob["git_sha"] / blob["step"] / blob["val_loss"]`; `git_sha()` appears only in the provenance echo, never in the export |
| T-14-20 | `CALIBRATION_DECISION_RULE` committed in `d7d7917`, before any calibration run; every literal and boundary pinned by CI |
| T-14-16 | `arm_outputs` scoping, now CI-tested pairwise across all four arms, plus `refuse_if_exists` on all five targets before any write |
| T-14-26 | `penalty_fn=None` with both structural reasons documented in place; the Fisher-bearing checkpoint's extras are never passed to the injected model |
| T-14-SC | Zero new packages |

## Known Stubs

None.

## Notes for the Next Plan

- **14-09:** `train_arm` returns `ppl_adapter_on` / `ppl_adapter_off` ready to feed
  `replay_required`, and `stats["mask_fraction"]` for the calibration report. Import `normalize` /
  `contains_value` / `score_question` from `phase14_recall` **lazily inside** the scoring function
  — `teach_persona` and `phase14_recall` reference each other and a module-level edge is an
  `ImportError`. Expect an unchanged allocation from `lock_family_allocation` (see Key Findings).
- **14-11:** `.venv/bin/python scripts/teach_persona.py real` is the single command; it gates on
  both verdicts, teaches, and exports `checkpoints/persona_adapter.pt`. It refuses to run if any
  of the five real-arm outputs already exist. `MAX_STEPS = 200` is the committed default and is
  the value calibration is expected to revise.

## Self-Check: PASSED

- `scripts/teach_persona.py` — FOUND (contains `def train_arm`, `CALIBRATION_DECISION_RULE`)
- `tests/test_phase14_teaching.py` — FOUND (contains `test_decision_rule_constants`)
- `.planning/phases/14-teach-then-recall-demo/14-07-SUMMARY.md` — FOUND
- commit `e61a184` — FOUND
- commit `d7d7917` — FOUND
- commit `0e32744` — FOUND
