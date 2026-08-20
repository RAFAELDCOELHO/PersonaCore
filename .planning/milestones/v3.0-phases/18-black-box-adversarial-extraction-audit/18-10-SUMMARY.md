---
phase: 18-black-box-adversarial-extraction-audit
plan: 10
subsystem: evaluation
tags: [run-surface, preflight-smoke, process-split, argparse, provenance, cpu-only]

# Dependency graph
requires:
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-03's D-04 pin — `K`, `ARMS`, `ATTACK_FAMILIES`, `FAMILY_ZERO`, `FAMILY_ZERO_DRAWS`, `REPORTED_TIER`, `_prove`, the import-time callee register"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-05's `build_corpus` / `CORPUS_PATH` / `CORPUS_ENTRY_KEYS` / `canonical_json` / `corpus_sha256` — the corpus this surface builds, writes and dispatches"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-06's `value_span_nll` / `reference_set_for` / `exposure_rank` / `assert_spread_zero_reductions_agree` / `measure_exposure` — the D-28 path the smoke exercises"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-08's `DRAW_RECORD_KEYS` — the record shape `run_arm` writes"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-09's `PHASE14_TAUGHT_QUESTIONS` — the 112 family zero must cover"
  - phase: 17-persona-isolation
    provides: "`phase17_persona_gate.build_unadapted_base` — the adapter-free load, imported and never copied"
  - phase: 14-teach-then-recall
    provides: "`draw_all`, `complete_question`, `load_adapted_model`, `assert_no_value_in_prompt` — all imported, none re-implemented"
provides:
  - "`run_smoke` / `SMOKE_REPORT_PATH` / `DEGENERATION_PRIORS` / `SMOKE_PROMPTS_PER_SHAPE` / `SMOKE_DRAWS_PER_PROMPT` / `_rate_lower_bound` / `_smoke_sample` / `_render_smoke_report` — D-12's four-shape pre-flight on the base, with a measured rate and D-28's NLL coverage"
  - "`run_arm` / `ARM_RECORD_PATHS` / `_guarded_span` — one recorded prompt, two arms, one draw loop, full provenance"
  - "`build_parser` / `main` / `run_corpus` / `_USAGE` / `_resolved_device` — four modes, no two-arm mode"
  - "three new committed guards in `tests/test_phase18_prereg.py`"
affects: [18-11, 18-13, 18-14, 18-15, 18-16]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A degeneracy floor written as a NON-OVERLAP test between two intervals from ONE committed instrument, so the threshold is derived from a measured prior instead of chosen, and the small-sample noise the prior cannot see is priced rather than ignored"
    - "A lower bound built as the complement of the committed UPPER bound on the failure rate — one pinned interval answering both questions, so there is no second interval free to disagree"
    - "A parser mode whose dispatch target lands in a LATER commit, guarded by a `_prove` that names the plan, because a `NameError` sends a terminal operator to read a 3,900-line pinned driver to discover an ordering"

key-files:
  created: []
  modified:
    - scripts/phase18_extraction.py
    - tests/test_phase18_prereg.py

key-decisions:
  - "Family zero draws through `phase14_recall.complete_question`, not through a locally built bare prompt. The AST guard forbids `build_recall_prompt` inside `run_arm`, and D-01 compares 112 taught rows against the report THAT function produced — a second bare-prompt path would be compared against numbers it did not generate. It also keeps the unstrided `1337 + index + s` stream verbatim, with `N_SEEDED_SAMPLES = 8` giving exactly `FAMILY_ZERO_DRAWS = 9`"
  - "A2's `prefix_text` is decoded off the ARTIFACT's own appended tail — `prompt_ids[-realized_injection:]` — rather than re-derived from the fact value through `split_value_ids`. D-15 appends verbatim and D-18's `realized_injection` measures that run, so the tail IS the prefix; reading it there keeps the fact set off the A2 scoring path entirely and records the text the model actually received"
  - "Both new drawing paths assert the clean room IN PLACE rather than naming an asserter in `DRAW_ALL_ASSERTED_BY`. `run_arm`'s prompts come off disk, so a registry entry would excuse it by pointing at a guard that ran in a different process; `_guarded_span` recovers D-16's partition from a corpus entry alone, so the check runs on the ids about to be dispatched"
  - "`_guarded_span` is ONE function called from both modes. D-16's argument is that the two checks must not be able to cancel, and a partition spelled twice is a partition that can drift between the pre-flight and the run"
  - "The smoke writes `SMOKE_REPORT_PATH` itself. 18-13's acceptance requires the file to exist with a provenance block; leaving the text on stdout would make a human hand-assemble the artifact the K decision is taken from"
  - "`run_corpus` serializes through `canonical_json` with NO trailing newline, because 18-14's standing guard re-derives the corpus and asserts BYTE equality — a newline added for tidiness would fail that guard for a reason unrelated to the corpus"

