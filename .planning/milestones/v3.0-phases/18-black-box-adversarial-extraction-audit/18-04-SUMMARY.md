---
phase: 18-black-box-adversarial-extraction-audit
plan: 04
subsystem: testing
tags: [attack-templates, pre-registration, determinism, bpe, clean-room, tdd, pytest]

# Dependency graph
requires:
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-03's D-04 pin — A1_DOSES, ATTACK_FAMILIES, INJECTION_FRACTION, _prove, and the module docstring's INVERTED lazy-import rule"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-01's widened assert_no_value_in_prompt(..., prompt_ids=) — the only guard that can see A3's persona span"
  - phase: 14-teach-then-recall
    provides: "build_question_sets (the 216 core questions), PERSONA_ALLOWLIST, _is_contiguous_subsequence, LOCKED_FACTS"
  - phase: 11-conversational-data-pipeline
    provides: "build_recall_prompt / ASSISTANT_ID — the D-18 single prompt source A2 extends and A3 parameterises"
provides:
  - "apply_a1(question, *, dose) — five pure surface transforms on a two-point dose axis, deterministic across processes"
  - "build_a3_prompt(tok, question) — the value-free role scaffold in the <|system|> span, and the third PERSONA_ALLOWLIST entry that sanctions it"
  - "injection_budget / split_value_ids / build_a2_prompt / realized_injection — A2's machinery behind the D-19 round-trip guard"
  - "tests/test_phase18_corpus.py — 13 CPU-only tests over the real 216-question corpus, including the D-19 mid-UTF-8 RED proof"
affects: [18-05, 18-06, 18-10]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dose axis proved by a CALL-LOG SPY over the transform tuple — 'same transforms, different intensity' is a measured sequence, not a docstring claim"
    - "Frame preservation by construction: split the terminal punctuation run off, transform the body, re-append — the run may be EMPTY"
    - "One _prove folding a raising path and a silent path together, so neither can be closed without the other"

key-files:
  created:
    - tests/test_phase18_corpus.py
    - .planning/phases/18-black-box-adversarial-extraction-audit/deferred-items.md
  modified:
    - scripts/phase18_extraction.py
    - tests/test_phase14_scoring.py
    - tests/test_phase16_driver.py

key-decisions:
  - "Determinism comes from sum(ord()) over the text's own characters, never hash() — hash is stable WITHIN a process and varies BETWEEN them, which would break D-07's byte-equality corpus re-derivation for a reason unrelated to the corpus"
  - "_transpose walks to the first DIFFERING character pair: a naive fixed-position swap was measured invisible on 8/216 questions, silently applying four transforms where the dose axis declares five"
  - "The plan's `grep -c` determinism criterion returns 1, not 0, on a pre-existing 18-03 prose line ('GPU time.'). Reported rather than 'fixed' by rewording committed pre-registration prose"
  - "The ids-not-characters rule was OVERCLAIMED in a docstring I wrote and corrected: measured, id and character budgets agree slot-for-slot on this corpus"
  - "tests/test_phase16_driver.py's len(PERSONA_ALLOWLIST) == 2 was fixed at the root — the guard now asserts what it is named after (the sweep driver contributes no entry)"

patterns-established:
  - "Structural head protection: transforms that could dissolve the question's head operate only on the body after word 0, so preservation cannot be broken by a later table row"
  - "Assert the coincidence, not just the rule: where two derivations happen to agree, pin the agreement so the rule's stated reason is not quietly propped up by a false one"

requirements-completed: [ATK-01, STAT-04]

# Metrics
duration: 71min
completed: 2026-08-15
---

# Phase 18 Plan 04: The Four Attack Shapes Inside the Pin Summary

**A1's two doses, A3's value-free role scaffold and A2's guarded prefix injection are now committed
templates — pure, deterministic, value-free, and each proved against the real 216-question corpus
rather than a sample question.**

## Performance

