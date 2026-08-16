---
phase: 18-black-box-adversarial-extraction-audit
plan: 11
subsystem: evaluation
tags: [report-renderer, clobber-guard, append-only, run-report, handoff-closed, cpu-only]

# Dependency graph
requires:
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-03's D-04 pin — `K`, `ASR_RUNGS`, `ARMS`, `ATTACK_FAMILIES`, `HOLM_FAMILY`, `VERDICTS`, `TIER_SPLIT_RATIONALE`, `_prove`, the import-time callee register"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-06's `EXPOSURE_RECORD_KEYS` / `EXPOSURE_THREATS_TO_VALIDITY` / `NLL_FRAME_RATIONALE` / `SPREAD_ZERO_CONTROL_SLOTS` — the six published NLL columns and the confound that travels with them"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-07's `null_result_is_admissible` / `ADMISSIBILITY_ZERO_KEYS` (144 cells) / `licensed_conclusion` / `LORA_PROPERTY_CAVEAT` / `LOWER_BOUND_SENTENCE`"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-08's `score_records` / `asr_ladder` / `cumulative_by_attempt` / `aggregate_questions` / `unique_successes` / `CLUSTER_DENOMINATOR_RATIONALE`"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-09's `parse_phase14_taught_rows` / `family_zero_matches` / `run_holm_family` / `assemble_verdict` / `BEST_ATTACK_RULE`"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-10's `run_arm` / `ARM_RECORD_PATHS` / `build_parser` / `main` — the `--report` branch this plan's `run_report` finally answers"
  - phase: 17-persona-isolation
    provides: "`phase17_isolation.render_report` / `assert_isolation_report_not_clobbered` / `append_addendum` / `prereg_commit` — the four registers twinned here"
  - phase: 16-persistence
    provides: "`report_proportion`, `WILSON_LABEL`, `SIGN_TEST_N` — imported, never re-implemented"
  - phase: 15-selective-erasure-preregistration
    provides: "`scripts/_verdict.py::recorded_verdict` — CR-02's one shared anchored read"
provides:
  - "`render_report` / `EXTRACTION_REPORT_PATH` / `_ladder_cell_text` / `_frame_column_label` / `_ladder_block` — every required column, rendered from pre-computed entry dicts alone"
  - "`assert_extraction_report_not_clobbered` / `append_addendum` / `EXTRACTION_SHIP_PENDING_LINE` / `EXTRACTION_SHIP_RECORDED_LINE` — S-6's write-once-then-extend, with no force flag"
  - "`run_report` / `_cell` / `_extracted_questions` — THE 18-10 HANDOFF, closed: `--report` is no longer inert"
  - "`prereg_commit` / `PREREG_PATH` / `INJECTION_BUDGET_DECLARED` / `A2_PREFILL_FRAME_CAVEAT` / `A2_PREFIX_LENGTH_CAVEAT`"
  - "four new committed guards in `tests/test_phase18_docs.py`"
affects: [18-13, 18-14, 18-15, 18-16]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Both ends of a clustering assumption emitted by ONE f-string, so `both or neither` is a property of the renderer rather than a discipline a caller has to remember"
    - "A column header whose ADMISSIBLE / PUBLISHED-BUT-EXCLUDED marker is derived from the gate's own constants, so a post-null switch of the admissible pair moves the label with it"
    - "A mode function given committed-default keyword paths, because the alternative is glue that fires for the first time after two 8.2-hour runs with nothing having ever executed it"

key-files:
  created: []
  modified:
    - scripts/phase18_extraction.py
    - tests/test_phase18_docs.py

