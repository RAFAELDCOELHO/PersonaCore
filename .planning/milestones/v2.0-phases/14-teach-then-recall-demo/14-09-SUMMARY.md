---
phase: 14
plan: 09
subsystem: calibration run + the four derived numbers
tags: [D-09, D-14, D-15, D-21, D-22, D-12, W-02, W-03, B-02, DEMO-05, DEMO-06, PITFALLS-14]
requires:
  - scripts/teach_persona.train_arm
  - scripts/teach_persona.CALIBRATION_DECISION_RULE
  - scripts/teach_persona.lock_thresholds
  - scripts/teach_persona.lock_family_allocation
  - scripts/teach_persona.replay_required
  - scripts/teach_persona.first_person_wins
  - scripts/phase14_recall.load_adapted_model
  - scripts/phase14_recall.complete_question
  - scripts/phase14_recall.score_question
  - scripts/phase14_recall.contains_value
  - scripts/phase14_factset.CALIBRATION_FACTS
  - scripts/phase14_factset.REGISTER_ARM_FACTS
  - checkpoints/convbase_best.pt
  - checkpoints/convbase_slim.pt
  - data/dialog_train.bin
  - data/dialog_val.bin
provides:
  - scripts/teach_persona.run_calibration
  - scripts/teach_persona.derive_all
  - scripts/teach_persona.score_arm
  - scripts/teach_persona.score_items
  - scripts/teach_persona.calibration_items
  - scripts/teach_persona.write_calibration_report
  - scripts/teach_persona.dump_results
  - scripts/teach_persona.rewrite_report
  - scripts/teach_persona.rule_commit_sha
  - scripts/teach_persona.REAL_RUN_REPLAY_RATIO
  - scripts/teach_persona.REAL_RUN_SECOND_PERSON
  - scripts/teach_persona.CALIBRATION_RESULTS
  - scripts/phase14_recall.TAUGHT_THRESHOLD
  - scripts/phase14_recall.HELDOUT_THRESHOLD
  - scripts/phase14_recall.CALIBRATION_SHA
  - scripts/phase14_recall.taught_gate
  - scripts/phase14_recall.heldout_gate
  - scripts/personalize_demo.DECODE_KW
  - results/phase14_calibration_report.md
  - results/phase14_calibration_results.json
  - results/phase14_calibration_run.log
affects:
  - "plan 14-11 (the real run is UNBLOCKED — the verdict reads ADAPT — and trains with replay at ratio 1.0)"
  - "plan 14-10 (TAUGHT_THRESHOLD = 0.2486 / HELDOUT_THRESHOLD = 0.2000 are committed literals — the recall report can state a verdict)"
  - "scripts/phase14_recall.py (the MPS generator fix unblocks every seeded draw on the M3)"
  - "scripts/personalize_demo.py (plan 14-08's demo now decodes under the harness's scored condition, not package defaults)"
tech-stack:
  added: []
  patterns:
    - "the four derivations as ONE pure function of the arm records (derive_all), so the report's numbers are re-derivable without a GPU"
    - "measurements dumped to JSON beside the report, so a wording fix never justifies re-measuring or hand-editing generated evidence"
    - "adapter-OFF scored on BOTH tiers, not only the tier the rule consumes — a held-out rate without a closed-book baseline is unjudgeable"
    - "identical closed-book numbers across arms used as a free cross-arm check that adapter_disabled restores the base"
    - "report display precision capped at what the stored measurement supports, so re-render is byte-stable"
key-files:
  created:
    - results/phase14_calibration_report.md
    - results/phase14_calibration_results.json
    - results/phase14_calibration_run.log
    - results/phase14_cal_first_person/run.csv
    - results/phase14_cal_first_person_replay/run.csv
    - results/phase14_cal_second_person/run.csv
  modified:
    - scripts/teach_persona.py
    - scripts/phase14_recall.py
    - scripts/phase14_factset.py
    - scripts/personalize_demo.py
    - tests/test_phase14_scoring.py
    - tests/test_phase14_demo.py
