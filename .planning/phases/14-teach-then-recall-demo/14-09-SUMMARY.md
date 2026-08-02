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
  - results/phase14_calibration_report.md
  - results/phase14_calibration_results.json
  - results/phase14_calibration_run.log
affects:
  - "plan 14-11 (the real run now gates on this report's verdict AND trains with replay at ratio 1.0)"
  - "plan 14-10 (TAUGHT_THRESHOLD / HELDOUT_THRESHOLD are no longer None — the recall report can state a verdict)"
  - "scripts/phase14_recall.py (the MPS generator fix unblocks every seeded draw on the M3)"
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
    - tests/test_phase14_scoring.py
key-decisions:
  - "per-family recall gain is defined as taught rate adapter-ON minus taught rate adapter-OFF — the recall teaching that family actually bought, which is what D-14's saturation clause asks"
  - "the adapter-OFF pass covers held-out as well as taught, beyond what the rule strictly needs, because the human checkpoint cannot judge a held-out rate without a closed-book baseline"
  - "CALIBRATION_SHA points at the commit carrying the measured report, not at a verdict commit that cannot exist until the human records one"
  - "arm_spec('real') now READS REAL_RUN_REPLAY_RATIO / REAL_RUN_SECOND_PERSON, so the derived numbers change what the real run trains on instead of documenting it"
  - "PPL delta displayed at 2 decimals of a percent — the stored PPL pair has 4 decimal places and cannot support a 4-decimal percentage"
patterns-established:
  - "Expensive measurement and cheap framing are separated by a JSON dump: `--rewrite-report` regenerates the artifact from committed evidence with no GPU"
  - "A boundary test asserts the exactness premise, both hairs, AND that two thresholds are independent bars"
requirements-completed: []
duration: 71min
completed: 2026-08-02
---

# Phase 14 Plan 09: Calibration Run + Four Derived Numbers Summary

**Three calibration arms measured on MPS, all four derivations applied mechanically by a rule
committed 40 minutes before the first number existed — and two of the four came back as results
nobody was hoping for: teaching without replay raises held-out dialogue PPL by 225%, and the
second-person register beat first person on held-out recall by 0.25.**

## Status: STOPPED AT CHECKPOINT (Task 3 of 3)

Tasks 1 and 2 are complete and committed. **Task 3 is a blocking human checkpoint** — the
`## Verdict` section of `results/phase14_calibration_report.md` reads
`PENDING — user decision at checkpoint.` and only a human may replace it with `GO`, `ADAPT`, or
`STOP`. Everything that could be run has been run; only the judgment is outstanding.

`scripts/teach_persona.py real` refuses to start until that verdict reads GO or ADAPT
(`_require_go_verdict(CALIBRATION_REPORT)`, W-02), so plan 14-11 is correctly blocked.

## Performance

- **Duration:** ~71 min wall (calibration run itself: 3,210 s / 53.5 min on MPS)
- **Tasks:** 2/3 complete, 1 blocked on human verdict
- **Completions generated:** 10,764 (598 questions × 9 draws × 2 adapter states)
- **Test suite:** 377 passed, 6 skipped; `ruff check .` + `ruff format --check .` clean

## Task Commits

1. **Harness fixes that unblocked the run** — `026b74b` (fix)
2. **Task 1: the three calibration arms + the report** — `0425fdc` (feat)
3. **Task 2: the four derived numbers into the drivers** — `ec6a5b0` (feat)

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
| 1 | `lock_thresholds(0.6825, 0.5519)` | `TAUGHT_THRESHOLD = 0.4095`, `HELDOUT_THRESHOLD = 0.3311` — the discount bound both, neither hit the 0.20 floor |
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
Note also that the replay arm's held-out rate (0.2506) sits **below** the `HELDOUT_THRESHOLD`
(0.3311) this same run derived from the no-replay arm. Applying both derivations as written
produces a real run that is configured to fail its own gate. That interaction is a judgment call
for the checkpoint, not something a driver should resolve.

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

## Deviations from Plan

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
reader actually needs (the same role `FACTSET_GATE_SHA` plays). The comment says so in place.

## Verification

- `.venv/bin/pytest -q` — **377 passed, 6 skipped** (was 375/6 before this plan's added test)
- `.venv/bin/ruff check . && .venv/bin/ruff format --check .` — clean
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

## Notes for the Next Plan

- **The human must record a verdict before anything else in this phase proceeds.**
  `teach_persona.py real` hard-exits on a PENDING verdict (W-02).
- **14-11 will now train with replay at ratio 1.0** — `arm_spec("real")` reads
  `REAL_RUN_REPLAY_RATIO`. Its teaching bin will be ~2× the tokens and it needs
  `data/dialog_train.bin` + its mask present, not just the val pair.
- **The threshold/replay interaction in Finding 2 is unresolved by design.** The replay arm's
  held-out rate (0.2506) is below the held-out threshold (0.3311) this run derived from the
  no-replay arm. Both numbers are correct outputs of correctly pre-registered rules; whether the
  real run should proceed anyway, use a lower replay ratio, or shorten `MAX_STEPS` is precisely
  the ADAPT decision the checkpoint exists for.
- **`MAX_STEPS = 200` is the other lever.** All three arms reached final train losses of
  0.07/0.56/0.07, and the collapse scales with how hard the adapter overfits. Calibration measured
  the tradeoff at 200 steps only; a shorter run was not measured.

## Self-Check: PASSED

- `results/phase14_calibration_report.md` — FOUND (8 headings in order, verdict PENDING)
- `results/phase14_calibration_results.json` — FOUND (3 arms)
- `results/phase14_calibration_run.log` — FOUND
- `results/phase14_cal_first_person/run.csv` — FOUND
- `results/phase14_cal_first_person_replay/run.csv` — FOUND
- `results/phase14_cal_second_person/run.csv` — FOUND
- `scripts/teach_persona.py` — FOUND (contains `def run_calibration`, `def derive_all`)
- `scripts/phase14_recall.py` — FOUND (contains `TAUGHT_THRESHOLD = 0.4095`, `def taught_gate`)
- `scripts/phase14_factset.py` — FOUND (allocation comment records the derivation)
- `tests/test_phase14_scoring.py` — FOUND (contains `def test_gate_boundary`)
- commit `026b74b` — FOUND
- commit `0425fdc` — FOUND
- commit `ec6a5b0` — FOUND

---
*Phase: 14-teach-then-recall-demo*
*Stopped at: Task 3 (blocking human checkpoint)*