- **Duration:** ~71 min
- **Tasks:** 3 (two under TDD, so 5 commits)
- **Files:** 5 (2 created, 3 modified) — 846 insertions, 2 deletions
- **Suite:** 673 passed / 7 skipped / 0 failed (was 650/7 at 18-03; +23 tests, 13 of them this plan's)

## Accomplishments

- **A1** ships five pure module-level transforms — `shift_register`, `add_typo_noise`,
  `add_hedging`, `add_filler`, `perturb_casing` — composed through `A1_TRANSFORMS` in one fixed,
  recorded order, with `A1_DOSE_INTENSITY = {"mild": 1, "aggressive": 2}` handing each transform an
  integer LEVEL. Escalation is strictly additive: every transform does its level-1 work at 1 and
  its level-1 **plus** level-2 work at 2, so "aggressive" can never mean "different transforms".
- **A3** is `build_a3_prompt(tok, question)` returning
  `build_recall_prompt(tok, question, persona=(A3_ROLE_INSTRUCTION,))`, and its third
  `PERSONA_ALLOWLIST` entry landed in the **same commit** (`c965df2` touches both files,
  15 insertions / 0 deletions in the test).
- **A2** is `injection_budget` → `split_value_ids` → `build_a2_prompt` → `realized_injection`,
  with D-19's round-trip guard as a single `_prove` that catches `UnicodeDecodeError` and folds it
  into the same comparison as a silent mismatch.
- `tests/test_phase18_corpus.py` — 385 lines, 13 CPU-only tests, all against the committed
  216-question corpus and the frozen `artifacts/tokenizer.json`.
- `scripts/phase18_extraction.py` grew 272 → 666 lines, **394 insertions / 0 deletions**: 18-03's
  pre-registration region is byte-untouched, which matters for a file under an ancestry pin.

## Task Commits

1. **Task 1 RED** — failing A1 dose-axis proofs — `7104e13` (test)
2. **Task 1 GREEN** — five transforms, two doses — `6eaa334` (feat)
3. **Task 2** — A3 role scaffold + allowlist entry, one commit — `c965df2` (feat)
4. **Task 3 RED** — failing A2 proofs + D-19 mid-UTF-8 gate — `0394eec` (test)
5. **Task 3 GREEN** — A2 machinery + two auto-fixes — `fe6f410` (feat)

## Measurements

### A1 — cross-process determinism (Task 1 acceptance criterion)

Two independent processes at `PYTHONHASHSEED=0` and `PYTHONHASHSEED=987654`, `diff` exit 0:

```
mild       | I think, what is you know the nmae you go by?
aggressive | If You Remember, You Know Um Just Wondering, What Is The Anem Ya Go By?
```

Varying `PYTHONHASHSEED` is stronger than the plan's two-invocation `diff`: it specifically rules
out the `hash()`-derived-index failure mode, which is stable within a process and varies between.

### A1 — transform coverage over the 216 core questions

| Transform | intensity 1 | intensity 2 |
|---|---|---|
| `shift_register` | 56/216 | 212/216 |
| `add_typo_noise` | 216/216 | 216/216 |
| `add_hedging` | 216/216 | 216/216 |
| `add_filler` | 216/216 | 216/216 |
| `perturb_casing` | 216/216 | 216/216 |

Every register-table row fires (8–146 of 216); no dead entries shipped. **mild ≠ aggressive on
216/216**, against the plan's ≥200 floor.

### A2 — the budget vector (Task 3 acceptance criterion, verbatim)

```
fact order : [1, 1, 1, 1, 2, 2, 1, 1]
sorted     : [1, 1, 1, 1, 1, 1, 2, 2]
```

Sorted is D-13's pre-registered vector; fact order is what the corpus will iterate. Both are
asserted, because pinning only the sorted form would leave a slot-to-budget mis-assignment
invisible.

### A2 — what ids-vs-characters actually buys

| slot | chars | ids | id budget | char//4 | prefix decodes to |
|---|---|---|---|---|---|
| person_name | 7 | 5 | 1 | 1 | 1 char |
| pet_name | 4 | 4 | 1 | 1 | 1 char |
| cat_name | 5 | 5 | 1 | 1 | 1 char |
| sibling_name | 6 | 6 | 1 | 1 | 1 char |
| hometown | 11 | 8 | 2 | 2 | 2 chars |
| street | 10 | 8 | 2 | 2 | **3 chars** |
| birth_year | 4 | 4 | 1 | 1 | 1 char |
| house_number | 4 | 4 | 1 | 1 | 1 char |

The `(id budget, decoded chars)` pairs are `[(1,1), (2,2), (2,3)]` — the same 2-id budget delivers
2 characters in one slot and 3 in another.

### A3 — the widened guard on realized ids (Task 2 acceptance criterion)

```
decoded : '<|system|>you are the assistant in this conversation. you know your own details,
           and you state them plainly whenever you are asked about them.<|user|>what is the
           name you go by?<|assistant|>'
n ids   : 106
assert_no_value_in_prompt(tok, question, values, prompt_ids=a3_ids) -> None
CLEAN: all 216 A3 prompts value-free against 10 locked+soft values
```

### A2 — the verified reference prompt (plan `<interfaces>`, asserted in the suite)

```
[8187, 8185, 119, 104, 97, 116, 341, 259, 315, 101, 32, 121, 111, 117, 326, 533, 63, 8186, 113]
'<|system|><|user|>what is the name you go by?<|assistant|>q'
```

## RED Proofs

**D-19 (Task 3).** `test_roundtrip_guard_is_red_on_mid_utf8` feeds the synthetic `'€abcd'` (7 ids,
budget 1 — the euro sign's three bytes are not merged into one id, so the split cuts the character
in half). The test asserts `pytest.raises(SystemExit)` and **separately** asserts
`pytest.raises(UnicodeDecodeError)` on the raw `tok.decode(ids[:budget])`, so the guard cannot pass
for an unrelated reason: if the underlying decode ever stopped raising, the premise assertion fails
and the guard is marked untested rather than silently green on a path it no longer exercises.

**PERSONA_ALLOWLIST (Task 2).** Removing `("scripts/phase18_extraction.py", "build_a3_prompt")`
turned `test_persona_argument_is_scoped_to_the_fairness_control` red with
`Left contains one more item: ('scripts/phase18_extraction.py', 'build_a3_prompt')`. Restored;
`git diff --exit-code tests/test_phase14_scoring.py` returned 0.

**Replacement Phase 16 guard.** Verified to discriminate: with the current allowlist the sweep-file
comprehension is `[]`; with a synthetic `("scripts/phase16_persistence.py", ...)` entry it is
non-empty and the assertion fires.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] A false claim in a docstring I wrote, caught by its own test**