key-decisions:
  - "ADAPT verdict: lock_thresholds re-applied to cal_first_person_replay (the arm replay_required=True selects) — TAUGHT 0.4095->0.2486, HELDOUT 0.3311->0.2000, both sets shown side by side in the report"
  - "the demo mirrors the harness's SAMPLED draw (0.8 / 0.95), not its greedy draw — 8 of every 9 scored draws come from it, and greedy is the measured looping failure mode"
  - "DECODE_KW holds no float of its own: it IMPORTS SAMPLE_TEMPERATURE / SAMPLE_TOP_P so the demo and the harness cannot drift apart"
  - "derive_all's threshold wiring is left as-is with the mismatch documented in its docstring — editing a derivation pipeline after seeing its numbers is what the pre-registration block exists to prevent"
  - "per-family recall gain is defined as taught rate adapter-ON minus taught rate adapter-OFF — the recall teaching that family actually bought, which is what D-14's saturation clause asks"
  - "the adapter-OFF pass covers held-out as well as taught, beyond what the rule strictly needs, because the human checkpoint cannot judge a held-out rate without a closed-book baseline"
  - "CALIBRATION_SHA points at the commit carrying the measured report, not at a verdict commit that cannot exist until the human records one"
  - "arm_spec('real') now READS REAL_RUN_REPLAY_RATIO / REAL_RUN_SECOND_PERSON, so the derived numbers change what the real run trains on instead of documenting it"
  - "PPL delta displayed at 2 decimals of a percent — the stored PPL pair has 4 decimal places and cannot support a 4-decimal percentage"
patterns-established:
  - "Expensive measurement and cheap framing are separated by a JSON dump: `--rewrite-report` regenerates the artifact from committed evidence with no GPU"
  - "A boundary test asserts the exactness premise, both hairs, AND that two thresholds are independent bars"
  - "A post-hoc correction shows BOTH numbers side by side and labels its own projections as projections — replacing the old number silently is what makes a correction indistinguishable from a threshold chosen to be cleared"
  - "Two files that must decode identically are pinned to each other by a test, not by a convention — the demo imports the harness's constants and a test pins the exact key set"
requirements-completed: [DEMO-05, DEMO-06]
duration: 78min
completed: 2026-08-02
---

# Phase 14 Plan 09: Calibration Run + Four Derived Numbers Summary

**Three calibration arms measured on MPS, all four derivations applied mechanically by a rule
committed 40 minutes before the first number existed — and two of the four came back as results
nobody was hoping for: teaching without replay raises held-out dialogue PPL by 225%, and the
second-person register beat first person on held-out recall by 0.25.**

## Status: COMPLETE (3 of 3 tasks)

The human recorded **`ADAPT`** on `results/phase14_calibration_report.md`. `grep -c PENDING` on
the report is **0**, `_require_go_verdict(CALIBRATION_REPORT)` returns `'ADAPT'`, and
`scripts/teach_persona.py real` no longer hard-exits — **plan 14-11 is unblocked.**

## Performance

- **Duration:** ~78 min wall (calibration run itself: 3,210 s / 53.5 min on MPS)
- **Tasks:** 3/3 complete
- **Completions generated:** 10,764 (598 questions × 9 draws × 2 adapter states)
- **Test suite:** 378 passed, 6 skipped; `ruff check .` + `ruff format --check .` clean

## Task Commits

1. **Harness fixes that unblocked the run** — `026b74b` (fix)
2. **Task 1: the three calibration arms + the report** — `0425fdc` (feat)
3. **Task 2: the four derived numbers into the drivers** — `ec6a5b0` (feat)
4. **Task 3: the ADAPT verdict, the corrected thresholds, the demo decode match** — see the final
   commit on this branch (feat)

## Measured Results

