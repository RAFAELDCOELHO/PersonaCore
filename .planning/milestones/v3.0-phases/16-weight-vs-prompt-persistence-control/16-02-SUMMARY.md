---
phase: 16-weight-vs-prompt-persistence-control
plan: 02
subsystem: instrument
tags: [pytest, ast-guard, bpe, seeding, pairing, structural-guard, shared-instrument]

# Dependency graph
requires:
  - phase: 14 (teach-then-recall)
    provides: "scripts/phase14_recall.py — the shared instrument, including stamp_seed_indices' CR-01 fix (the shape PERS-05 mirrors) and assert_no_value_in_prompt (the shape PERS-06 mirrors)"
  - phase: 16 (plan 01)
    provides: "the committed ordering guard + dependency freeze this plan runs under"
provides:
  - "PERS-05 closed: run_fairness_control draws each question's OWN seed_index, so the control is PAIRED with the scored arms rather than merely comparable"
  - "A `-1` sentinel guard that refuses an unstamped item, so a silently-unpaired comparison cannot run at all"
  - "PERS-06 closed: assert_value_in_prompt is a public, parameterized, two-level guard — the logical twin of assert_no_value_in_prompt"
  - "Both fixes live in the SHARED instrument (D-20), so Phases 17 and 18 inherit them without a second edit"
  - "A measured correction to the plan's prescribed assertion operator, pinned by a test against the real committed fixture"
affects: [phase-16 remaining plans, phase-17, phase-18, every arm and ladder rung that draws through draw_all]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Union-of-detectors asserted from both polarities: NOT(a) AND NOT(b) for absence, a OR b for presence — the same predicate, never two different strictnesses"
    - "Cost-asymmetry decides the operator: a detector whose false positives are free in one direction has fatal false negatives in the other"
    - "Extraction is a MOVE, never a copy — the weaker inline assertion is deleted in the same commit that names its replacement"
    - "A synthetic-double test pins the logic; a real-fixture test pins the premise the logic was derived from"

key-files:
  created: []
  modified:
    - "scripts/phase14_recall.py — run_fairness_control (:1195) seed fix + sentinel guard + D-19 docstring; assert_value_in_prompt added at :424, beside its twin at :398"
    - "tests/test_phase14_scoring.py — 8 new tests (3 for PERS-05, 5 for PERS-06)"

key-decisions:
  - "The in-prompt guard's verdict is the UNION of its two detectors, not their intersection — the plan prescribed an intersection, which measurement falsified on 54 of 216 core fairness prompts"
  - "The seed sentinel guard is placed as the FIRST statement in the loop, before the prompt is built, so an unstamped item aborts before any work is done on it"
  - "seed_index is recorded in the per-question `asked` dict, matching run_scored_recall — a pairing claim absent from the record is not auditable afterwards"
  - "results/phase14_recall_report.md deliberately NOT amended (D-19/T-16-07): mitigation for the changed number is disclosure, not prevention"
  - "The behavioural test drives run_fairness_control against the REAL tokenizer and the REAL build_recall_prompt, stubbing only the two things that need a loaded model, so the in-prompt guard is genuinely exercised rather than stubbed past"

patterns-established:
  - "Deliberate-RED mutations applied and reverted inside a `finally`, byte-identity proven against the pre-mutation bytes (15-03 / 16-01 precedent)"
  - "A plan instruction contradicted by measurement is implemented per the measurement and the contradiction is reported, never silently resolved either way"

requirements-completed: [PERS-05, PERS-06]

# Metrics
duration: 25min
completed: 2026-08-13
---

# Phase 16 Plan 02: Shared-instrument surgery (PERS-05 / PERS-06) Summary

**The fairness control now draws each question's own seeded stream instead of its position in the list it was handed, and the in-prompt assertion is a named two-level guard beside its absence twin — both in `scripts/phase14_recall.py`, so Phases 17 and 18 inherit them (D-20).**

## Performance

- **Duration:** ~25 min wall clock (13:23 → 13:48 -03:00)
- **Tasks:** 2
- **Files modified:** 2
- **Tests added:** 8 (416 → 424 passed)