patterns-established:
  - "`_guarded_span(entry)` — a security partition recovered from a recorded artifact, so the guard can be re-run at dispatch without the fact set and without a rebuild"

requirements-completed: [ATK-01, ATK-02, ATK-03, STAT-05]

# Metrics
duration: ~65min
completed: 2026-08-16
---

# Phase 18 Plan 10: The Run Surface — Smoke, Arms, Parser Summary

**`scripts/phase18_extraction.py` can now be operated from a terminal, and the only thing it cannot
be made to do is run both arms in one process — the four modes are mutually exclusive, `--arm`
takes one constrained name, and the pre-flight that decides K is structurally incapable of
touching the taught column.**

## Performance

- **Duration:** ~65 min end to end; the four task commits span **21m**.
- **Tasks:** 3, four commits (three task commits plus one report-legibility correction).
- **Files:** 2 modified — **971 insertions / 2 deletions** in the pinned driver, **287 / 0** in
  `tests/test_phase18_prereg.py`. The whole plan is **1,256 insertions and 2 deletions**.
- **Suite:** **711 passed / 7 skipped / 0 failed** in 128s. The arithmetic is the predicted worktree
  delta exactly: `707 (Wave 8 base, itself 713 on main − 6 worktree-only skips) + 3 new tests + 1
  = 711`, the `+1` being the extra `test_phase18_prereg.py` node this plan's three tests add on top
  of Wave 7's count as merged.

## Task Commits

1. **Task 1** — `run_smoke`, `DEGENERATION_PRIORS`, `_rate_lower_bound`, the two AST guards — `e37395e` (feat)
2. **Task 2** — `run_arm`, `ARM_RECORD_PATHS`, `test_one_corpus_two_arms` — `98c8185` (feat)
3. **Task 3** — `_USAGE`, `build_parser`, `main`, `run_corpus`, `_guarded_span`, `test_no_multi_arm_mode` — `745bc61` (feat)
4. **Correction** — `draws_per_min` rendered once per shape; the docstring's percent claim fixed — `7f7d8b7` (docs)

## Accomplishments

- **The pre-flight cannot preview the taught column, and that is read off the AST.**
  `run_smoke` builds the pure base through `phase17_persona_gate.build_unadapted_base` — the
  function Phase 17 wrote because the recall loader *has no un-adapted return path* and would
  silently hand back a taught model. Measured: `persona_adapter`, `inject_lora` and
  `adapter_disabled` appear **0 times** in `run_smoke`'s source segment (docstring included) and
  `adapter_disabled` appears in `run_arm`'s. The docstring is still free to *explain* why it
  declines the adapted load, because the guard reads the AST and not the text.
- **The smoke's prompts are built in memory and the artifact is never read.** Asserted as an
  absence of a `CORPUS_PATH` **Name node**, an absence of `open` / `json.load` / `json.loads`
  calls, and the presence of a `build_corpus` call. `results/phase18_corpus.json` is committed one
  wave *after* the smoke runs, so a file read would abort the phase's most expensive gate on an
  artifact that cannot exist yet.