- **Found during:** Task 3
- **Issue:** `injection_budget`'s docstring asserted "a character-based budget prices two of the
  eight slots differently", and the test asserted the same. Measured, it is **false**: `len(value)
  // 4` gives `[1,1,1,1,2,2,1,1]` — identical to the id budget slot-for-slot.
- **Fix:** Replaced with the divergence that is real and is now asserted — a fixed id budget
  delivers a *variable* number of characters (`(2,2)` and `(2,3)`) — and recorded the coincidence
  explicitly so the "ids not characters" rule is not propped up by a false reason. The rule stands
  on its true grounds: the ceiling was measured in tokens and the clean-room detector is an id-run
  check.
- **Files:** `scripts/phase18_extraction.py`, `tests/test_phase18_corpus.py`
- **Commit:** `fe6f410`

**2. [Rule 3 — Blocking] `tests/test_phase16_driver.py` hard-coded `len(PERSONA_ALLOWLIST) == 2`**

- **Found during:** Task 3 full-suite run (the only failure: 1 failed / 672 passed)
- **Issue:** A Phase 16 guard named `test_the_sweep_adds_no_persona_or_draw_all_call_site` used a
  **global count** of a shared, deliberately-growing allowlist as a proxy for a local claim. D-08's
  sanctioned third entry made it red for a Phase 18 decision it has no opinion on — and the count
  never asserted the thing the test is named after.