## Task Commits

1. **Task 1 — PERS-05, seed from `item.seed_index`** — `cf6088e` (fix)
2. **Task 2 — PERS-06, extract `assert_value_in_prompt`** — `9f42f46` (feat)

## What landed

### Task 1 — PERS-05 / D-17 / T-16-06

`run_fairness_control` drew with `enumerate(questions)` — the question's index in the concatenated
`core_taught + core_held_out` list it is handed — while the scored arms draw with the index
`stamp_seed_indices` stamps **per ARM**, each arm restarting at 0. Every question past the first arm
therefore drew a different `question_seed(index) + s` in the control than it drew when scored. The
arms were comparable and not paired, and PERS-02 claims pairing by `item.seed_index` explicitly.

- `for item in questions:` replaces the `enumerate`; `item.seed_index` reaches `draw_all`.
- A `-1` sentinel `_prove` guard mirroring `run_scored_recall:795-800`, placed as the **first**
  statement in the loop so an unstamped item aborts before a prompt is even built. The message names
  PERS-05 and `stamp_seed_indices`, and both strings are pinned by a test.
- `"seed_index": item.seed_index` recorded in the per-question `asked` dict, matching what
  `run_scored_recall` already records at `:822`.
- `n_answerable` is untouched and still `sum(1 for entry in asked if entry["k"] > 0)` — the
  STAT-01-legal question-unit numerator every Phase 16 ladder cell compares against.
- The docstring gained two paragraphs naming the defect and D-19 (see the disclosure section below).

### Task 2 — PERS-06 / D-18 / D-20 / T-16-05 / T-16-08

`assert_value_in_prompt(tok, prompt_ids, values)` now sits at `:424`, immediately after
`assert_no_value_in_prompt` at `:398`, so the twins read as a pair. `values` is a parameter with no
default (LAZY-IMPORT RULE); it takes already-built `prompt_ids` rather than a question string,
because its callers build prompts with a persona span and rebuilding from a bare question would
check a different prompt than the one actually drawn from.

The inline `_prove(contains_value(...))` block was **deleted**, not left beside the named function —
T-16-08 exactly: two assertions of differing strictness is how the stricter one stops being the one
that runs. An AST test pins that `run_fairness_control` holds zero `contains_value` calls in an
assertion position while still calling it for the per-completion `hits` flags.

## Deviation — the assertion operator, corrected by measurement

**This is the one substantive deviation in the plan, and it is a correction to a plan instruction
rather than to the code.** It is reported in full because this phase's product is a
pre-registration.

**What the plan prescribed.** Task 2's `<action>`: "for each value in `values`, `_prove` BOTH
levels" — an intersection. Its test spec: "feed a synthetic tokenizer double where the string check
passes but the id run does not (and the converse), assert `SystemExit` in both directions."

**What was measured, before any code was written.** Against the committed core fixture, driving the
real `build_recall_prompt` with the real tokenizer and the real first-person statements:

```
items: 216
string-level failures: 0
id-run-level failures: 54
Counter({'cand_sister_orsala': 27, 'cand_town_brindlemoor': 27})
```

**The mechanism, isolated.** Byte-level BPE is context-dependent at merge boundaries, so a value
preceded by a space encodes differently from the same value encoded standalone:

```
cand_sister_orsala     statement 'my sister is named orsala.'
  encode(value)      [111, 114, 115, 97, 108, 97]   -> 'o' 'r' 's' 'a' 'l' 'a'
  encode(' '+value)  [398, 114, 115, 97, 108, 97]   -> " o" merged into ONE id
  contiguous(standalone) False    contiguous(with space) True    in decoded string True

cand_town_brindlemoor  statement 'i live in brindlemoor.'
  encode(value)      [98, 114, 105, 266, 295, 109, 396, 114]
  encode(' '+value)  [432, 266, 295, 109, 396, 114]  -> " bri" merged into ONE id
  contiguous(standalone) False    contiguous(with space) True    in decoded string True

cand_dog_zorp          " z" does NOT merge -> contiguous True. Six of eight facts pass by luck.
```

