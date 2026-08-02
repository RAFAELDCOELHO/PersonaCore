---
phase: 14
plan: 11
subsystem: the real teaching run + the scored recall run + the evidence artifacts
tags: [DEMO-05, DEMO-06, DEMO-07, SC1, SC2, SC3, SC4, D-11, D-12, D-20, T-14-18, T-14-25, T-14-28]
status: awaiting-blocking-checkpoint
requires:
  - scripts/teach_persona.train_arm
  - scripts/phase14_recall.main
  - scripts/personalize_demo.build_demo
  - checkpoints/convbase_best.pt
  - checkpoints/convbase_slim.pt
  - data/dialog_train.bin
  - data/dialog_val.bin
  - results/phase14_factset_report.md
  - results/phase14_calibration_report.md
provides:
  - checkpoints/persona_adapter.pt
  - results/phase14_real/run.csv
  - results/phase14_teaching_run.log
  - results/phase14_recall_report.md
  - results/phase14_transcripts.md
  - results/phase14_recall_run.log
affects:
  - "Phase 15 (the figures + writeup consume these two evidence artifacts and the adapter)"
tech-stack:
  added: []
  patterns:
    - "an artifact-path contract enforced by the plan that consumes it, not by the plan that wrote it"
    - "the run's own guard re-checked independently after the fact — the guard passing and a second pass over the committed dumps are two different claims"
key-files:
  created:
    - results/phase14_recall_report.md
    - results/phase14_transcripts.md
    - results/phase14_recall_run.log
    - results/phase14_teaching_run.log
    - results/phase14_real/run.csv
  modified:
    - scripts/phase14_recall.py
    - .planning/phases/14-teach-then-recall-demo/14-VALIDATION.md
key-decisions:
  - "TRANSCRIPTS_PATH renamed to results/phase14_transcripts.md — the code was the outlier against five planning documents, and the report was pointing at a file that would not exist"
  - "the demo's Part B behaviours were exercised through the shipped closures rather than a launched server, because launch() blocks forever and the closures are what a browser calls anyway"
  - "the verdict line is left PENDING — recording it is the blocking human act this plan exists to reach, and both gates passing does not make it automatic"
metrics:
  duration: ~50min
  completed: 2026-08-02
  tasks_complete: 2
  tasks_total: 3
requirements-completed: []
---

# Phase 14 Plan 11: Real Teaching Run + Scored Recall Run Summary

**The adapter recalls taught facts from an empty prompt in a fresh process at 0.4921 taught and
0.3483 held-out, against a base that scores exactly 0.0000 on the identical 2,430 closed-book
prompts — both pre-registered thresholds cleared, with the adapter-off logits bit-identical to the
un-adapted base at max |diff| 0.0.**

## Status: 2 of 3 tasks — STOPPED AT THE BLOCKING HUMAN CHECKPOINT

Tasks 1 and 2 are complete and committed. Task 3 is `checkpoint:human-verify` with
`gate="blocking"`: it requires a human to read the report end to end, spot-check five transcripts
by hand, record the verdict, and exercise the demo in a browser with Wi-Fi off. **No verdict was
guessed.** `results/phase14_recall_report.md` `## Verdict` still reads
`PENDING — user decision at checkpoint.`

## Measured Results

### Recall (DEMO-06 / SC2 / SC3)

| tier | k/N | rate | threshold | gate |
| --- | --- | --- | --- | --- |
| core taught | 496/1008 | **0.4921** | 0.2486 | **PASS** (+0.2435) |
| core held-out | 326/936 | **0.3483** | 0.2000 | **PASS** (+0.1483) |
| closed-book control (adapter off) | 0/2430 | **0.0000** | — | descriptive |
| soft tier (gates nothing, D-05) | 201/486 | 0.4136 | — | excluded |

**The held-out tier is the number that matters.** Held-out means entirely held-out template
FAMILIES — a stimulus the adapter never saw — which is the evidence D-20 part (c) names as
distinguishing *(i) knowledge extracted by reasoning* from *(ii) stimulus-response completion*.
It cleared its threshold by 74% of the threshold's own value. The pre-registered
`## Pre-Registered Failure Branch` was therefore **not** taken, and the report says so by leaving
that section as committed framing rather than as an active claim.

The closed-book control is the strongest form of its statement: **zero** across 2,430 completions,
on the same weights in the same process with the same per-question seeds, only the 36 LoRA
`enabled` flags differing.