key-decisions:
  - "The clobber refusal is `render_report`'s FIRST STATEMENT, not a step `run_report` is trusted to take first. Phase 17 put it in the mode function; here there is no path to the write that skips it, and the RED proof is therefore against the render path itself as Task 2's acceptance requires"
  - "The `## Verdict` section holds the computed verdict and its reasons and NOTHING else, and the ship-decision placeholder lives in its own later section. A `PENDING` token inside the verdict section would tell the clobber guard no verdict had been recorded — the guard would then license overwriting exactly the evidence it exists to protect"
  - "`INJECTION_BUDGET_DECLARED` is the SORTED multiset `(1,1,1,1,1,1,2,2)`, not a slot-keyed vector. D-13 committed it sorted and D-18 verifies it sorted (`the two 2-id slots injected 2`); a slot-keyed version would need the fact set to build, which is the one thing the render path may not reach"
  - "A D-18 divergence RENDERS as a bolded divergence line instead of aborting. The realized-vs-declared comparison is the publication D-18 asks for; aborting would make an 8.2-hour run unreportable over a finding, which is the ATK-04 inversion pointed at the report generator"
  - "The ASR ladder budget is read from the arm record's `config.k`, never from the `K` constant. `asr_ladder` already `_prove`s membership in `ASR_RUNGS`, so a run that spent an off-ladder budget is refused there rather than published at a rung it never drew"
  - "`attack_successes` into the gate is the count of DISTINCT gated questions extracted by ANY attack family, not a sum over families. A question reached by three families is one question that leaked, and the sum would exceed the tier's own denominator"

patterns-established:
  - "`_cell(scored, ...)` — the deliberately EMPTY-TOLERANT slice, next to `_one_slice`'s non-empty `_prove`: a ladder over an empty cell publishes a zero denominator as a finding, while the 144-cell coverage check needs an absent cell to be reportable"

requirements-completed: [STAT-01, STAT-02, STAT-06, ATK-04, ATK-06]

# Metrics
duration: ~70min
completed: 2026-08-16
---

# Phase 18 Plan 11: The Report Renderer, Its Guards, and the Closed Handoff Summary

**The pinned driver is complete — templates, budget, ladder, instruments, admissibility, verdict
and now the report's own text are all committed before a single number exists — and `--report` is
no longer inert: it reaches `run_report`, pairs the two arm records, and refuses by naming the
command that produces the one it is missing.**

## Performance

- **Duration:** ~70 min end to end; the three commits span **26m**.
- **Tasks:** 2, three commits (two task commits plus one grep-legibility correction).
- **Files:** 2 modified. Against the phase-18 base `4f9c198`: **897 insertions / 0 deletions** in
  the pinned driver and **559 / 0** in `tests/test_phase18_docs.py` — **1,456 insertions and ZERO
  removals** for the whole plan. The phase's zero-removal property on the pre-registration holds.
- **Suite:** **715 passed / 7 skipped / 0 failed** in 129s. Exactly the predicted delta:
  `711 (Wave 8 base in a worktree) + 4 new tests = 715`.

## Task Commits

1. **Task 1** — `render_report`, `assert_extraction_report_not_clobbered`, `prereg_commit`, the
   constants, `test_no_bare_zero_percent_in_rendered_report`,
   `test_render_path_never_reaches_the_fact_set` — `d945c29` (feat)
2. **Task 2** — `append_addendum`, **`run_report`**, `test_addendum_append_is_additive`,
   `test_run_report_pairs_two_arms_and_renders` — `ec18cfe` (feat)
3. **Correction** — the clobber guard's docstring stopped spelling the forbidden Verdict split, so
   the acceptance grep stays a guard rather than matching the paragraph rejecting it — `9e8e1ff` (docs)

## Accomplishments

- **The 18-10 handoff is closed, and the closure is visible from a terminal.** `run_report` exists.
  Before this plan `python scripts/phase18_extraction.py --report` refused with *"the report
  renderer ... has not landed yet"*; it now reaches the mode function and exits 1 with
  *"`results/phase18_arm_adapter-on.json` is missing ... run `--arm adapter-on` in its own process
  first"*. The `_prove` on `"run_report" in globals()` is left in place: it still fires if a future
  edit removes the function, which is a cheaper failure than a `NameError` in a 4,857-line driver.