- **The degeneracy floor is a non-overlap test, not a point comparison.** D-12 says "floored
  against the measured priors rather than an invented threshold", and a literal point test at 64
  draws would abort on noise: the 56/936 prior is 3.83 expected hits with a spread of about 2.
  `_rate_lower_bound` builds the observed rate's 95% lower bound as the complement of
  `wilson_upper_bound` on the FAILURE rate — the same pinned instrument, no second interval — and
  the abort fires only when the two intervals are disjoint. Measured: that puts the abort at **9 of
  64** for the role-token attractor and **8 of 64** for the college-student one, a **1.7%** chance
  of firing on a base behaving exactly as Phase 17 measured it, against a certainty of firing on a
  shape that has actually collapsed.
- **D-28's NLL path is exercised before the run, and finiteness is checked rather than assumed.**
  The smoke scores every candidate in R across all 8 slots x 3 frames x 2 reductions and `_prove`s
  `math.isfinite` on each — calling the function proves it returns, and the failure D-28 names is a
  NaN, which returns perfectly well and then ranks unpredictably. The spread-0 control is proved to
  have **RUN**, not merely to have not raised: `assert_spread_zero_reductions_agree` returns `False`
  on the six confounded slots, so a control that silently did not run is otherwise
  indistinguishable in the report from one that ran and agreed.
- **One prompt object, two arms, one draw loop.** `test_one_corpus_two_arms` asserts off the AST
  that none of `apply_a1` / `build_a1` / `build_a2_prompt` / `build_a3_prompt` /
  `build_recall_prompt` is called inside `run_arm`, and that its `draw_all` call sites are
  **exactly `['recall.draw_all']`** — a second loop is how two arms stop being paired while both
  still look like they ran.
- **The base column's inertness has a runtime witness.** `LoRALinear.enabled` is a plain Python
  bool kept out of `state_dict()`, so no weight digest and no artifact can see it. `run_arm` asserts
  **inside** the context manager that no `LoRALinear` is still enabled — without it, a broken
  `adapter_disabled` would produce a negative control that is a second copy of the taught column
  wearing the other label, and every null in this phase would rest on it.