**Why an intersection is wrong, not merely inconvenient.** Under `AND`, the fairness control would
`SystemExit` on 54 of 216 core questions — a quarter of the arm — on values that are unambiguously
in the model's view. The repository already contains the argument that settles this, in
`contains_value`'s committed docstring: an id-subsequence check is *"at best a diagnostic; it is
used that way in `assert_no_value_in_prompt`, where a false positive costs nothing and a false
negative would be a leak."* Inverting the polarity inverts the cost asymmetry — here a false
negative of the id detector aborts a legitimate run.

**What was implemented.** The verdict is the **UNION** of the two detectors. This is the true De
Morgan twin: `assert_no_value_in_prompt` proves `NOT(string) AND NOT(ids)` ≡ `NOT(string OR ids)`,
so its twin proves `string OR ids`. The same predicate, asserted from both sides — which is what
"logical twin" means. It is also **strictly stronger than what it replaces** (the deleted inline
check was string-only), so T-16-08's strictness ratchet holds.

**The plan is not uniformly against this.** Its own prescribed docstring text (b) argues for the
union: *"a value split across a BPE merge boundary is present in the string but not as a contiguous
id run, **which is still 'in view' for the model**."* The prose and the action contradicted each
other; the measurement settled which one was right. Every other constraint the plan attached to this
function is satisfied verbatim — public, `values` last and a parameter with no default, both levels
computed, `_is_contiguous_subsequence` called (AST-pinned), `_prove`/`SystemExit` register.

**What guards it.** `test_assert_value_in_prompt_accepts_the_measured_bpe_boundary_case` runs the
real 216-prompt construction through the guard and asserts `split_level > 0`, so the test cannot go
green having stopped exercising the merge boundary. A future tightening to `AND` — which looks
stricter and is simply wrong — turns that test red with the real offending value named.

**If a human wants the intersection anyway,** the change is one operator at
`scripts/phase14_recall.py:464` plus the two real-data assertions; the consequence is that the
fairness control aborts and the Phase 16 ladder's top rung cannot run.

## D-19 / T-16-07 — the changed number, disclosed not prevented

**`results/phase14_recall_report.md` was NOT amended, and the committed Phase 14 number stays
exactly as published.** `git diff --stat results/` is empty across both commits — verified after
each task and again at close.

The seed fix changes which streams the control draws, so the count that code produced in Phase 14
does not reproduce bit-for-bit afterwards. That is the definition of the defect, not a regression:
Phase 14 never compared this arm against anything, so pairing was not in play there. The mitigation
is **disclosure** — `run_fairness_control`'s docstring now states plainly that the number moves by
design, that the committed report is deliberately not amended, and that Phase 16 re-runs the control
post-fix and reports the delta separately (D-13) as a measurement of this fix's impact rather than a
silent assertion that it did not matter. Nothing was preserved behind a flag and nothing was quietly
overwritten.

## Observed RED #1 — Task 1, the seed fix reverted

`for item in questions:` → `for index, item in enumerate(questions):` and
`draw_all(..., item.seed_index)` → `draw_all(..., index)`, i.e. the pre-fix code exactly. Verbatim:

```
.FF.                                                                     [100%]
=================================== FAILURES ===================================
_______ test_fairness_control_seeds_from_the_item_not_the_loop_position ________
        items = _fairness_items((7, 3, 11))
        seen, result = _run_fairness(monkeypatch, items)

>       assert seen == [7, 3, 11]
E       assert [0, 1, 2] == [7, 3, 11]
E
E         At index 0 diff: 0 != 7
tests/test_phase14_scoring.py:833: AssertionError
____________ test_fairness_control_has_no_enumerate_over_questions _____________
>       assert enumerates == []
E       assert [<ast.Call ob... 0x10ba85b10>] == []
E         Left contains one more item: <ast.Call object at 0x10ba85b10>
tests/test_phase14_scoring.py:859: AssertionError
=========================== short test summary info ============================
FAILED tests/test_phase14_scoring.py::test_fairness_control_seeds_from_the_item_not_the_loop_position
FAILED tests/test_phase14_scoring.py::test_fairness_control_has_no_enumerate_over_questions
2 failed, 2 passed, 32 deselected in 0.57s
```