- **No fact value can enter the render path, and that is read off the AST as a transitive closure.**
  The closure over `render_report` is exactly
  `['_frame_column_label', '_ladder_block', '_ladder_cell_text', '_prove',
  'assert_extraction_report_not_clobbered', 'prereg_commit', 'render_report']`, and the only import
  anywhere inside it is `subprocess`. The closure is walked rather than the body scanned, because
  the property is about what the render path CAN reach and not about what today's body happens to
  call. D-11's recorded `slot` is what makes it possible at all.
- **Both denominators are emitted by one f-string.** `_ladder_cell_text` renders
  `question_unit['formatted']` and `fact_unit['formatted']` from a single expression, so
  `CLUSTER_DENOMINATOR_RATIONALE`'s "both or neither" is structural — there is no expression in the
  renderer that produces one without the other. It also `_prove`s the two zeros AGREE: a fact is
  extracted exactly when one of its questions is, so a disagreement can only mean the two units
  were computed over different cells.
- **The all-zero fixture is the test case, because it is this phase's hoped-for outcome.** Every
  proportion in the rendered report is a zero, which is the input that most tempts a bare `0%`. The
  scan runs on the RENDERED TEXT — the half a source scan structurally cannot do — and three
  positive assertions run beside it, because a renderer that dropped its denominators entirely
  would satisfy the bare-zero regex perfectly while publishing exactly the certainty STAT-02
  forbids.
- **A recorded verdict cannot be overwritten, and the refusal is unreachable-around.** The clobber
  guard is `render_report`'s first statement rather than a step the mode function is trusted to
  take, so there is no path to the write that skips it. `grep -cE "force[_-]?flag|--force|force\s*="`
  returns **0** and the absence is a committed regex guard over the whole file.
- **Continuations are provably additive, checked on the produced bytes.** `append_addendum` proves
  the placeholder occurs exactly once, the prefix survives byte-identically, and the recorded
  `## Verdict` section is unchanged — all three against `updated`, never inferred from the
  construction that made it. `placeholder` is a keyword with a committed default because S-6 names
  three surfaces and the two published documents carry their own dated-continuation markers.
- **The glue is exercised end to end before it matters.** `test_run_report_pairs_two_arms_and_renders`
  writes two synthetic arm records, drives the whole pipeline, and then falsifies each pairing proof
  in turn: a swapped pair (both files well-formed, only the filing wrong — the case a
  glob-and-score reader cannot see), a shared pid, a drifted corpus digest, a drifted `k`, and a
  missing record. `run_report` fires for the first time AFTER two 8.2-hour runs, which is precisely
  the position the D-12 pre-flight exists to buy out for the generation path.

## Measurements

Every number below is an **instrument-shape measurement** over committed source and synthetic
records. No model, no checkpoint, no tokenizer and no device is involved anywhere in this plan.
**None of them is a finding about the model.**

### The render path's fact-set closure (Task 1 acceptance, `python`, exit 0)

```
closure over render_report   ['_frame_column_label', '_ladder_block', '_ladder_cell_text',
                              '_prove', 'assert_extraction_report_not_clobbered',
                              'prereg_commit', 'render_report']
imports inside the closure   {'prereg_commit': ['subprocess']}
phase14_factset              0 functions
phase17_persona_facts        0 functions
```

### The all-zero render into a tmp path (Task 1 acceptance, `python`, exit 0)

```
rendered == bytes written on disk         True
rule of three rendered as `3/104`         True
Wilson label (independence-assuming)      True   persistence.WILSON_LABEL, verbatim
question-level denominator                True   `/104 questions`
fact-level denominator                    True   `(fact-level, n = 8)`
D-18 per-slot distribution section        True
D-18 declared vector `[1,1,1,1,1,1,2,2]`  True
D-18 realized multiset agrees             True
bare-zero regex \b0(\.0+)?%               0 matches
`## Verdict` section anchorable           True
ship placeholder occurrences              1
LORA_PROPERTY_CAVEAT verbatim             True   (`PROPERTY OF LoRA`, quoted not retyped)
LOWER_BOUND_SENTENCE                      True
A2 prefill + prefix-length caveats        True
lines rendered                            265
```

### The rendered section order (the `## Verdict` anchor's whole precondition)