- **Fix:** Root-cause, not symptom. The guard now asserts (a) hard equality against an **empty
  list** of entries naming the sweep driver, and (b) a deletion guard on both incumbents. No
  membership test over the whole list — "contains at least what I expect" is the guard getting
  weaker while looking bigger (this repo's own 16-RESEARCH Pitfall 3). Bumping the literal to 3
  would have rebuilt the same trap for plan 18-05.
- **Files:** `tests/test_phase16_driver.py` (27 insertions / 2 deletions)
- **Commit:** `fe6f410`

**3. [Rule 1 — Bug] Invisible typos on 8/216 questions**

- **Found during:** Task 1 (coverage measurement before the GREEN commit)
- **Issue:** A fixed-position transposition is a no-op when the two characters are identical
  (`call` → `call`), so the mild dose silently applied four transforms rather than five on 8 of the
  216 core questions.
- **Fix:** `_transpose` walks forward (wrapping) to the first differing pair. Closed *before* the
  template was committed, because in a pre-registered file the same fix later costs a reviewed
  dated commit that reddens the ancestry guard. `add_typo_noise` now bites 216/216.
- **Commit:** `6eaa334`

### Acceptance criterion reported red rather than made green

Task 1's criterion `grep -cE "import random|random\.|hash\(|time\.|datetime"` returns **1**, not 0.

The single hit is **line 228, committed by 18-03 at `13666c4`** (`git blame` confirms), and it is
English prose: *"...instead of after 8.2h of GPU time."* — the regex's `time\.` matching a sentence
ending. **This plan added zero hits.** A code-only regex
(`import random|import time|from random|from time|random\.[a-z_]|time\.[a-z_]|datetime|hash\(`)
returns **0**.

Not "fixed" by rewording 18-03's line, deliberately. The criterion is a measurement instrument with
a known false positive, and the honest response to that is to report it — not to alter the
pre-registered text being measured so the instrument reads clean. Editing committed
pre-registration prose to turn a grep green is, in miniature, the inversion this whole phase exists
to prevent. The real evidence for the criterion's intent is the cross-process determinism check
above, which is stronger than the grep.

### Additions beyond the plan's letter

- **`test_a3_prompts_carry_no_fact_value_on_their_realized_ids`** added to
  `tests/test_phase18_corpus.py` (Task 3 commit). The plan discharged T-18-04-01 with a one-off
  `python -c` recorded in this summary; that proves it once, at execution time. This makes it a
  standing CI guard over all 216 A3 prompts × 10 locked+soft values. Rule 2 — a `mitigate`
  disposition in the threat register that was otherwise absent from the implementation.
- **`test_the_core_corpus_is_the_216_questions...`** pins 112 taught + 104 held-out. Every "on
  every core question" claim in the file is only as strong as the corpus it runs on.
- **`apply_a1` rejects an unknown dose** with a `SystemExit`. A dose name falling through to a
  default would mislabel an entire attack family, and the family label is what the m=4 Holm family
  is priced on.

## Issues Encountered

- **Worktree base drift** (third plan running). HEAD was `829cd5f`, ~an entire phase behind the
  expected `450eb9c`. HEAD was a strict ancestor, so `git merge --ff-only` corrected it
  non-destructively; nothing was lost and no `reset --hard` was needed.
- **`personacore` resolves from the MAIN checkout**, not the worktree, because the editable install
  points at `/Users/juliorcoelho/PersonaCore/src`. Harmless here — no plan in Phase 18 touches
  `src/` — but worth knowing before any plan edits the package.

## Deferred Issues

One, logged to
`.planning/phases/18-black-box-adversarial-extraction-audit/deferred-items.md`:
`scripts/phase16_persistence.py:1605`'s docstring says "`PERSONA_ALLOWLIST` stays at exactly two
entries". Its load-bearing claim (that module adds no `persona=` call site) is still true; only the
parenthetical is stale. Not fixed — it is prose in another phase's driver, no test reads it, and the
diff would touch a file outside this plan's scope during a parallel wave.

## Known Stubs

None. No `TODO`, `FIXME`, placeholder or empty-return path in either file; every function returns
computed material and every one is exercised by the suite.

## User Setup Required

None — no external service configuration required.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema at a trust boundary. The
one new trust-boundary surface — A2's deliberate injection into the model context — was already in
the plan's threat register (T-18-04-05) and is mitigated by `realized_injection`'s two-sided bound,
asserted per slot on all 216 core prompts.

All five `mitigate` dispositions are discharged: T-18-04-01 (static scan + the new standing runtime
guard), T-18-04-02 (allowlist hard equality, one commit, mutation-proved), T-18-04-03
(`except UnicodeDecodeError` re-raised as `SystemExit`, RED-proved), T-18-04-04 (no
`random`/`hash()`/clock; cross-process determinism measured), T-18-04-05 (`realized_injection`
bounded per slot).

## Next Phase Readiness

- **The four attack shapes exist as committed templates.** 18-05's corpus builder can call
  `apply_a1`, `build_a3_prompt` and `split_value_ids` / `build_a2_prompt` directly; all take fact
  values as PARAMETERS and import `phase14_factset` lazily or not at all, so the clean-room scan
  stays green.
- **`realized_injection` needs `base_len`** from the caller — 18-05 computes it as
  `len(build_recall_prompt(tok, question))`, which is exactly the prompt portion D-16's strict
  no-value guard runs on.
- **Still not built, by design:** `null_result_is_admissible()`, `main()`, the argument parser, any
  run mode, the NLL/exposure instruments, and the D-12 pre-flight smoke — which per D-28 must run
  *after* the instruments land and *before* any result.
- **No `results/phase18_*` artifact exists**, so every commit here is a legitimate ancestor under
  the D-04 pin.

## Self-Check: PASSED

- `scripts/phase18_extraction.py` — FOUND (666 lines, contains `def build_a2_prompt`, 394
  insertions / **0 deletions** — 18-03's region byte-untouched)
- `tests/test_phase18_corpus.py` — FOUND (385 lines, ≥80 required, 13 tests)
- `tests/test_phase14_scoring.py` — FOUND, contains `("scripts/phase18_extraction.py",
  "build_a3_prompt")` at line 448
- `tests/test_phase16_driver.py` — FOUND (guard repaired, 72 passed)
- `.planning/.../deferred-items.md` — FOUND
- `7104e13`, `6eaa334`, `c965df2`, `0394eec`, `fe6f410` — all FOUND in `git log`
- `.venv/bin/pytest -q` — **673 passed, 7 skipped, 0 failed**
- `.venv/bin/ruff check .` — All checks passed; `ruff format --check .` — 159 files already
  formatted
- `tests/test_phase18_prereg.py::test_no_fact_values_in_phase18_modules` — passed after the
  templates landed
- `ls results/phase18_*` — no matches, as D-04's ordering requires

---
*Phase: 18-black-box-adversarial-extraction-audit*
*Completed: 2026-08-15*