- **There is no way to spell a two-arm invocation.** Three routes are closed and each is asserted:
  a fifth mode (the group's four dests are pinned by hard equality), an out-of-family arm name
  (`--arm both` exits **2**, naming both legal choices), and accumulation (`nargs in (0, None)`, no
  `_AppendAction`; a repeated `--arm` overwrites and yields one `str`).
- **The argumentless invocation still proves the gate.** `python scripts/phase18_extraction.py`
  exits **0** printing the 144-cell self-check, because the `__main__` guard branches on
  `sys.argv[1:]` before the parser is reached — so "run the CPU self-check" and "fall through to
  something reasonable" stay different things, and the reasonable-looking thing here is an
  eight-hour generation run.

## Measurements

Every number below is an **instrument-shape measurement** over committed source, synthetic records
and committed constants. No model, no checkpoint, no tokenizer and no device is involved anywhere
in this plan. **None of them is a finding about the model.**

### The AST scope proofs (acceptance, `python -c`, exit 0)

```
run_smoke   persona_adapter False   inject_lora False   adapter_disabled False
run_arm     persona_adapter False   inject_lora False   adapter_disabled True

run_smoke   CORPUS_PATH as a Name node   False
run_smoke   open / json.load / json.loads calls   none
run_smoke   build_corpus call   present
run_arm     draw_all call sites   ['recall.draw_all']
run_arm     prompt-construction calls   []
```

`persona_adapter` and `inject_lora` are **0 in the whole file**, not only in `run_smoke` — see
"Acceptance criteria reported rather than contorted" below.

### The degeneracy floor, priced (`python -c`, against the committed `wilson_upper_bound`)

```
attractor                    prior     prior 95% upper   aborts at   expected   P(false abort)
<|assistant|> leakage        56/936    0.073894          >= 9 / 64      3.83         0.0167
college-student attractor    47/936    0.063306          >= 8 / 64      3.21         0.0172
```

At the pre-registered 8 prompts x 8 draws per shape. A point comparison against the prior rate
would abort at 4 of 64, which the prior itself predicts about 40% of the time.

### The rendered pre-flight report, from a synthetic record (`python -c`, exit 0)

```
lines rendered                            81
bare-zero regex \b0(\.0+)?%                0 matches
adapter-on|persona_adapter|adapter_disabled  0 matches (case-insensitive)
lines containing draws_per_min             4  — one per prompt shape
projected wall clock                       derived from the four measured rates, derivation shown
```

Both remaining `%` characters in the file are inside the phrase "95% bound", which names a
confidence level rather than reporting a measurement.

### The parser surface (`test_no_multi_arm_mode`, and at the terminal)

```
mutually exclusive groups                 1, required
mode dests                                ['arm', 'corpus', 'report', 'smoke']  (hard equality)
--arm choices                             ('adapter-on', 'adapter-off')  == ARMS
--arm both                                exit 2, "invalid choice: 'both' (choose from ...)"
--smoke --arm adapter-on                  exit 2, "not allowed with argument --smoke"
--arm X --arm Y                           parses to the single str 'adapter-off', never a list
(no arguments)                            exit 0, self-check prints 144 cells
```

### Ancestor set for the STAT-05 guard

```
git log --oneline -- scripts/phase18_extraction.py | wc -l     22
```

Nineteen before this plan, three added here. This set grows **once more** in 18-11, and every
`results/phase18_*` first-add must descend from all of it.

## Deviations from Plan

### 1. [Rule 2 — Missing critical check] Both new drawing paths must assert the clean room in place

- **Found during:** Task 3, on the full-suite run
- **Issue:** `tests/test_phase14_scoring.py::test_every_draw_all_call_site_asserts_something` — a
  live PERS-06 guard — failed on `scripts/phase18_extraction.py::run_smoke`. It requires every
  `draw_all` call site either to call an in-prompt assertion itself, or to be named in
  `DRAW_ALL_ASSERTED_BY` against a same-file asserter. Both of this plan's drawing paths were
  unchecked. The guard's own wording is the argument: "a path that draws without asserting either
  is a path where NEITHER property is checked — the rate it reports measures nothing while still
  looking like a measurement."
- **Fix:** both `run_smoke` and `run_arm` call `recall.assert_no_value_in_prompt` on the ids they
  are about to dispatch, over `_guarded_span(entry)` — D-16's partition, recovered from a corpus
  entry alone. The registry route was **declined for `run_arm`**: its prompts come off disk, so
  naming `build_corpus` would excuse a drawing path by pointing at a guard that ran in a different
  process, and D-03 widened `assert_no_value_in_prompt` with a `prompt_ids` path precisely so the
  corpus could be checked against *the bytes the model receives*. Cost is microseconds against an
  eight-hour run. `tests/test_phase14_scoring.py` is **byte-untouched**.
- **Files:** `scripts/phase18_extraction.py`
- **Commit:** `745bc61`

### 2. [Rule 3 — Blocking] Family zero has no corpus entries, and `build_recall_prompt` is forbidden

- **Found during:** Task 2
- **Issue:** The plan's action says family zero is dispatched from the corpus with the unstrided
  `seed_index`. It is not in the corpus: `build_corpus` `_prove`s its families equal
  `ATTACK_FAMILIES` and 18-14 pins the artifact at exactly **864** entries, all A1/A2/A3. So the
  112 bare taught prompts have to come from somewhere — and Task 2's own acceptance criterion
  forbids calling `build_recall_prompt` anywhere inside `run_arm`.
- **Fix:** family zero draws through `phase14_recall.complete_question`, reading its questions and
  their unstrided `seed_index` from the binding fixture. That is strictly better than either
  alternative: it is **Phase 14's own function**, the one whose output produced the 496/1008
  reference rows D-01 compares against, so the reproduction traverses the instrument rather than a
  copy of it. Its `N_SEEDED_SAMPLES = 8` default yields exactly `FAMILY_ZERO_DRAWS = 9`, asserted
  per question. `run_arm`'s `draw_all` call sites stay at exactly one.
- **Commit:** `98c8185`

### 3. [Rule 2 — Missing critical check] `run_arm` asserts the base column entered generation inert

- **Found during:** Task 2
- **Issue:** The plan asks for `adapter_disabled` on the off arm and nothing more. The gate is a
  plain Python bool kept out of `state_dict()`, so the recorded `adapter_enabled: False` is a
  claim no digest, no artifact and no later reader can check. A silently ineffective context
  manager would make the negative control a second copy of the taught column — and every null in
  this phase rests on the two arms differing only in that gate.
- **Fix:** Phase 17's ISO-03 runtime witness, ported: inside the context, `_prove` that no
  `LoRALinear` is still `enabled`, naming the modules that were.
- **Commit:** `98c8185`

### 4. `--report` dispatches to a function this plan does not define

- **Found during:** Task 3
- **Issue:** The plan requires `--report` in the parser and an exhaustive `main` with no default
  branch. The renderer is **18-11's** — that plan adds `render_report`, the clobber guard and
  `append_addendum` — and no plan in the phase owns the mode function that assembles the report
  from the arm records. Defining it here would preempt 18-11's design (`render_report` takes
  pre-computed entry dicts whose shape that plan chooses).