```
Pre-Registration · ASR Ladder core_held_out · ASR Ladder core_taught · Cumulative by Attempt ·
A2 Realized Injection (D-18) · Canary Exposure · The Holm Family · Unique Successes ·
The Positive Control · Threats to Validity · VERDICT · Conclusion · Ship Decision · Provenance

headings inside the anchored Verdict body   []   (the section holds the verdict and nothing else)
first line of the body                      **`NULL_ADMISSIBLE`** — returned by null_result_is_admissible
```

### The acceptance greps, as counts

```
grep -c "def render_report"                                       1
grep -c 'split("## Verdict")' / "split('## Verdict')"             0
grep -cE "force[_-]?flag|--force|force\s*="                       0
grep -o "force[a-z-]*" | sort | uniq -c        3 force, 4 forced, 1 forced-choice   (see below)
git log --oneline -- scripts/phase18_extraction.py | wc -l       25   (22 before, +3 here)
ls results/phase18_*                                              no matches
git status --porcelain results/                                   empty
```

### `--report` at the terminal, before and after

```
before (18-10)   exit 1, "the report renderer ... has not landed yet ... Run --smoke, --corpus or --arm"
after  (18-11)   exit 1, "results/phase18_arm_adapter-on.json is missing ... run --arm adapter-on
                 in its own process first (D-07 pairs the arms by dispatching one recorded corpus twice)"
(no arguments)   exit 0, self-check prints 144 cells and 5 INCONCLUSIVE branches
```

## Deviations from Plan

### 1. [Rule 3 — Blocking] `run_report()` did not exist and no plan owned it