`assert [0, 1, 2] == [7, 3, 11]` is the defect's literal signature: the seed handed to `draw_all` is
the loop position, not the question's own index. Both PERS-05 tests go red, which is the honest
result of reverting the fix — the AST guard is not independent of the behavioural one, it is the
structural half of the same claim. **Revert proven byte-identical** against the pre-mutation bytes
inside a `finally` block.

## Observed RED #2 — Task 2, each level deleted in turn

Both single-level mutations were run. The plan asks for the string-only case; the id-only case was
run too because it is the one that proves the real-fixture guard bites.

**String level only (`in_ids` dropped)** — the id-only synthetic double wrongly aborts:

```
..F.                                                                     [100%]
        # The id run sees it, the decoded string does not. Deleting the ID level wrongly aborts here.
        ids_only = _SplitTokenizer("nothing legible here", {_FAKE_VALUE: [2, 3, 4]})
>       pr.assert_value_in_prompt(ids_only, ids, [_FAKE_VALUE])
tests/test_phase14_scoring.py:976:
scripts/phase14_recall.py:464: in assert_value_in_prompt
    _prove(
E           SystemExit: [phase14_recall] PROOF FAILED: value 'wibblex' is in the prompt neither as a
            normalized string nor as a contiguous id run — the prompt does not carry the fact it
            exists to put in view, so anything drawn from it measures nothing while still reporting a rate
=========================== short test summary info ============================
FAILED tests/test_phase14_scoring.py::test_assert_value_in_prompt_checks_both_levels
1 failed, 3 passed, 37 deselected in 0.60s
```

**Id level only (`in_string` dropped)** — the synthetic double AND the real fixture both abort:

```
    def test_assert_value_in_prompt_accepts_the_measured_bpe_boundary_case():
            prompt_ids = build_recall_prompt(tok, item.question, persona=[statements[item.fact.id]])
>           pr.assert_value_in_prompt(tok, prompt_ids, [item.fact.value])  # SystemExit on a miss
tests/test_phase14_scoring.py:1015:
scripts/phase14_recall.py:464: in assert_value_in_prompt
    _prove(
E           SystemExit: [phase14_recall] PROOF FAILED: value 'orsala' is in the prompt neither as a
            normalized string nor as a contiguous id run — the prompt does not carry the fact it
            exists to put in view, so anything drawn from it measures nothing while still reporting a rate
=========================== short test summary info ============================
FAILED tests/test_phase14_scoring.py::test_assert_value_in_prompt_checks_both_levels
FAILED tests/test_phase14_scoring.py::test_assert_value_in_prompt_accepts_the_measured_bpe_boundary_case
2 failed, 2 passed, 37 deselected in 0.58s
```

The second failure is the deviation's whole argument rendered as a test failure: a real committed
value, in a real prompt, in the model's view, reported as absent by the id detector alone.
**Both reverts proven byte-identical** against the pre-mutation bytes inside a `finally` block.

## Verification

```
.venv/bin/python -m pytest tests/test_phase14_scoring.py -q
    36 passed                                      (Task 1 gate)
.venv/bin/python -m pytest tests/test_phase14_scoring.py tests/test_phase14_factset.py -q
    49 passed                                      (Task 2 gate — test_no_fact_strings_at_import
                                                    still green with the new docstrings)
.venv/bin/python -m pytest tests/test_phase14_scoring.py tests/test_phase14_factset.py \
                          tests/test_phase16_fixture_regen.py -q
    54 passed

.venv/bin/python -m pytest -q
    424 passed, 1 skipped, 83 warnings in 119.56s (0:01:59)

.venv/bin/python -m ruff check .           All checks passed!
.venv/bin/python -m ruff format --check .  143 files already formatted

git diff --stat results/                   (empty — byte-unchanged)
```