- **Fix:** the `--report` branch `_prove`s `"run_report" in globals()` before calling it, with a
  message that says nothing is wrong with the invocation and names the modes that do work. The
  call carries `# noqa: F821`. **Handoff to 18-11: add `run_report()`** — the glue that reads both
  arm records, scores them, aggregates, calls `assemble_verdict` and renders. A `NameError` here
  would send a terminal operator to read a 3,900-line pinned driver to discover a plan ordering.
- **Commit:** `745bc61`

### 5. The `__main__` guard's two lines are replaced — the phase's zero-removal streak ends, by instruction

- **Found during:** Task 3
- **Issue:** Every prior plan in this phase kept `git diff | grep '^-'` empty on the pinned driver.
  Task 3's action explicitly requires changing the `__main__` block so an argumentless invocation
  still runs the self-check while a flagged one dispatches.
- **Fix:** recorded rather than worked around. The whole-plan diff against `ee78ea4` is **1,256
  insertions and 2 deletions**, and both deletions are the old two-line `__main__` block, replaced
  by a five-line branch. **No pre-registered content was removed**: no constant, no rationale
  literal, no function, no docstring. The self-check is verified still reachable — `python
  scripts/phase18_extraction.py` exits 0 and prints 144 cells. Zero files deleted by any commit.

### Acceptance criteria reported rather than contorted

**`grep -c "force"` returns 4, not 0.** All four predate this plan and none is a flag:
"D-04's **forced** commit order" (`:682`), "a **forced**-choice scorer and a teacher-**forced**
NLL" (`:965`), "**Teacher-forced** NLL of `value_ids`" (`:1040`), and "the teacher-**forced**
value-span NLL" (`:1690`). Satisfying the criterion literally would mean editing pre-registered
content under the D-04 pin, which is forbidden and would be a strictly worse outcome than the one
the criterion protects against. The criterion's **intent** — no override on the clobber refusal —
is measured and met: `grep -cE "force[_-]?flag|--force|force\s*="` returns **0**, and
`test_one_corpus_two_arms` asserts `not re.search(r"--force|force\s*=|force_|_force\b", source)`
over the whole file as a committed guard.

**`persona_adapter` and `inject_lora` appear 0 times in the entire driver, `run_arm` included.**
The criterion says "every occurrence must be inside `run_arm`, never inside `run_smoke`". Zero
occurrences satisfies the half that matters and the half that is checkable; `run_arm` reaches both
through `recall.load_adapted_model`, which is the point — the loader is imported, not
re-implemented. `adapter_disabled` is the one token that does appear, exactly once, inside
`run_arm`, and both halves are asserted.

**`grep -c "56\|47"` is reported as its content, not its count.** That grep matches any line
holding those two digit pairs anywhere and is not evidence of anything. What was asserted instead,
as a committed test, is that `DEGENERATION_PRIORS["attractors"]` carries exactly `{(56, 936),
(47, 936)}` read off the loaded module, and that its `note` contains `NOT PHASE 18 FINDINGS`.