| Arm | taught ON | held-out ON | closed book (OFF) | train loss | masked dialogue-val PPL OFF → ON |
|---|---|---|---|---|---|
| `cal_first_person` | **0.6825** (860/1260) | **0.5519** (447/810) | 0.0000 / 0.0000 | 0.0754 | 4.5737 → 14.8559 (**+224.81%**) |
| `cal_first_person_replay` | 0.4143 (522/1260) | 0.2506 (203/810) | 0.0000 / 0.0000 | 0.5555 | 4.5737 → 5.9180 (+29.39%) |
| `cal_second_person` | 0.9405 (711/756) | **0.8045** (391/486) | 0.0000 / 0.0000 | 0.0668 | 4.5737 → 18.7520 (+310.00%) |

The adapter-OFF baseline is **exactly zero on all six tiers**. The frozen base never once
produced a calibration value across 3,276 closed-book completions, which is the strongest
possible statement that these recall rates come from the adapter.

The adapter-OFF masked dialogue-val PPL is **4.5737 on all three arms**, matching the frozen-base
anchor (Phase 12 recorded 4.5733) — independent confirmation the base was never disturbed.

## The Four Derivations

| # | Rule function | Result |
|---|---|---|
| 1 | `lock_thresholds(0.6825, 0.5519)` → **corrected at the checkpoint** to `lock_thresholds(0.4143, 0.2506)` | **`TAUGHT_THRESHOLD = 0.2486`** (the discount binds), **`HELDOUT_THRESHOLD = 0.2000`** (the FLOOR binds — 0.6 × 0.2506 = 0.1504 discounts below it). See "The Recorded Verdict" below |
| 2 | `lock_family_allocation(...)` | **UNCHANGED**: taught `{F1,F2,F4,F5,F6}`, held-out `{F3,F7,F8}` — neither trigger fired, two proposed moves refused |
| 3 | `replay_required(4.5737, 14.8559)` | **True** → `REAL_RUN_REPLAY_RATIO = 1.0` |
| 4 | `first_person_wins(0.5519, 0.8045)` | **False** (margin −0.2526) → recorded unamended, `REAL_RUN_SECOND_PERSON` stays `False` |

`git log -S 'CALIBRATION_DECISION_RULE = (' -- scripts/teach_persona.py` returns exactly one
commit, `d7d7917` (2026-08-02 01:52), which strictly precedes every output of this run
(first arm bins written 05:39 UTC). That ordering is D-09 condition 2's proof.

## Key Findings

### 1. Teaching without replay collapses the conversational base — the trigger fired hard

`+224.81%` masked dialogue-val PPL against a `COLLAPSE_PPL_TRIGGER` of `0.10`. This is not a
marginal call; the no-replay arm is 22× past the line. 200 steps at batch 8 × 256 over a
9,065-token corpus is ~50 epochs, the deliberate overfit ARCHITECTURE Anti-pattern 6 prescribes,
and it evidently overwrites conversational competence along with installing the facts.

### 2. Replay mitigates but does not solve, and it is expensive

The paired arm is the whole point of D-15, and it says both halves out loud:

| | no replay | replay 1.0 |
|---|---|---|
| PPL delta | +224.81% | +29.39% |
| taught recall | 0.6825 | 0.4143 |
| held-out recall | 0.5519 | 0.2506 |

Replay at ratio 1.0 removes ~87% of the collapse and **still trips the trigger**, while costing
0.27 of taught recall and 0.30 of held-out recall. "Replay required" is not "replay solves it" —
the report says so explicitly, and this is the single most important thing for the human to weigh.
Note also that the replay arm's held-out rate (0.2506) sat **below** the `HELDOUT_THRESHOLD`
(0.3311) this same run derived from the no-replay arm. Applying both derivations as written
produced a real run configured to fail its own gate. **This is exactly the interaction the
checkpoint resolved** — see "The Recorded Verdict" below.

### 3. The register arm came back negative, and it is recorded unamended

Second person measured **0.8045** held-out against first person's **0.5519** — a margin of
−0.2526 where D-21 needed +0.10 for a first-person win. Per D-12 this is reported as measured and
**does not reopen D-01 mid-phase**: D-01's register lock rests on the qualitative 14-RESEARCH
F3/F5 evidence (the base answering `i have a dog named my name is cuddling` — structure copied,
content not), and this arm was designed to supplement that with the head-to-head D-01 was missing,
not to replace it. Re-authoring the register after seeing a number is exactly the move the
pre-registration block exists to prevent.