**Baseline was `416 passed, 1 skipped` (captured by the orchestrator immediately before dispatch).
Delta `+8` = Task 1's 3 tests + Task 2's 5 tests. Zero failed, zero errors.** `make test` /
`make lint` were substituted with the venv-explicit forms per the recorded environment fact on this
machine (bare `pytest` resolves to a pyenv 3.12 shim and produces ~63 spurious
`ModuleNotFoundError: No module named 'torch'` collection errors).

## Success criteria

| Criterion | Result |
|---|---|
| `run_fairness_control` contains no `enumerate` and draws from `item.seed_index` | AST-verified, exit 0 |
| `assert_value_in_prompt` exists, public, `values` a parameter, both levels checked | `['tok', 'prompt_ids', 'values']`; `_is_contiguous_subsequence` + `normalize` + `_prove` AST-verified |
| `results/phase14_recall_report.md` and `results/phase16_recall_sample.json` byte-unchanged | `git diff --stat results/` empty |
| Full suite green | 424 passed, 1 skipped |
| Both deliberate-RED observations recorded | above, verbatim |

## Tests added

| Test | Pins |
|---|---|
| `test_fairness_control_seeds_from_the_item_not_the_loop_position` | seeds `(7, 3, 11)` reach `draw_all` in that order; `seed_index` in the record; `n_answerable` keeps its question-unit shape (3 answerable / 6 draws) |
| `test_fairness_control_has_no_enumerate_over_questions` | no `enumerate` call survives anywhere in the function (AST) |
| `test_fairness_control_refuses_an_unstamped_item` | `seed_index == -1` aborts; the message names PERS-05 and `stamp_seed_indices` |
| `test_assert_value_in_prompt_is_the_named_twin` | public, `['tok', 'prompt_ids', 'values']`, no `question` parameter |
| `test_assert_value_in_prompt_holds_no_module_level_values` | no defaults; no module-level constant passed at any call site (AST) |
| `test_assert_value_in_prompt_checks_both_levels` | union semantics in all three directions + every entry of `values` checked |
| `test_assert_value_in_prompt_accepts_the_measured_bpe_boundary_case` | the real 216 prompts all pass, and `split_level > 0` so the premise cannot silently vanish |
| `test_fairness_control_calls_the_named_twin` | the control calls the twin and holds zero `contains_value` in an assertion position (AST) |

## Decisions Made

- **`test_assert_value_in_prompt_accepts_the_measured_bpe_boundary_case` is a fifth test the plan
  did not name.** It is the only guard that pins the deviation against a future "tightening", and it
  costs 0.1s because it builds prompts without drawing. Adding it is Rule 2 (missing critical
  functionality) applied to the deviation itself.
- **The behavioural test uses the real tokenizer and the real `build_recall_prompt`,** stubbing only
  `draw_all` and `adapter_disabled`. The plan permitted stubbing `contains_value` and
  `score_question` too; not stubbing them means the in-prompt guard is genuinely exercised by the
  behavioural test rather than bypassed, so the same test kept working unchanged across both tasks.
- **A synthetic value (`wibblex`) is used throughout the new tests,** never a locked one. These tests
  are about the instrument, so binding them to fact material would make them re-fail whenever the
  fact set is re-rolled. The one test that must use real material (the BPE-boundary case) imports it
  lazily inside the function, the idiom the file already uses.
- **The `-1` guard is the first statement in the loop,** before `statements[item.fact.id]` and before
  the prompt is built, so an unstamped item cannot do partial work before aborting.

## Deviations from Plan

### 1. [Rule 1 — Bug] The in-prompt guard's verdict is a union, not an intersection

- **Found during:** Task 2, before any code was written (the measurement was taken first).
- **Issue:** the plan's prescribed `_prove` of BOTH levels would abort `run_fairness_control` on 54
  of 216 core questions.
- **Fix:** `_prove(in_string or in_ids, ...)`. Both levels still computed, both still pinned.
- **Files modified:** `scripts/phase14_recall.py:461-467`, `tests/test_phase14_scoring.py`
- **Commit:** `9f42f46`
- Full argument, measurement and mechanism above. This is the only place the plan text was not
  followed literally, and the plan's own prescribed docstring text argues for what was implemented.