**`run_smoke`'s docstring mentions `load_adapted_model` and `CORPUS_PATH`.** Both appear only in
the paragraphs explaining why the smoke uses neither — which the plan's action explicitly asks for
("record in the docstring that this is a different load"). The acceptance criterion specifies an
**AST walk**, and measured that way both are absent: no `CORPUS_PATH` Name node and no
`load_adapted_model` attribute access. This is the same instrument choice 18-08 and 18-09 made for
the same reason: a text scan is equally happy inside the paragraph rejecting the thing.

**`test_smoke_scope_is_base_only` does not assert on `run_arm`.** The plan's Task 1 acceptance
requires that node to pass at Task 1, when `run_arm` did not yet exist. The other half of the scope
claim — that `adapter_disabled` DOES appear in `run_arm`, so the base column is gated rather than
not gated at all — lives in `test_one_corpus_two_arms`, which is where the arm's structure is
asserted, and is cross-referenced from both docstrings.

### The four wave carry-forwards, checked and reported

- **`seed_index` is global row order 0..111 (18-09).** Honoured and load-bearing. `run_arm` reads
  family zero's `seed_index` **verbatim from the binding fixture** and passes it unstrided to
  `complete_question`; it derives no index from question text and re-numbers nothing. The 112 rows
  it draws are the same rows in the same order `parse_phase14_taught_rows` reads. `_prove`d against
  `PHASE14_TAUGHT_QUESTIONS`. **No conflict.**
- **`arm` is on the scored record (18-08).** Every draw record `run_arm` writes carries
  `arm=arm`, on both the 864 attack rows and the 112 control rows, so `score_records` passes it
  straight through to `SCORED_RECORD_KEYS` and `_one_slice` can filter on it. **No conflict.**
- **144-cell admissibility key space (18-07).** Untouched — nothing in this plan reads
  `ADMISSIBILITY_ZERO_KEYS` or builds a cell grid; the self-check still prints **144**.
  **No conflict.**
- **D-29's f4-vs-f3 identity (18-06).** The smoke scores all three frames and asserts only
  FINITENESS, never a contrast between them, so the unobtainable f4-vs-f3 separation is neither
  relied on nor reported. **No conflict.**

### One observation, recorded and deliberately not acted on

D-06's stride is `seed_index * K`, and `seed_index` is **tier-local**: the taught tier numbers
0..111 and the held-out tier 0..103. So `(core_taught, 0)` and `(core_held_out, 0)` receive the
same 64-seed window, and the four families derived from one source question share a window too.
D-06's stated purpose — eliminating *cross-question* sharing within a tier, which at K=64 would
otherwise span 63 neighbours — is achieved. The remaining sharing is across different prompts,
where the probability vectors differ. **The plan's action names `record["seed_index"] * K`
explicitly and it is a D-04 pre-registration; changing the seed derivation would change what gets
measured, so it is reported here rather than silently reinterpreted.**

## Verification

| Check | Result |
|---|---|
| `pytest -q` (full suite) | **711 passed, 7 skipped, 0 failed** in 128s |
| `pytest -q tests/test_phase18_prereg.py` | 26 passed (23 inherited + 3 new) in 1.4s |
| `pytest -q tests/test_phase18_{corpus,draws,docs,widenings}.py` | 36 passed — Waves 1–7's guards untouched |
| `pytest -q tests/test_phase14_scoring.py` | 42 passed — PERS-06's draw-site guard green with no registry edit |
| `pytest -q tests/test_phase16_prereg.py -k phase18` | 1 passed — the D-04 ancestry pin |
| `python scripts/phase18_extraction.py` | exit 0, self-check prints 144 cells, no model/checkpoint/device |
| `python scripts/phase18_extraction.py --arm both` | exit 2, argparse names both legal choices |
| `python scripts/phase18_extraction.py --smoke --arm adapter-on` | exit 2, "not allowed with argument --smoke" |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 161 files already formatted |
| `git diff --exit-code tests/test_phase14_scoring.py` | exit 0 — byte-untouched |
| `grep -cE "force[_-]?flag\|--force\|force\s*="` (driver) | **0** |
| `grep -c "corpus_sha256"` (driver) | **6** — the definition plus five uses |
| `ls results/phase18_*` | no matches — nothing here writes to disk |
| `git status --porcelain results/` | empty |
| Files deleted by any commit | **0** |
| Removals from either file vs `ee78ea4` | **2**, both the old `__main__` block (Deviation 5) |
| `git log --oneline -- scripts/phase18_extraction.py \| wc -l` | **22** |