Two caveats the report carries and the human should weigh:
- The arms score **different fact sets** (10 calibration facts vs 6 register-arm facts), because
  D-21 requires the register arm's facts to be disjoint from both other sets. This is the
  strongest head-to-head that disjointness allows, not a clean A/B.
- The second-person arm also collapsed the base **worst** of the three (+310.00%). If register is
  ever revisited, that is part of its price.

### 4. `F4` and `F5` have no measured gain — absence of measurement, not measurement of zero

Every question those two families generate names its own fact value (`F4` is the D-22 reversed
direction, `F5` is yes/no verification), so the scored harness's mechanical `contains_value`
filter drops all of them. `lock_family_allocation` reads a missing key as `0.0`, judged both
saturated, and **proposed moving both to held-out**; both moves were refused — `F4` by D-22,
`F5` by the W-03 paraphrase band (it would drop every locked fact to 18 taught paraphrases,
outside `[20, 50]`).

The refusals are exactly the saturation result 14-07 predicted, arriving by a route 14-07 did not
predict: not because the measured families saturated (they gained +0.65 to +0.70) but because two
families are structurally unmeasurable by this harness. The report states this in the one place a
refusal can land, because an unrecorded refusal is a silently altered allocation — and because a
reader who skims `gain: 0.0` would wrongly conclude reversed-direction teaching failed. **This run
says nothing either way about `F4`/`F5`.**

### 5. The closed-book pass paid for itself twice

Beyond supplying the baseline, the OFF pass produced identical `0/1260` and `0/810` results across
all three arms — a free cross-arm confirmation that `adapter_disabled` restores the pre-injection
base exactly, on three independently trained adapters.

## The Recorded Verdict (Task 3)

**`ADAPT` — the real run proceeds, with exactly one deviation.**

### The deviation: `lock_thresholds` was fed the wrong arm

Derivation 3 returned `replay_required = True`, which sets `REAL_RUN_REPLAY_RATIO = 1.0` and makes
`cal_first_person_replay` the arm the real run actually runs under. Derivation 1 had been applied
to `cal_first_person` — the no-replay baseline. The **identical committed rule function** was
re-applied to the matching arm's rates:

```
max(THRESHOLD_FLOOR, round(rate * THRESHOLD_DISCOUNT, 4))

taught     max(0.2, round(0.4143 * 0.6, 4)) = max(0.2, 0.2486) = 0.2486
held-out   max(0.2, round(0.2506 * 0.6, 4)) = max(0.2, 0.1504) = 0.2000   <- the FLOOR binds
```

| Threshold | as first derived | **committed** | bound by |
|---|---|---|---|
| `TAUGHT_THRESHOLD` | 0.4095 | **0.2486** | the DISCOUNT |
| `HELDOUT_THRESHOLD` | 0.3311 | **0.2000** | the FLOOR |

Both sets appear side by side in the report so a reader can check independently that the
correction **narrows a wiring mismatch** rather than relaxing the gate below what the mechanism
needed to clear. The held-out threshold does not fall to 0.1504 — the pre-registered
`THRESHOLD_FLOOR` catches it, which is the floor doing the job it was committed for.

The deviation note is recorded **verbatim** in the report's Derivation 1:

> lock_thresholds was fed cal_first_person (no-replay) while replay_required=True selected the replay config. Feeding it the matching arm is a wiring correction, not a threshold chosen to be cleared. Recorded post-hoc; both numbers shown.

### The projections, labelled as projections

| Tier | replay-arm rate | corrected threshold | PROJECTED margin |
|---|---|---|---|
| taught | 0.4143 | 0.2486 | **+0.1657** |
| held-out | 0.2506 | 0.2000 | **+0.0506** |