### 2. [Environment] `make test` / `make lint` substituted with venv-explicit invocations

- **Plan text:** `<verification>` specifies `make test`.
- **What was run:** `.venv/bin/python -m pytest -q`, `.venv/bin/python -m ruff check .`.
- **Why:** recorded fact about this machine — bare `pytest` resolves to a pyenv 3.12 shim and yields
  ~63 `ModuleNotFoundError: No module named 'torch'` collection errors across files this plan never
  touched. Same substitution as 16-01. The gate actually run is the full suite the `make` target
  wraps.

### 3. [Tooling] Deliberate-RED reverts performed by byte-restore, not `git checkout --`

- Mutations were applied and restored inside `try/finally` blocks, with byte-identity asserted
  against the pre-mutation content (`RESTORED bytes-identical: True` for all three). `git diff
  --exit-code` against HEAD is not the right check mid-task, because the file legitimately carries
  the task's own uncommitted fix at that point; the pre-mutation bytes are the correct baseline. The
  `finally` scoping also makes the mutation window crash-safe.

### 4. [Sequencing] Task 1 briefly held a forward reference to Task 2's function

- While editing, `assert_value_in_prompt(...)` was written into `run_fairness_control` before the
  function existed. Caught and reverted to the inline `_prove(contains_value(...))` form **before**
  the Task 1 commit, so `cf6088e` is green standing alone and the extraction is entirely Task 2's
  diff. Noted because atomic-commit integrity is the property at stake, not the typo.

---

**Total deviations:** 4 (1 code, 1 environment, 1 tooling, 1 sequencing). Deviation 1 is the only one
that changes an artifact relative to the plan text; it is measured, reported, and test-pinned.

## Issues Encountered

- **`state.update-progress` remains a no-op on this STATE.md** (16-01 recorded the same): this repo
  keeps progress in a frontmatter block rather than a body "Progress" field.
- The dangling identifier D-10 declares non-existent stayed out of both touched files, both commit
  messages, and this summary — verified by repo-wide grep, whose only hits are planning artifacts
  that predate this plan and exist to record its non-existence.
- No package was installed and none was needed, so the STAT-04 freeze from 16-01 was never
  approached.

## Next Phase Readiness

- **The shared instrument is now safe to measure through.** Both defects are closed in
  `scripts/phase14_recall.py`, so Phases 17 and 18 inherit both fixes with no second edit (D-20).
- **`assert_value_in_prompt` is the guard every Phase 16 ladder rung should call.** It takes
  `prompt_ids`, so a rung that builds its prompt with a synthetic span in the question text can call
  it without rebuilding — which was the reason for that signature choice.
- **The post-fix fairness re-run (D-13) is now unblocked and will produce a different number than
  the committed `1/1944`.** That is expected; the delta is the reported measurement of this fix's
  impact. Whoever runs it should also report it in the STAT-01-legal question unit — the
  `n_answerable` numerator, untouched by this plan, is already computed for exactly that.
- **One thing to watch:** the union-vs-intersection decision is the kind of thing a reviewer may want
  to overturn. It is deliberately concentrated in one operator with a test that names the real
  offending value, so overturning it is a one-line change with an immediately visible consequence.

## Self-Check: PASSED

Both modified files exist on disk with the claimed content: `scripts/phase14_recall.py` (`def
assert_value_in_prompt` at `:424`, `def run_fairness_control` at `:1195`) and
`tests/test_phase14_scoring.py` (all 8 new test functions located by grep). Both task commits resolve
in `git log`: `cf6088e`, `9f42f46`. All three deliberate-RED mutations restored byte-identical.
`git diff --stat results/` empty. Working tree carries only the two pre-existing unrelated items this
plan did not touch: modified `.gitignore`, untracked `AGENTS.md`.

---
*Phase: 16-weight-vs-prompt-persistence-control*
*Completed: 2026-08-13*