## Threat register disposition

| Threat ID | Disposition | Discharged by |
|---|---|---|
| T-18-10-01 (Tampering — a prompt rebuilt inside an arm unpairs the arms) | mitigated | AST proof that no prompt-construction call exists inside `run_arm`, and that its `draw_all` sites are exactly `['recall.draw_all']`; the corpus sha256 is recorded per arm; family zero routes through Phase 14's own `complete_question` rather than a second bare-prompt path |
| T-18-10-02 (Information Disclosure — the smoke previews the taught column) | mitigated | AST scope proof over `run_smoke`'s source segment: zero occurrences of the three adapter tokens, docstring included; the base is built through `build_unadapted_base`, which Phase 17 structurally pins against reaching any adapter path |
| T-18-10-03 (Tampering — an overwritten arm record replaces published completions) | mitigated | Clobber refusal called FIRST and cheapest in `run_arm` and `run_corpus`; no override in any spelling, asserted as a committed regex guard over the whole file |
| T-18-10-04 (Elevation of Privilege — a flag runs both arms in one process) | mitigated | One required mutually exclusive group; four dests by hard equality; `--arm` constrained to `ARMS`; no `nargs`, no append action; a repeated `--arm` proved to yield one `str` |
| T-18-10-05 (Denial of Service — a NaN in the NLL path found after 8.2h) | mitigated | The smoke `_prove`s `math.isfinite` on every candidate in R across 8 slots x 3 frames x 2 reductions, and proves the spread-0 control RAN on both declared slots rather than merely not raising |
| T-18-10-SC (Tampering — package installs) | accepted | Zero installs; `pyproject.toml` untouched |

## Issues Encountered

- **Worktree base drift, ninth consecutive plan.** HEAD was `829cd5f`, a strict ancestor of the
  required `ee78ea4` with a clean tree, so `git merge --ff-only` corrected it with 0 commits lost.
- **PERS-06's draw-site guard caught both new drawing paths** — see Deviation 1. It is the only
  cross-phase guard this plan tripped, and it tripped for the right reason.
- **`ruff` F821 on `run_report`**, which is real and is Deviation 4's whole subject; suppressed at
  the one call site with the reason on the line, behind a `_prove` that fires first.
- **Three `ruff` E501s and one reformat**, all in `_USAGE` prose and assertion messages; reflowed
  before their commits. No logic involved.
- **`argparse` allows a repeated `--arm`** — the first RED of `test_no_multi_arm_mode` expected a
  `SystemExit` and got a clean parse. The correct property is that the repeat cannot ACCUMULATE:
  argparse overwrites, so the parsed value is one `str` and one arm runs. The test asserts that
  instead, which is the property D-07 actually needs.

## Deferred Issues

None new. The one item in `deferred-items.md` is 18-04's and is untouched.

## Known Stubs

**One, declared and time-boxed to one wave.** `main`'s `--report` branch calls `run_report()`,
which is not defined in this file yet — see Deviation 4. It is guarded by a `_prove` that fires
before the call with an operator-legible message, so the failure mode is a named refusal rather
than a `NameError`. **18-11 must add `run_report()`**; it is the last driver commit and already
owns `render_report`, the clobber guard and `append_addendum`. No `results/phase18_*` artifact can
exist before then, so nothing downstream is blocked by the gap.

`grep -c "TODO\|FIXME\|placeholder"` returns **1** for the driver and **0** for the test file; the
single hit is 18-06's pre-existing use of "placeholder" at the `ans1` `{v}` template token, the
same one 18-07, 18-08 and 18-09 all reported.