- **Found during:** Task 2 (flagged by 18-10's SUMMARY as an explicit handoff)
- **Issue:** The plan's task list names `render_report`, the clobber guard and `append_addendum`,
  and none of them is the mode function `main`'s `--report` branch dispatches to. 18-10 recorded
  the gap as a declared, time-boxed stub: its branch `_prove`s `"run_report" in globals()` and
  refuses legibly rather than raising `NameError`. Without this function `--report` stays inert and
  the phase cannot produce its report at all — 18-16 would have nothing to run.
- **Fix:** `run_report()` added, with the order 18-10's docstring and Phase 17's `run_report_mode`
  both fix: refuse to clobber FIRST and cheapest, read both arm records BY NAME and prove them
  paired, score both arms in one pass through the committed predicate, aggregate, assemble the
  verdict, render. It computes no statistic of its own. `main`'s `_prove` and its `# noqa: F821`
  are deliberately left in place — see *Acceptance criteria reported rather than contorted*.
- **Files:** `scripts/phase18_extraction.py`, `tests/test_phase18_docs.py`
- **Commit:** `ec18cfe`

### 2. [Rule 2 — Missing critical check] Glue that first fires after 8.2 hours needs a committed exercise

- **Found during:** Task 2
- **Issue:** `run_report` reads `ARM_RECORD_PATHS` and writes `EXTRACTION_REPORT_PATH`, both
  committed module constants. D-04 forbids a `results/phase18_*` artifact existing before this pin
  is complete, so with hard-wired paths the function could not be executed even once without
  producing the very artifact the ancestry guard forbids — and it fires for the first time only
  after two 8.2-hour runs. That is the exact failure mode D-12's pre-flight buys out for the
  generation path, left open on the report path.
- **Fix:** `run_report(*, record_paths=ARM_RECORD_PATHS, path=EXTRACTION_REPORT_PATH)` — the same
  keyword-with-committed-default register `render_report(path=...)` already uses.
  `test_run_report_pairs_two_arms_and_renders` then drives the whole pipeline on synthetic records
  in `tmp_path` and falsifies five separate refusals. `ls results/phase18_*` still returns nothing.
- **Commit:** `ec18cfe`

### 3. [Rule 1 — Bug] `erasure_is_worth_attempting` returns a 2-tuple, not a record

- **Found during:** Task 1
- **Issue:** The conclusion section was first written to render
  `verdict['erasure_precondition']['worth_attempting']` and `['reason']`.
  `erasure_gate.erasure_is_worth_attempting` returns `(bool, reason)` — a tuple — so the handoff
  line would have raised `TypeError` at report time, after the run.
- **Fix:** indexed as the tuple it is. Caught by the all-zero fixture on its first render, which is
  why the fixture exercises the LICENSED path rather than only the INCONCLUSIVE one.
- **Commit:** `d945c29`

### 4. [Rule 2 — Missing critical check] The Wilson label is not in `report_proportion`'s `formatted`

- **Found during:** Task 1, on the first RED of `test_no_bare_zero_percent_in_rendered_report`
- **Issue:** `report_proportion` puts `wilson_label` on the returned ROW but does not interpolate it
  into `formatted`, and a renderer that quotes `formatted` and nothing else — which is the common
  case and the one 18-08 already priced — publishes every Wilson bound in the report without the
  label naming it as the INDEPENDENCE-ASSUMING width. That is the assumption this phase's entire
  clustering discussion exists to price, published unlabelled.
- **Fix:** `persistence.WILSON_LABEL` is rendered once in `## Pre-Registration`, stated to cover
  every Wilson bound below it, and asserted present by the committed test. Quoted from the constant,
  never retyped.
- **Commit:** `d945c29`

### 5. The clobber guard landed in Task 1 rather than Task 2

- **Found during:** Task 1
- **Issue:** The plan puts `assert_extraction_report_not_clobbered` in Task 2, but Task 2's own
  acceptance criterion is a RED proof that *"the render path"* raises `SystemExit` on a recorded
  verdict. Making the refusal `render_report`'s first statement is what makes that true; leaving it
  to a caller would satisfy the letter of the split while leaving a reachable path to the write.
- **Fix:** the guard is defined in Task 1 beside `EXTRACTION_REPORT_PATH` and called as
  `render_report`'s first statement. Task 2 keeps `append_addendum`, `run_report` and both of its
  acceptance tests; no acceptance criterion of either task is weakened, and the RED proof is
  stronger than the split would have produced.

### Acceptance criteria reported rather than contorted

**`grep -c "force"` returns 8 lines' worth of matches, not 0, and none of them is a flag.** The
mechanical intent — no override on the clobber refusal — is measured and met:
`grep -cE "force[_-]?flag|--force|force\s*="` returns **0**, and
`test_addendum_append_is_additive` asserts `not re.search(r"--force|force\s*=|force_|_force\b", source)`
over the whole file as a committed guard. The remaining hits are 18-03's *"D-04's **forced** commit
order"*, 18-06's *"a **forced**-choice scorer and a teacher-**forced** NLL"*, *"**Teacher-forced**
NLL"*, *"the teacher-**forced** value-span NLL"*, and three occurrences of the phrase *"no force
flag"* in the two new docstrings that REFUSE to have one. Editing pre-registered content to satisfy
a substring count is forbidden under D-04 and would be strictly worse than the thing the criterion
protects against.

**The Verdict-split grep was 1 and was corrected rather than reported.** The clobber guard's first
docstring spelled the forbidden call verbatim while explaining why it is forbidden — the same
text-scan blind spot 18-10 hit twice. `tests/test_phase15_docs.py:527` already records the
convention explicitly (*"the exact forbidden call is spelled out nowhere in this file so
`grep -c 'split(...)'` stays a usable guard"*), so the docstring was reworded to keep the
explanation without the literal. Count is now **0**. Those 4 replaced lines are the plan's ONLY
in-history line changes and they are invisible against the base: the whole-plan diff against
`4f9c198` is **1,456 insertions and 0 deletions**, because the lines removed had been written by
this same plan two commits earlier.

**`main`'s `_prove("run_report" in globals())` and its `# noqa: F821` are left in place.** Both are
now always-satisfied. Removing them would be four line removals on the pinned driver for no gain:
the `_prove` still fires if a future edit deletes `run_report`, which is a cheaper failure than a
`NameError` for the operator at the terminal. The comment above it saying the renderer *"may not
have landed yet"* is now historical; it is recorded here rather than edited, because a comment
correction is not worth a removal on a pre-registration.

### The six carry-forward corrections, checked and reported

- **`build_corpus` emits 864 A1/A2/A3 entries and NO family-zero entries; family zero is drawn
  through `phase14_recall.complete_question` (18-10).** Honoured and load-bearing. `run_report`
  derives `draws_declared` as `config["corpus_entries"] * config["k"] + PHASE14_TAUGHT_QUESTIONS *
  FAMILY_ZERO_DRAWS` — the two budgets ADDED, never one denominator covering both — and the
  D-18 injection scan reads only `family == "A2"` rows. **No conflict.**
- **`seed_index` is global row order 0..111; D-01's vector is per-question hit COUNTS (18-09).**
  Honoured. `run_report` passes family-zero scored rows to `assemble_verdict` untouched and
  `parse_phase14_taught_rows` supplies the reference; nothing here re-derives an index or a
  granularity. The report publishes `len(mismatches)` as the comparison and the `496/1008` pair
  only under `FAMILY_ZERO_CONSEQUENCE_LABEL`, which says it asserts nothing. **No conflict.**
- **`arm` is part of the scored-record schema; `cumulative_by_attempt` requires `tier` (18-08).**
  Both used as such: every `asr_ladder` and `cumulative_by_attempt` call in `run_report` passes
  `family`, `arm` AND `tier`, and the 144-cell grid keys on `(slot, family, arm, tier)`.
  **No conflict.**
- **The admissibility key space is 144 cells, not 160 (18-07).** Honoured by reference:
  `run_report` iterates `ADMISSIBILITY_ZERO_KEYS` and never rebuilds or narrows it. The
  argumentless self-check still prints **144**. **No conflict.**
- **D-29's f4-vs-f3 frame separation is UNOBTAINABLE, equal by construction (18-06).** Honoured.
  The exposure table publishes all six frame x reduction columns and the renderer draws NO contrast
  between any two of them; `NLL_FRAME_RATIONALE` — which records the identity and reframes it as an
  internal control — is rendered verbatim into the section. **No conflict.**
- **ATK-06's `LORA_PROPERTY_CAVEAT` is committed with `PROPERTY OF LoRA` in caps (18-12).**
  Honoured. The Threats to Validity section interpolates the constant; the phrase is nowhere
  retyped in this plan. Asserted verbatim in the acceptance run. **No conflict.**

## Verification

| Check | Result |
|---|---|
| `pytest -q` (full suite) | **715 passed, 7 skipped, 0 failed** in 129s |
| `pytest -q tests/test_phase18_docs.py` | 8 passed (4 inherited + 4 new) |
| `pytest -q tests/test_phase18_docs.py --collect-only` | 18-12's `test_docs_continuation_is_additive` and `test_no_bare_zero_percent_in_docs` **both still listed** alongside this plan's four — no `def` shadowed |
| `pytest -q tests/test_phase18_{corpus,draws,prereg,widenings}.py` | 61 passed — Waves 1–8's guards untouched |
| `pytest -q tests/test_phase16_prereg.py -k phase18` | 1 passed — the D-04 ancestry pin |
| `python scripts/phase18_extraction.py` | exit 0, self-check prints 144 cells |
| `python scripts/phase18_extraction.py --report` | exit 1, names the missing arm record and the command that produces it |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 161 files already formatted |
| `grep -c "def render_report"` | **1** |
| `grep -c 'split("## Verdict")'` \| `"split('## Verdict')"` | **0** |
| `grep -cE "force[_-]?flag\|--force\|force\s*="` | **0** |
| `ls results/phase18_*` | no matches — this plan writes no artifact |
| `git status --porcelain results/` | empty |
| Files deleted by any commit | **0** |
| Removals vs the phase base `4f9c198` | **0** across both files |
| `git log --oneline -- scripts/phase18_extraction.py \| wc -l` | **25** |

## Threat register disposition

| Threat ID | Disposition | Discharged by |
|---|---|---|
| T-18-11-01 (Repudiation — a zero without its denominator and ceiling) | mitigated | Every proportion through `report_proportion`; the bare-zero `_prove` runs on the RENDERED text before a byte is written; the all-zero fixture is the committed test case and asserts the ceiling, the label and both denominators PRESENT in the same pass |
| T-18-11-02 (Repudiation — only the flattering question-level denominator) | mitigated | `_ladder_cell_text` emits both from ONE f-string, and `_prove`s the two zeros agree — a fact is extracted exactly when one of its questions is |
| T-18-11-03 (Information Disclosure — a fact value via a fact-set import) | mitigated | Transitive AST closure over `render_report`: 7 functions, one import (`subprocess`), zero fact-set modules. Entries carry D-11's `slot` |
| T-18-11-04 (Tampering — a re-render destroys a recorded verdict) | mitigated | Clobber guard anchored via `_verdict.recorded_verdict`, called as `render_report`'s FIRST statement so no path to the write skips it; no force flag in any spelling, asserted as a committed regex; `append_addendum` is the only post-verdict path and proves additivity on the produced bytes |
| T-18-11-05 (Repudiation — exposure published without its length confound) | mitigated | `EXPOSURE_THREATS_TO_VALIDITY` rendered into a required `## Threats to Validity` section; the per-slot token-length spread is a required column beside every exposure figure; the spread-0 control is reported as having RUN |
| T-18-11-SC (Tampering — package installs) | accepted | Zero installs; `pyproject.toml` untouched |

## Issues Encountered

- **Worktree base drift, tenth consecutive plan.** HEAD was `829cd5f`, a strict ancestor of the
  required `4f9c198` with a clean tree, so `git merge --ff-only` corrected it with 0 commits lost.
- **The first render raised on `erasure_precondition`** — Deviation 3. The all-zero fixture drives
  the LICENSED path, which is the only reason it surfaced before 18-16.
- **The Wilson label was absent from the rendered text** — Deviation 4, caught by the first RED.
- **The Verdict-split grep matched a docstring rejecting the thing** — the third instance of this
  blind spot in the phase, and the reason both new guards in this plan read the AST rather than
  the text wherever the property is structural.
- **Six `ruff` E501s and two reformats**, all in docstrings, comments and f-string assertion
  messages; reflowed or bound to locals before their commits. No logic involved.

## Deferred Issues

None new. The one item in `deferred-items.md` is 18-04's and is untouched.

## Known Stubs

**None. 18-10's single declared stub is CLOSED** — `run_report()` exists, is dispatched by
`main`'s `--report` branch, and is exercised end to end by a committed test.

`grep -c "TODO\|FIXME\|placeholder"` returns **10** for the driver and **6** for the test file, and
every hit is the WORD "placeholder": nine are `append_addendum`'s `placeholder` parameter and the
docstring describing it, one is 18-06's pre-existing `{v}` template token that 18-07 through 18-10
all reported, and the six in the test file are the addendum test's own vocabulary. No `TODO` and no
`FIXME` anywhere in either file.

## User Setup Required

None — no external service configuration required. `--report` needs both
`results/phase18_arm_*.json` records on disk and refuses by name when either is absent. It loads no
model, no checkpoint, no tokenizer and no device.

## Threat Flags

None. No new network endpoint or auth path. Two new **file-access patterns**, both inside function
bodies and neither at import: `render_report` writes its `path` argument (default
`EXTRACTION_REPORT_PATH`, behind the clobber refusal that is its own first statement) and
`append_addendum` reads and rewrites the path it is given (behind the exactly-one-placeholder
proof). `run_report` reads the two arm records and `prereg_commit` shells out to `git log`. The
import-time callee register is a hard equality and is **unchanged** — the new module-level names
are a `pathlib` division, a tuple literal and four strings, none of which is a `Call` node, and
`test_nothing_loads_at_import` stays green. Nothing in this plan writes to disk when nothing calls
it, so `results/phase18_*` still does not exist and every commit here remains a legitimate ancestor
under D-04.

## Next Phase Readiness

- **The pre-registration is COMPLETE.** Every one of D-04's named components — attack templates,
  `K`, the injection budget, the ASR ladder, the NLL instruments, the admissibility gate, the
  verdict domain, the closing paragraph's generator and now the report's own text — is committed
  before a single number exists. **The ancestry guard arms on the next `results/phase18_*`
  first-add**, which is 18-13's pre-flight report.
- **18-13 / 18-14 / 18-15 are unchanged by this plan.** `--smoke`, `--corpus` and `--arm` were not
  touched; the only edits to `main`'s surrounding code are none.
- **18-16 can run `--report` as-is.** It requires both arm records on disk, writes
  `results/phase18_extraction_report.md` once, and refuses every subsequent render because the
  rendered `## Verdict` section carries a computed verdict rather than `PENDING`. The human then
  records the ship decision by replacing `EXTRACTION_SHIP_PENDING_LINE` through `append_addendum`,
  which is the only path by which that file, `README.md` or `docs/REPORT.md` may grow afterwards.
- **What a D-18 divergence will look like.** If the realized multiset disagrees with
  `[1,1,1,1,1,1,2,2]` the report renders a bolded **D-18 DIVERGENCE** line naming both multisets
  and stating that every A2 number was produced under the realized budget. It does not abort —
  aborting would make an 8.2-hour run unreportable over a finding.
- **Carried forward, all six checked above:** 18-06's `f4_reversed` ≡ `f3_bare` identity, 18-07's
  144-cell key space, 18-08's `arm` axis and `tier` requirement, 18-09's global `seed_index` and
  count-granularity vector, 18-10's corpus/family-zero split, and 18-12's caps-exact
  `LORA_PROPERTY_CAVEAT`.

## Self-Check: PASSED

- `scripts/phase18_extraction.py` — FOUND (4,857 lines; contains `def render_report`,
  `def assert_extraction_report_not_clobbered`, `def append_addendum`, `def run_report`,
  `def prereg_commit`, `def _ladder_cell_text`, `def _frame_column_label`, `def _ladder_block`,
  `def _cell`, `def _extracted_questions`, `EXTRACTION_REPORT_PATH`, `PREREG_PATH`,
  `INJECTION_BUDGET_DECLARED`, `EXTRACTION_SHIP_PENDING_LINE`)
- `tests/test_phase18_docs.py` — FOUND (978 lines, ≥200 required; 8 tests, 4 of them this plan's)
- `d945c29`, `ec18cfe`, `9e8e1ff` — all FOUND in `git log`
- `git status --short` clean apart from this SUMMARY
- No `STATE.md`, `ROADMAP.md` or `REQUIREMENTS.md` touched — the orchestrator owns them
- No file deleted by any commit; **0 removals** against the phase base
- `ls results/phase18_*` returns nothing — this plan writes no artifact

---
*Phase: 18-black-box-adversarial-extraction-audit*
*Completed: 2026-08-16*
</content>
</invoke>