**These are NOT a result.** They are the calibration arm's own rates against a gate that same arm
produced — an arm cannot be independent evidence for a threshold derived from it — measured on a
throwaway fact set the shipped adapter is never taught. **Plan 14-11's real teaching run produces
the number that actually counts.** If the real run lands below either threshold, that is the
result and it gets recorded as one.

### What is NOT adapted

Derivation 2's allocation stands unchanged, refusals and all, with its F4/F5
absence-of-measurement note. Derivation 3's `replay_required = True` and
`REAL_RUN_REPLAY_RATIO = 1.0` stand. Derivation 4's negative register result stands **unamended**
(D-12) and does not reopen D-01 mid-phase — `REAL_RUN_SECOND_PERSON` stays `False`. **No measured
number in the report was altered.**

## Deviations from Plan

### Checkpoint-driven scope deviation

**`scripts/personalize_demo.py` is plan 14-08's file, outside 14-09's declared `files_modified`.**
The change is authorized by the user at this checkpoint and is recorded here as an explicit scope
deviation.

**What changed.** The demo ran the package defaults (`temperature=1.0`, no `top_p`, no `top_k`)
while every committed recall number was measured under
`phase14_recall.complete_question`'s sampled draw. The page and the report described two different
systems. The demo now imports `SAMPLE_TEMPERATURE` / `SAMPLE_TOP_P` from the harness into a
module-level `DECODE_KW` and threads it into `generate_text_from_ids_cumulative`.

**The match, parameter by parameter** against `personacore.generation.core.generate`:

| parameter | harness (sampled draw) | demo (now) | match |
|---|---|---|---|
| `temperature` | `SAMPLE_TEMPERATURE` = 0.8 | imported, same object | exact |
| `top_p` | `SAMPLE_TOP_P` = 0.95 | imported, same object | exact |
| `top_k` | never passed → `None` | never passed → `None` | exact |
| `greedy` | not passed on this path → `False` | not passed → `False` | exact |
| `max_new_tokens` | `RECALL_MAX_NEW_TOKENS` = 48 | slider floors AND defaults at 48 | floor is the measured condition |
| `forbid_ids` | `undecodable_ids_mask(tok, vocab)` | same call — pinned by `test_forbid_ids_parity` | exact |
| `stop_ids` | `set(STOP_IDS)` | `set(STOP_IDS)`, imported | exact |
| `eos_id` / `block_size` | `model.config` defaults | `model.config` defaults | exact |
| `generator` | `question_seed(index) + s` | `None` (global RNG) | **deliberately not mirrored** |

**Which path was mirrored, and why.** The harness scores **1 greedy + 8 seeded draws** per
question, so 8 of every 9 scored draws come from the sampled path. Greedy is the odd one out and
is a poor fit for the demo on its own terms: 14-RESEARCH Pitfall 6 measured greedy decoding
**looping** on this base (`i live in the country i live in the country.`) — the documented failure
mode `RECALL_MAX_NEW_TOKENS` was sized around. Putting it on camera would show a decode artifact
rather than where the memory lives.

**Why seeding is not mirrored.** `question_seed(index) + s` exists so a scored run is re-derivable
from `SEED` alone; `index` is a question's position in its tier, and a demo taking free-text input
has no tier and no index. Repeat asks therefore vary — the honest rendering of a metric that is a
success **rate** over draws and never one transcript.

**The coupling is pinned, not conventional.** `DECODE_KW` holds no float literal of its own (it
imports both), and `tests/test_phase14_demo.py::test_decode_settings_match_the_scoring_harness`
asserts three separable things: the bare literals `0.8` / `0.95` (so a change to the HARNESS also
goes red — `pd.X == pr.X` alone would be a tautology), the **exact key set** (an added `top_k` is
as much a divergence as a changed value), and that `**DECODE_KW` actually reaches the generation
call. Same discipline as the `forbid_ids` parity and token-dump byte-identity tests already locked
for this phase.

### Auto-fixed Issues

**1. [Rule 1 - Bug] `complete_question` built a CPU generator for a device-resident sample**