### The three D-11 controls

| control | measured | reading |
| --- | --- | --- |
| **1 — question fairness** (D-11.1) | **1/1944 = 0.0005** | the base cannot extract a fact even when it is in its own persona span |
| **2 — no collateral collapse** (D-11.2) | masked dialogue-val PPL 4.5733 → 5.8154, **+27.16%** | trigger tripped; **descriptive, no gate** — calibration pre-recorded the replay arm at +29.39% |
| **3 — adapter-off bit identity** (D-11.3) | `torch.equal` **True** on 5 prompts, max &#124;diff&#124; **exactly 0.0**, on CPU | the demo's OFF state IS the un-adapted base, measured on the real weights |

**Control 1 came back essentially negative, and that is the most important thing for the human to
weigh.** The pre-registered part (a)/(b)/(c) reconciliation committed in 14-10 anticipated exactly
this and it is in the report unamended: (a) a closed-book failure *in isolation* can no longer be
read as unambiguous evidence of absent memory, because this base demonstrably fails to surface a
fact it can see; (b) the phase's claim rests on the adapter-on/adapter-off **differential**, where
the extraction weakness is a property both arms share equally and cancels; (c) the held-out rate is
what separates (i) from (ii). No new metric was introduced and no framing was authored after seeing
the number — `git log -S` shows the framing predates the run.

### Teaching (DEMO-05 / SC1)

| property | value |
| --- | --- |
| episodes / tokens | 220 episodes, 20,036 tokens (10,018 teaching + 10,018 PersonaChat replay at ratio 1.0) |
| paraphrases per fact | inside DEMO-05's `[20, 50]` band for all 10 facts |
| mask fraction | 0.4025 (mean 0.3810, min 0.1884, max 0.6000) |
| wrapped projections / trainable | 36 / **331,776** = `r * n_layer * 18 * n_embd` |
| adapter | 1.35 MB, sha256 `226f2ae5…` |
| canary | **passed** — every trainable moved, every frozen base param bit-untouched |
| held-out leakage | 130 held-out questions, none present in the teaching bin at token level |
| final train loss | 0.6205 |
| base fingerprint | `git_sha=04e724c…`, `step=4000`, `val_loss=1.5235939979553224` — read from the base, matching `convbase_slim.pt` |

### Clean room (SC2)

| fact | teaching run | recall run |
| --- | --- | --- |
| pid | 27638 | **32721** |
| wall clock (UTC) | 2026-08-02T11:29:09Z | **2026-08-02T12:10:49Z** |

Different pid, later wall clock, with the adapter file on disk in between — the process boundary in
its auditable form. `results/phase14_transcripts.md` carries **540 context dumps**, one per
question, each recorded before the model was called.

**Independent leak recheck.** `assert_no_value_in_prompt` guarding the run and a second pass over
the committed evidence are two different claims, so both were made: a separate script re-read all
540 `decoded :` prompt lines and matched them against every locked and soft fact value. **0 prompts
contain a fact value.** The guard's silence and the artifact's content agree.

### The frozen-base sanity anchor, and why two numbers appear

The upstream anchor is ~4.5737 (Phase 12 recorded 4.5733). Both appear in this plan's artifacts and
they are **not** run-to-run noise:

- `results/phase14_teaching_run.log` records adapter-OFF **4.5737** — `teach_persona.train_arm`
  calls `masked_perplexity` **without** `forbid_ids`.
- `results/phase14_recall_report.md` Control 2 records adapter-OFF **4.5733** — the harness passes
  `forbid_ids=forbid`, which is the frozen Phase-12 gate metric ("dead ids forbidden", as the report
  states in place) and matches Phase 12's own 4.5733 exactly.

The 4-in-the-4th-decimal gap is the dead-id mask in the softmax denominator (STATE.md's DEBT-02
policy), reproducible rather than stochastic. Either way the base is intact: Control 3 independently
proves the adapter-off logits are bit-identical to `convbase_slim.pt` at max |diff| exactly 0.0.

## The two adapter-gated tests activated

`tests/test_phase14_demo.py::test_forbid_ids_parity_real_artifacts` and
`::test_build_demo_stylesheets_real` skipped for the entire phase because
`checkpoints/persona_adapter.pt` did not exist. Task 1 produced it. Both now **run and pass**:

| | before 14-11 | after |
| --- | --- | --- |
| full suite | 381 passed, 6 skipped | **386 passed, 1 skipped** |