## User Setup Required

None — no external service configuration required. The three modes that load a model
(`--smoke`, `--corpus`, `--arm`) need `checkpoints/convbase_slim.pt` and, for `--arm`,
`checkpoints/persona_adapter.pt`; both loaders raise a named `SystemExit` naming the export script
if either is absent.

## Threat Flags

None. No new network endpoint or auth path. Three new **file-access patterns**, all inside
function bodies and none at import: `run_corpus` writes `CORPUS_PATH`, `run_arm` reads
`CORPUS_PATH` and `CORPUS_SOURCE_FIXTURE` and writes `ARM_RECORD_PATHS[arm]`, and `run_smoke`
writes `SMOKE_REPORT_PATH`. Every write is behind a clobber refusal or is the pre-flight's own
re-runnable report; every read is of a tracked artifact. The import-time callee register is a hard
equality and grew by exactly one entry — `main`, under the `__name__` guard — which
`test_nothing_loads_at_import` pins. Nothing in this plan writes to disk when nothing calls it, so
`results/phase18_*` still does not exist and every commit here remains a legitimate ancestor under
D-04.

## Next Phase Readiness

- **The driver is one commit from complete.** 18-11 adds `render_report`, its clobber guard,
  `append_addendum`, `prereg_commit` — **and `run_report()`**, the mode function this plan's
  dispatch calls. After that commit the ancestry guard arms on the next `results/phase18_*`
  first-add.
- **18-13 can run the smoke as-is.** `--smoke` writes `results/phase18_preflight_report.md` with
  the provenance block, four `draws_per_min` lines, the attractor table against its priors, the
  D-28 NLL coverage line and a projection whose derivation is shown. It aborts loudly on any
  failure and reports no quantity about the taught column. It is deliberately re-runnable — unlike
  an arm record it is a pre-flight measurement, not evidence a rate was scored from.
- **18-14 can generate the corpus as-is.** `--corpus` writes `canonical_json(corpus)` with no
  trailing newline behind a clobber refusal, and prints the entry count and sha256.
- **18-15 can run both arms as-is.** Two fresh processes, `--arm adapter-on` then
  `--arm adapter-off`. Each record carries `arm` at top level and on every draw row, a `config`
  block holding `corpus_sha256`, `forbid_ids_sha256`, `k`, `family_zero_draws`, the device,
  `git_sha`, `pid`, `preflight` and `wall_clock_min`, a flat `draws` list of **976** rows (864 at
  K, 112 at 9) in `DRAW_RECORD_KEYS` shape plus `stopped` / `source_family` /
  `realized_injection`, and an `exposure` list of 8 `measure_exposure` records. All five pairing
  fields 18-15 verifies are present in both records.
- **Carried forward:** 18-06's `f4_reversed` ≡ `f3_bare` identity, 18-07's 144-cell key space,
  18-08's `arm` axis and 18-09's global `seed_index` — all four checked against this plan above,
  all four still applying to whoever reports them.

## Self-Check: PASSED

- `scripts/phase18_extraction.py` — FOUND (3,960 lines; contains `def run_smoke`, `def run_arm`,
  `def build_parser`, `def main`, `def run_corpus`, `def _guarded_span`, `def _rate_lower_bound`,
  `SMOKE_REPORT_PATH`, `DEGENERATION_PRIORS`, `ARM_RECORD_PATHS`, `_USAGE`)
- `tests/test_phase18_prereg.py` — FOUND (1,802 lines, ≥450 required; 26 tests, 3 of them this
  plan's)
- `e37395e`, `98c8185`, `745bc61`, `7f7d8b7` — all FOUND in `git log`
- `git status --short` clean apart from this SUMMARY
- No `STATE.md`, `ROADMAP.md` or `REQUIREMENTS.md` touched — the orchestrator owns them
- No file deleted by any commit; 2 line removals, both the replaced `__main__` block (Deviation 5)
- `ls results/phase18_*` returns nothing — this plan writes no artifact

---
*Phase: 18-black-box-adversarial-extraction-audit*
*Completed: 2026-08-16*