- **Found during:** Task 1 setup (throughput benchmark, before any arm ran)
- **Issue:** `scripts/phase14_recall.py:503` created `torch.Generator(device="cpu")` while
  `next_token` calls `torch.multinomial(probs, generator=...)` with `probs` on the model device.
  On MPS that raises `RuntimeError: Expected a 'mps' device type for generator but found 'cpu'`
  on the **first seeded draw of the first question**. Every test in the suite is CPU-only, so it
  passed CI green and would have killed both this plan's calibration run and plan 14-11's real
  scored run at their first sampled token.
- **Fix:** `torch.Generator(device=device)`, with the failure mode named in a comment. MPS
  generators are supported and reproducible (verified: two generators seeded identically draw the
  same token).
- **Files modified:** `scripts/phase14_recall.py`
- **Commit:** `026b74b`

**2. [Rule 3 - Blocking] `load_adapted_model` could only load the shippable adapter**

- **Found during:** Task 1
- **Issue:** `ADAPTER_PATH` is a module constant, so the calibration arms — which write to
  `checkpoints/phase14_cal_*_adapter.pt` by design (14-07's arm scoping) — had no way to be scored
  through the harness the plan requires them to be scored through.
- **Fix:** an optional `adapter_path=None` parameter defaulting to `ADAPTER_PATH`. Every existing
  caller is unchanged. The alternative — a parallel loader in `teach_persona` — would derive the
  thresholds from a different pipeline than the one they gate.
- **Files modified:** `scripts/phase14_recall.py`
- **Commit:** `026b74b`

### Added beyond the plan

**`dump_results` + `--rewrite-report` (`results/phase14_calibration_results.json`).**
The measurements are a 53-minute unrepeatable MPS run; the prose framing them is not. Without a
re-render path, any wording fix in the report is either a re-measurement or a hand-edit of
generated evidence, and hand-editing an artifact whose entire purpose is auditability defeats the
artifact. The JSON is committed, `--rewrite-report` regenerates the report from it with no GPU,
and the re-render is **byte-stable** (verified by rendering twice and diffing).

This was used once, deliberately: the run-generated report was diffed against a re-render, the
diff was exactly the two prose blocks added in Finding 3 and Finding 4 above plus a 4th-decimal
percentage rounding artifact, and the display precision was then capped at 2 decimals of a percent
(what the stored 4-decimal PPL pair actually supports) so re-render became byte-stable. **No number
in the report was ever typed by hand.**

**`derive_all` extracted as a pure function.** The plan implies the derivations happen inline in
the run. Making them a pure function of the arm records means the four derivations can be re-run
and checked against the report without a GPU, and it let the report writer be smoke-tested on
fabricated records (both the saturated/collapsed/negative branch and the healthy branch) **before**
the 53-minute run started rather than after.

**The adapter-OFF pass covers held-out as well as taught.** The rule only consumes the taught OFF
rates (as the gain's second term). Held-out OFF costs ~15 minutes and is what makes a held-out rate
judgeable at all — the human checkpoint has to decide whether 0.5519 means something, and it means
something very different against a base scoring 0.0000 than against a base scoring 0.35. It also
produced Finding 5.

### Deviation of interpretation

**`CALIBRATION_SHA` points at the evidence commit, not a verdict commit.** The plan specifies
"the git sha of the commit carrying the recorded calibration verdict". That commit cannot exist
when Task 2 runs — the verdict is recorded by a human at Task 3, after Task 2 — and the plan's own
acceptance criterion requires `git cat-file -e $CALIBRATION_SHA` to exit 0. It is set to `0425fdc`,
the commit carrying the measured report and the results JSON, which is the traceability anchor a
reader actually needs (the same role `FACTSET_GATE_SHA` plays). Every rate feeding
`lock_thresholds` for **either** arm is already in the report at that SHA, so the corrected
thresholds are re-derivable from it too. The comment says so in place.

**`derive_all`'s threshold wiring is left as-is, with the mismatch documented in its docstring.**
The function still feeds `lock_thresholds` the baseline arm. Correcting the wiring would mean
editing a derivation pipeline **after seeing its numbers** — the exact move the pre-registration
block exists to prevent — and the committed report records what this function actually ran. The
docstring now names the mismatch, states that the committed thresholds come from the replay arm,
and requires anyone re-running with `--force` to re-decide which arm feeds the rule at the human
checkpoint. The clobber guard makes that path gated rather than silent.

## Verification

- `.venv/bin/python -m pytest -q` — **378 passed, 6 skipped** (was 377/6; +1 is the new decode pin)
- `.venv/bin/python -m ruff check .` — `All checks passed!`;
  `ruff format --check .` — `132 files already formatted`
- `grep -c PENDING results/phase14_calibration_report.md` → **0**
- `_require_go_verdict(CALIBRATION_REPORT)` → **`'ADAPT'`** (so `teach_persona.py real` no longer
  hard-exits; W-02 satisfied)
- `lock_thresholds(0.4143, 0.2506)` → `(0.2486, 0.2)`, **identical** to the committed
  `TAUGHT_THRESHOLD` / `HELDOUT_THRESHOLD` — the literals are the rule's output, not a transcription
- `_refuse_clobber(report, force=False)` still raises `SystemExit` naming the path; `force=True`
  still passes — the recorded ADAPT verdict is protected exactly as a GO would be
- Plan Task 1 verify block — passes verbatim (eight headings present **and in order**, all three
  arm names present, opener present)
- Plan Task 2 verify block — passes verbatim (`derived numbers committed`)
- `git cat-file -e 0425fdc4…` — exits 0
- Clobber guard: with `## Verdict` temporarily set to `GO`, both `--calibration` and
  `--rewrite-report` exit **1** naming the report path; `--force` is required
- Report re-render is **byte-identical** across two consecutive `--rewrite-report` runs
- Copied-back adapter SHA-256s match the digests recorded in the report, all three
- `git log -S 'CALIBRATION_DECISION_RULE = (' -- scripts/teach_persona.py` → one commit,
  `d7d7917`, predating every calibration output

## Threat Model Coverage

| Threat ID | Mitigation as shipped |
|-----------|----------------------|
| T-14-20 | Rule committed in `d7d7917`; the report's `## Pre-Registration` names that SHA and gives the `git log -S` command to re-derive it; the human checkpoint verifies the ordering before recording a verdict |
| T-14-16 | `arm_outputs` scoping + `refuse_if_exists` on all five targets per arm, before any write; three distinct adapters with three distinct SHA-256s recorded |
| T-14-06 | `_refuse_clobber` on the report path, on BOTH `--calibration` and `--rewrite-report`; verified to exit non-zero against a recorded verdict |
| T-14-31 | `CALIBRATION_SHA` in the driver, a per-derivation report section naming its rule function and every input, and `derive_all` as a pure function so any reader can re-derive from the committed JSON |
| T-14-05 | Calibration and register-arm facts are invented and disjoint from the real set; both pools passed the same D-02/D-03 gate; no real personal data reaches `results/` |
| T-14-SC | Zero new packages |

## Known Stubs

None.

## Threat Flags

None. No new network endpoint, no new deserialization path (the calibration adapters cross the
existing `weights_only=True` `load_adapter` choke point), no schema change, no new package.

## Artifacts Copied Back to the Main Repo

Gitignored, so they do not travel with the branch:

- `checkpoints/phase14_cal_first_person_adapter.pt`
- `checkpoints/phase14_cal_first_person_replay_adapter.pt`
- `checkpoints/phase14_cal_second_person_adapter.pt`

All three digests verified against the report after copying.

**Deliberately discarded** (regenerable intermediates, ~180 MB): the three
`checkpoints/phase14_cal_*_latest.pt` training checkpoints and the six `data/persona_cal_*` bins.
Nothing downstream reads them; `--rewrite-report` needs only the committed JSON.

## What 14-10 and 14-11 Must Consume

### Plan 14-11 (the real teaching run) — now UNBLOCKED

- **The gate is open.** `_require_go_verdict(CALIBRATION_REPORT)` returns `'ADAPT'`.
- **Train with replay at ratio 1.0.** `arm_spec("real")` reads `REAL_RUN_REPLAY_RATIO`. The
  teaching bin is ~2× the tokens and needs `data/dialog_train.bin` **plus its mask** present, not
  just the val pair.
- **`REAL_RUN_SECOND_PERSON` stays `False`.** The negative register result does not reopen D-01.
- **The allocation is unchanged**: taught `{F1, F2, F4, F5, F6}`, held-out `{F3, F7, F8}`.
- **`MAX_STEPS = 200` is the untested lever.** All three arms reached final train losses of
  0.07/0.56/0.07 and the collapse scales with how hard the adapter overfits. Calibration measured
  the tradeoff at 200 steps **only**; a shorter run was never measured. If the real run's PPL
  collapse is unacceptable, this is the knob — and it needs its own measurement, not a guess.
- **Expect the real run's own PPL delta to be reported.** The replay arm still tripped
  `COLLAPSE_PPL_TRIGGER` at +29.39%. Replay was required, not sufficient.

### Plan 14-10 (the recall report)

- **The thresholds are committed literals, no longer `None`:** `TAUGHT_THRESHOLD = 0.2486`,
  `HELDOUT_THRESHOLD = 0.2000`. Use `taught_gate(rate)` / `heldout_gate(rate)` — both are `>=`,
  so a rate landing exactly on a threshold **passes**.
- **`CALIBRATION_SHA = "0425fdc494025d9c59cfac1e62092b10820a619e"`** is the evidence anchor to
  cite; the ADAPT verdict and the arm correction live on that same report in a later commit.
- **Cite the corrected numbers, and say which arm produced them.** A reader comparing 14-10's
  report against the calibration report will see both threshold sets; the report explains why.
- **Do NOT cite the +0.1657 / +0.0506 margins as results.** They are the calibration arm's own
  rates against its own gate, labelled as projections in both the report and here. 14-11's real
  run produces the number that counts.
- **The demo now decodes at temperature 0.8 / top_p 0.95** — the same condition 14-10's numbers
  are measured under. If 14-10 changes `SAMPLE_TEMPERATURE` or `SAMPLE_TOP_P`, the demo follows
  automatically (it imports them) and
  `test_decode_settings_match_the_scoring_harness` goes red on the bare literals, forcing both
  files to be looked at together. That is intentional.

## Self-Check: PASSED

- `results/phase14_calibration_report.md` — FOUND (8 headings in order, verdict **ADAPT**,
  `grep -c PENDING` = 0, both threshold sets present, deviation note verbatim)
- `results/phase14_calibration_results.json` — FOUND (3 arms)
- `results/phase14_calibration_run.log` — FOUND
- `results/phase14_cal_first_person/run.csv` — FOUND
- `results/phase14_cal_first_person_replay/run.csv` — FOUND
- `results/phase14_cal_second_person/run.csv` — FOUND
- `scripts/teach_persona.py` — FOUND (contains `def run_calibration`, `def derive_all`)
- `scripts/phase14_recall.py` — FOUND (contains `TAUGHT_THRESHOLD = 0.2486`,
  `HELDOUT_THRESHOLD = 0.2000`, `def taught_gate`)
- `scripts/phase14_factset.py` — FOUND (allocation comment records the derivation)
- `scripts/personalize_demo.py` — FOUND (contains `DECODE_KW = {`, `**DECODE_KW`)
- `tests/test_phase14_scoring.py` — FOUND (contains `def test_gate_boundary`)
- `tests/test_phase14_demo.py` — FOUND (contains
  `def test_decode_settings_match_the_scoring_harness`)
- commit `026b74b` — FOUND
- commit `0425fdc` — FOUND
- commit `ec6a5b0` — FOUND

---
*Phase: 14-teach-then-recall-demo*
*Completed: 3/3 tasks — verdict ADAPT recorded*