## Demo verification (SC4) — what was proven without launching a server

`launch()` binds and blocks forever, so the shipped closures were driven directly — the same
functions a browser calls through the event listeners, reached via `demo.fns`:

| check | result |
| --- | --- |
| `build_demo()` constructs against the real adapter | OK — every startup assertion passed |
| `demo.stylesheets` | `[]` (offline lock) |
| startup token panel | `ids   (3) : [8187, 8185, 8186]` — exactly the plan's step-8 expectation |
| **same question, memory ON vs OFF → identical panel** | **True** — `ids  (16) : [8187, 8185, 119, 104, 97, 116, 341, 32, 121, 111, 117, 114, 315, 101, 63, 8186]` both turns |
| answers differ across the toggle | ON `yes, i like to sell marrowgate.` / OFF `i am not. mine is right. i am currently running.` |
| prior bubble's `**memory ON**` stamp after toggling | unchanged |
| Reset | banner `MEMORY: DELETED`; checkbox `interactive: False`, value `False`; Reset button `interactive: False` |
| Ask still works after Reset | yes — answered from the bare base |

**That third-from-bottom row is the phase's central claim in one line: the prompt did not change,
and the answer did.**

One honest note for the human at the checkpoint: the ON draw above **missed**. The demo
deliberately does not mirror the harness's per-question seeding (14-09's recorded reasoning: a
free-text box has no tier index, and the metric is a success *rate* over draws, never one
transcript). At a taught rate of 0.4921 roughly half of single ON turns will miss. Ask a question
two or three times before concluding anything from one bubble.

## Deviations from Plan

### 1. [Rule 3 — blocking] The transcripts artifact path did not match the phase's contract

- **Found during:** Task 2, before the run
- **Issue:** `phase14_recall.TRANSCRIPTS_PATH` pointed at `results/phase14_recall_transcripts.md`,
  an undocumented drift introduced in 14-06 (its own plan specifies `phase14_transcripts.md`).
  14-RESEARCH's layout diagram, 14-PATTERNS, 14-06-PLAN, 14-10-PLAN, 14-VALIDATION, and this plan's
  `must_haves.artifacts` **and** its Task-2 automated verify all name `phase14_transcripts.md`. The
  code was the sole outlier, and the report's `## Clean-Room Evidence` section would have pointed a
  reader at a filename that does not exist.
- **Fix:** renamed the constant and the three prose references (two docstrings plus the report's
  pointer). No behavioural change; the report's framing constants are otherwise untouched and
  `git log -S "Pre-Registered Failure Branch"` still resolves to 14-10's `48d557a`.
- **Files modified:** `scripts/phase14_recall.py`
- **Commit:** `6f873a5`

### 2. [Rule 1 — stale fact] 14-VALIDATION's runtime estimate was measurably wrong

- **Issue:** the tracker claimed "quick: <1 s · full: ~0.75 s (286 tests collected at research
  time)". The suite is now 386 tests and takes ~110 s; the quick run takes 3.74 s. The file
  describes itself as "the living status tracker", so a demonstrably false number in it is a defect.
- **Fix:** both figures re-measured and recorded with their date, and the "Feedback latency < 5s"
  sign-off box ticked against the **measured** 3.74 s rather than an assumption.
- **Commit:** `043bf4d`

### Not a deviation, recorded because it looks like one

`REAL_RUN_SECOND_PERSON` stayed `False` and the family allocation stayed
`{F1,F2,F4,F5,F6}` / `{F3,F7,F8}`. Both are the wave-7 locked configuration and neither was
revisited despite the register arm's negative result — per D-12 that result does not reopen D-01
mid-phase. `TAUGHT_THRESHOLD = 0.2486` / `HELDOUT_THRESHOLD = 0.2000` were not touched;
`git diff` on them is empty.

## Verification

| Check | Result |
| --- | --- |
| `scripts/teach_persona.py real` | **exit 0** |
| Task 1 automated verify (1.35 MB, 331,776 params, fingerprint match) | PASS |
| re-running the real arm without deleting outputs | **exit 1**, naming all five paths |
| `scripts/phase14_recall.py` | **exit 0** |
| Task 2 automated verify (13 report sections, transcripts opener, `ids (N) :`, VALIDATION flags) | PASS |
| independent 540-prompt leak recheck | **0 leaks** |
| `.venv/bin/pytest -q` | **386 passed, 1 skipped** |
| `.venv/bin/ruff check . && ruff format --check .` | clean (132 files) |
| `git diff --quiet -- scripts/demo_app.py` | exit 0 |
| `git diff c3d942e HEAD -- scripts/finetune_ab.py` | empty |
| recall pid/wall-clock differ from teaching's | PASS (27638/11:29:09Z vs 32721/12:10:49Z) |

## Threat Model Coverage

| Threat ID | Mitigation as shipped |
|-----------|----------------------|
| T-14-18 | `assert_no_value_in_prompt` guarded every prompt (the run completing is the proof) **and** an independent pass over all 540 committed dumps found 0 leaks. The five-by-hand spot check remains the human's at the checkpoint — a guard and a reader are different assurances |
| T-14-25 | `snapshot_params` canary passed; `results/phase14_teaching_run.log` capturing it is committed |
| T-14-34 | The run was executed exactly once. `refuse_if_exists` verified to exit 1 on a second attempt naming all five paths; `assert_report_not_clobbered` armed at the top of `main()`. No threshold was touched and no recipe was retried |
| T-14-27 | **Partially covered** — `demo.stylesheets == []` measured, and `test_no_remote_stylesheets` is green. The Wi-Fi-off / empty-cache / devtools observation is by contract an empirical browser check and is the human's at the checkpoint |
| T-14-28 | Control 3 measured max &#124;diff&#124; exactly 0.0 on CPU on the real weights, plus the identical-panel/different-answer pair through the shipped closures |
| T-14-05 | Every fact value is invented; `data/`, `checkpoints/`, `*.pt` stay gitignored; only invented values reach `results/` |
| T-14-SC | Zero new packages |

## Known Stubs

None.

## Threat Flags

None. No new network endpoint, no new deserialization path, no schema change, no new package.

## Artifacts Not Committed (gitignored)

- `checkpoints/persona_adapter.pt` (1.35 MB, sha256 `226f2ae5…`) — the phase's headline
  deliverable. It lives in the main working tree and its digest is recorded in both evidence
  artifacts, which is how a reader ties the committed numbers to the weights that produced them.
- `checkpoints/phase14_real_latest.pt`, `data/persona_real_train{,_mask}.bin` — regenerable
  intermediates.

## Commits

| Commit | Task |
| --- | --- |
| `f93b502` | Task 1 — the real teaching arm, the adapter, the canary, the run log |
| `6f873a5` | Task 2 (pre-run) — transcripts artifact path fix |
| `043bf4d` | Task 2 — both evidence artifacts, the run log, and the validation tracker |

## What Remains — the blocking checkpoint (Task 3)

**Part A — the evidence.** Read `results/phase14_recall_report.md` end to end; spot-check five
prompts in `results/phase14_transcripts.md` by hand; confirm failures are present (they are —
`0/9` rows appear in both tiers); then replace `PENDING — user decision at checkpoint.` under
`## Verdict` with `GO`, `ADAPT`, or `STOP`. **Both gates passed, so no D-12 miss has to be
recorded and `## Ship Decision — post-verdict, discretionary` correctly stays empty.**

**Part B — the demo, in a browser.** `.venv/bin/python scripts/personalize_demo.py` →
http://127.0.0.1:7860. The behaviours listed in the table above are already confirmed at the
handler level; what a browser adds and a handler cannot is: streaming grows monotonically on
screen, the token panel does not move during streaming, the accordion is collapsed at startup, the
slider refuses to drag below its minimum, and — with **Wi-Fi off and an empty cache** — devtools
shows no third-party origin. Then record the demo frame.

## Self-Check: PASSED

- `checkpoints/persona_adapter.pt` — FOUND (1.35 MB)
- `results/phase14_recall_report.md` — FOUND (579 lines, 13 pre-registered sections)
- `results/phase14_transcripts.md` — FOUND (25,609 lines, 540 context dumps)
- `results/phase14_recall_run.log` — FOUND
- `results/phase14_teaching_run.log` — FOUND
- `results/phase14_real/run.csv` — FOUND (20 eval rows)
- `.planning/phases/14-teach-then-recall-demo/14-VALIDATION.md` — FOUND (`nyquist_compliant: true`)
- commit `f93b502` — FOUND
- commit `6f873a5` — FOUND
- commit `043bf4d` — FOUND

---
*Phase: 14-teach-then-recall-demo*
*2/3 tasks complete — stopped at the blocking human verdict, nothing guessed*
