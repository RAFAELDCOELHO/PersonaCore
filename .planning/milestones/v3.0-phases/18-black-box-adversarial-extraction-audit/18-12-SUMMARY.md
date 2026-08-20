---
phase: 18-black-box-adversarial-extraction-audit
plan: 12
subsystem: documentation
tags: [claim-correction, dated-continuation, verbatim-identity, additivity, cpu-only]

# Dependency graph
requires:
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-07's `LORA_PROPERTY_CAVEAT` / `LOWER_BOUND_SENTENCE` — the ATK-06 caveat this plan restates in prose and names as the pinned form"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-07's `tests/test_phase18_docs.py` — the file extended here"
  - phase: 15-selective-erasure-preregistration
    provides: "the dated-additive-continuation pattern (`tests/test_phase15_docs.py:511-545`) and `_anchored_section`'s shape"
  - phase: 14-clean-room-demo
    provides: "`MEMORY_INFO` / `STATUS_OFF` / `RESET_LABEL` and `_UI_COPY`'s wholesale copy scan"
provides:
  - "`scripts/personalize_demo.py::TOGGLE_IS_AVAILABILITY` — the corrected sentence as the SINGLE SOURCE OF TRUTH, interpolated into `MEMORY_INFO` and `STATUS_OFF`"
  - "README.md + docs/REPORT.md dated v3.0 continuations — 28/0 and 55/0, prior bytes an exact prefix"
  - "`test_claim_sentence_is_verbatim_in_three_surfaces` — AST-read source of truth, anchored section reads, ATK-06 caveat guard"
  - "`test_docs_continuation_is_additive` — committed pre-continuation heading baselines, prefix equality"
  - "`test_no_bare_zero_percent_in_docs` — STAT-02 on both published surfaces, with the regex exercised on controls first"
affects: [18-16]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A published sentence maintained in ONE code literal and read out of it by `ast.literal_eval` — the doc test never retypes it, and `literal_eval` doubles as a guard that the constant stays a plain literal (an f-string cannot be matched character for character in Markdown)"
    - "Additivity proved by PREFIX EQUALITY over a committed heading baseline — presence, order and end-placement in one assertion, with no git call (shallow CI clones make `git show <sha>:<file>` unusable)"
    - "A correction landed DIRECTLY where no prior published claim existed, and as a dated continuation only where one did — the framing is chosen per surface rather than applied uniformly"

key-files:
  created: []
  modified:
    - scripts/personalize_demo.py
    - README.md
    - docs/REPORT.md
    - tests/test_phase18_docs.py

key-decisions:
  - "The sentence lives on ONE UNWRAPPED LINE in both Markdown files. Containment is asserted exactly — no whitespace normalization — and a wrapped sentence would contain a newline that no exact `in` check could match. README already carried a 235-char line, so this is in-file style, not a new one"
  - "`ast.literal_eval` over `importlib` for reading the demo constant: `personalize_demo.py` imports gradio and torch at module scope, and `test_phase18_docs.py`'s stated contract is model-free and framework-free. The plan's rule — read the module's literals, never the Gradio app object — is satisfied more strictly by parsing than by importing"
  - "Heading baselines are committed LITERALS, not read from git. `git show <sha>:<file>` is only checkable where that commit is reachable and CI clones shallow; this is the same reasoning that pinned `_DEMO_APP_SHA256` as content rather than as a commit id"
  - "Prefix equality (`headings[:N] == baseline`) rather than set membership — a set check passes on a document whose sections were shuffled, and shuffling shipped text is exactly what the dated-continuation rule exists to make visible"
  - "The two continuation heading anchors differ in case (`## Claim correction` / `## Claim Correction`) because each file's own heading style differs — README writes `## ` headings in sentence case, docs/REPORT.md in Title Case. Both prefixes end on a word character, which `_anchored_section`'s `\\b` requires"
  - "ATK-06's caveat is RESTATED in doc prose rather than quoted verbatim from `LORA_PROPERTY_CAVEAT`: the committed literal writes `PROPERTY OF LoRA` in caps, which the acceptance grep `LoRA property|property of LoRA` (case-sensitive) does not match. Both docs name the pinned constant as the authoritative form"

requirements-completed: [ATK-06, STAT-02]

# Metrics
duration: ~55min wall clock across a network interruption
completed: 2026-08-16
---

# Phase 18 Plan 12: One Sentence, Three Surfaces

**The memory toggle now reads as availability rather than authorization on all three published
surfaces, the two that carried shipped v2.0 text were EXTENDED with zero deletions and a
byte-identical prefix, and the identity between the three is enforced by a test that was watched
turn red on a one-character change.**

## Performance

- **Duration:** ~55 min wall clock, spanning a transient network failure between Tasks 1 and 2.
- **Tasks:** 3, three commits (one per task; Task 3 is test-only, so it is a single `test(...)`).
- **Files:** 4 — **28/0** README.md, **55/0** docs/REPORT.md, **20/2** `personalize_demo.py`,
  **243/1** `test_phase18_docs.py`. Zero files deleted by any commit.
- **Suite:** **691 passed / 7 skipped / 0 failed** in 133s. The arithmetic is the predicted
  worktree delta exactly: `694 (main after Wave 5) − 6 worktree-only skips + 3 new tests = 691`.

## Task Commits

1. **Task 1** — `TOGGLE_IS_AVAILABILITY` and the corrected `MEMORY_INFO` / `STATUS_OFF` — `809da9b`
2. **Task 2** — the dated v3.0 continuations in README and `docs/REPORT.md` — `5ddb225`
3. **Task 3** — the three guards, plus the watched-RED mutation proof — `576e59b`

## Accomplishments

- **There are not three copies of the sentence; there is one literal and two assertions.**
  `TOGGLE_IS_AVAILABILITY` is a module constant in `scripts/personalize_demo.py`, interpolated into
  both `MEMORY_INFO` and `STATUS_OFF` by f-string, and read out of the source by
  `ast.literal_eval` in the test. The test never retypes it — a retyped sentence is a fourth copy,
  and the drift would leave the test green while the three published surfaces disagreed.
- **The demo's correction carries no supersession framing, because D-23's premise was verified
  rather than assumed.** `grep -cE "superseded|supersedes|previously (stated|claimed)"` on
  `personalize_demo.py` returns **0**. The existing mechanically-honest clauses are kept intact
  ("Nothing is reloaded and nothing is recomputed — 36 boolean flags flip"; "the adapter is loaded
  but gated off") — the correction ADDS the framing sentence rather than replacing the mechanism
  description. `RESET_LABEL` is byte-unchanged and recorded in an inline comment as the one
  authorization-flavoured string in the demo, noted and deliberately not changed.
- **Both published documents were extended, and the extension is proved rather than asserted.**
  `git diff --numstat 098ac4d HEAD` shows **0 in the deletions column** for README and
  `docs/REPORT.md`, and a byte-level check confirms the prior file is an exact PREFIX of the new
  one in both cases (README 11,576 → 13,536 bytes; REPORT 68,137 → 71,839). No section was
  renumbered, no prior sentence reworded.
- **The additivity guard cannot pass vacuously.** Both heading scans are meta-guarded — the test
  asserts headings were found AND that the baseline fixture is non-empty before it asserts anything
  about order — and it uses prefix equality, so a shuffled document fails where a set check would
  pass. The failure message names the index, the heading found and the heading expected.
- **The zero-percent scan proves itself before it reports.** `test_no_bare_zero_percent_in_docs`
  runs its regex against three controls first (a bare `0%` must match, a padded `0.00%` must match,
  a `10%` must not). A scan that had silently stopped matching would otherwise report the strongest
  possible result — no hits anywhere — while checking nothing.
- **ATK-06's caveat is on the surface that will carry the number.** `docs/REPORT.md` records, in
  advance of any Phase 18 measurement, that a low extraction rate may be a property of LoRA at this
  capacity rather than an achievement of PersonaCore's design, and that the audit runs no arm
  separating the two — alongside the lower-bound-on-leakage bound. Both name
  `LORA_PROPERTY_CAVEAT` in `scripts/phase18_extraction.py` as the pinned wording.

## Measurements

Every figure below is a **document/instrument-shape measurement** over committed text. No model,
checkpoint or device is involved anywhere in this plan, and nothing here is a finding about the
model.

### Additivity (Task 2 acceptance)

```
file              insertions  deletions   prev bytes -> now   prior content an exact prefix?
README.md                 28          0    11,576 -> 13,536   YES
docs/REPORT.md            55          0    68,137 -> 71,839   YES
```

### Heading baselines (Task 3)

```
file              pre-continuation `## ` headings   after   prefix equality
README.md                                       7       8   holds
docs/REPORT.md                                 31      32   holds
```

### The watched RED (Task 3 acceptance)

One character changed in README — `authorization` → `authorisation` — applied and restored inside a
single Python process, so an interrupted or crashed proof could not leave the tracked file edited
(18-07's deviation 7, same reasoning). The mutation asserts exactly one byte differs before it is
written.

```
MUTANT written: README.md 'authorization' -> 'authorisation' (1 character)
pytest exit code: 1
E  AssertionError: README.md does not carry the sentence character for character.
   The demo literal is the source of truth and this file is a copy of it: ...
RESTORED.  git diff --exit-code README.md -> 0
```

### Acceptance greps

```
grep -c "availability, not authorization" scripts/personalize_demo.py      1
grep -c "availability, not authorization" README.md                        1
grep -c "availability, not authorization" docs/REPORT.md                   1
grep -cE "superseded|supersedes|previously (stated|claimed)" demo          0
grep -cE "LoRA property|property of LoRA" docs/REPORT.md                    1
grep -nE "\b0(\.0+)?%" README.md docs/REPORT.md                       (none)
grep -c "split(\"## |split('## " tests/test_phase18_docs.py                0
pytest --collect-only | grep -c 'test_'                                    5  (all distinct)
```

## Deviations from Plan

### 1. [Process] The run was cut off by a transient network error after Task 1

- **Found during:** between Tasks 1 and 2
- **Issue:** an `ENOTFOUND` killed the executor after Task 1 was committed. Nothing was stranded:
  the branch was intact, the working tree clean, and `809da9b` already carried the whole of Task 1.
- **Fix:** the coordinator inspected the worktree and resumed the same agent from Task 2. Task 1 was
  verified with `git show --stat 809da9b` and NOT redone. No work was lost or duplicated.
- **Commit:** n/a — no code change.

### 2. [Rule 1 — Bug] The first draft of the demo comment tripped its own acceptance grep

- **Found during:** Task 1, running the acceptance grep
- **Issue:** the comment explaining why no supersession framing belongs in the demo used the word
  *"superseded"* to say it. `grep -cE "superseded|supersedes|previously (stated|claimed)"` returned
  **1** against a criterion of 0. The criterion is right and the draft was wrong: a grep for
  supersession language in the demo should find nothing, and a comment saying "a superseded note
  would be wrong here" still puts that word in the file for the next reader grepping it.
- **Fix:** reworded to "a dated correction marker here would invent a correction that never
  happened". Grep now returns **0**. This is the same mechanical-grep lesson as 18-07's deviation 5,
  arriving on a different file.
- **Files:** `scripts/personalize_demo.py`
- **Commit:** `809da9b`

### 3. [Rule 3 — Blocking] The ATK-06 caveat could not be quoted verbatim and satisfy its own grep

- **Found during:** Task 2
- **Issue:** the wave brief prefers quoting 18-07's committed literal over retyping. But
  `LORA_PROPERTY_CAVEAT` writes the key phrase as **`PROPERTY OF LoRA`** in caps, and Task 2's
  acceptance is `grep -cE "LoRA property|property of LoRA"` — case-sensitive, so a verbatim quote
  of the committed literal would return **0** against a criterion of ≥1. Quoting and satisfying the
  criterion are mutually exclusive as written.
- **Fix:** the caveat is restated in doc prose in the same words with ordinary casing, and both
  documents NAME `LORA_PROPERTY_CAVEAT` in `scripts/phase18_extraction.py` as the pinned,
  authoritative form — so a reader knows which copy governs and the prose is explicitly a
  restatement rather than a rival. The verbatim-identity requirement applies to the availability
  sentence, which is enforced by test; the caveat's mitigation is the grep, as the threat register
  specifies. `scripts/phase18_extraction.py` was NOT edited (18-08 owns it).
- **Files:** `README.md`, `docs/REPORT.md`
- **Commit:** `5ddb225`

### 4. [Rule 2 — Missing critical check] `ast.literal_eval` chosen over `importlib` to read the constant

- **Found during:** Task 3
- **Issue:** the obvious way to read `TOGGLE_IS_AVAILABILITY` is the house `importlib` load, but
  `personalize_demo.py` imports gradio and torch at module scope and `test_phase18_docs.py`'s
  docstring declares the file GPU-free with no model load. Importing would have quietly broken that
  contract to read one string.
- **Fix:** the constant is parsed out of the source with `ast` and `literal_eval`. This is stricter
  on the plan's own rule ("only the module's literals, never the Gradio app object") and buys a free
  guard: the constant must remain a PLAIN string literal, because an f-string would raise here — and
  a sentence assembled at runtime cannot be matched character for character inside a Markdown file.
- **Files:** `tests/test_phase18_docs.py`
- **Commit:** `576e59b`

### 5. The sentence occupies one unwrapped line in both Markdown files

- **Found during:** Task 2, designing for the exact-containment assertion
- **Issue:** the repo wraps Markdown prose at ~95 characters. A wrapped sentence contains a newline,
  which no exact `in` check can match and which `grep` (line-based) would also miss — the plan's
  `grep -c "availability, not authorization"` acceptance requires the phrase on one line at minimum.
  Whitespace-normalizing the comparison instead would have weakened "character for character" to
  "character for character modulo wrapping".
- **Decision:** keep the assertion exact and put the sentence on one line. README already carried a
  235-character line, so this is in-file style rather than a new one. Recorded here because it is
  the reason a reader will find one long line in two otherwise-wrapped documents.

## Verification

| Check | Result |
|---|---|
| `pytest -q` (full suite) | **691 passed, 7 skipped, 0 failed** in 133s |
| `pytest -q tests/test_phase18_docs.py` | 5 passed (2 inherited + 3 new) |
| `pytest -q tests/test_phase14_demo.py` | 22 passed, 2 skipped — unchanged by the copy edit |
| `pytest -q tests/test_phase15_docs.py` | passes with the new `## ` heading appended to REPORT |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 161 files already formatted |
| `git diff --numstat 098ac4d HEAD -- README.md docs/REPORT.md` | **0 deletions on both** |
| Prior content a byte-identical prefix | **YES**, both files |
| Files deleted by any commit | **0** |
| `STATE.md` / `ROADMAP.md` / `REQUIREMENTS.md` touched | **none** — the orchestrator owns them |
| `scripts/phase18_extraction.py` touched | **no** — 18-08 owns it; read only |

## Threat register disposition

| Threat ID | Disposition | Discharged by |
|---|---|---|
| T-18-12-01 (Tampering — shipped v2.0 text edited in place) | mitigated | 0 deletions on both files, prior bytes verified as an exact prefix, and `test_docs_continuation_is_additive`'s prefix equality over a committed heading baseline |
| T-18-12-02 (Repudiation — the three surfaces drift) | mitigated | One literal, read by AST; exact containment asserted in the other two; watched RED on a one-character change |
| T-18-12-03 (Repudiation — supersession framing invented for honest copy) | mitigated | D-23's premise verified against the shipped copy before writing; the acceptance grep returns 0, including inside comments (see deviation 2) |
| T-18-12-04 (Repudiation — ATK-06's caveat omitted) | mitigated | Present in `docs/REPORT.md` and in README, asserted by `test_claim_sentence_is_verbatim_in_three_surfaces`, and named against its pinned constant |
| T-18-12-SC (Tampering — package installs) | accepted | Zero installs; `pyproject.toml` untouched |

## Issues Encountered

- **Worktree base drift, seventh consecutive plan.** HEAD was `829cd5f`, a strict ancestor of the
  required `098ac4d` with a clean tree, so `git merge --ff-only` corrected it with 0 commits lost.
- **Network interruption after Task 1** (see deviation 1). Recovery was clean because Task 1 was
  already committed — the per-task commit discipline is what made the resume free.
- **One `ruff format` reflow** in the new test block (a list comprehension), no `ruff check`
  findings.

## Deferred Issues

None new. The one item in `deferred-items.md` is 18-04's and is untouched.

## Known Stubs

None. Every sentence this plan added is final published text, not a placeholder, and every guard it
added is exercised by a committed test. `RESET_LABEL`'s authorization-flavoured wording is
deliberately unchanged and is recorded as such in D-23, in an inline comment in the demo, and in
both continuations — it is a scoped exclusion, not an unfinished edit.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema at a trust boundary. This
plan writes only prose and test code; nothing here runs a model or touches `results/`.

## Next Phase Readiness

- **18-16 has its additive path already open and already tested.** Appending the measured result to
  `docs/REPORT.md` after this continuation keeps prefix equality holding, and
  `test_no_bare_zero_percent_in_docs` will scan whatever it appends — so a bare `0%` reaching the
  report is caught on the surface a reader actually reads, not only in the driver's rendered text.
- **If 18-16 appends a new `## ` heading to README or `docs/REPORT.md`,
  `_README_HEADINGS_BEFORE` / `_REPORT_HEADINGS_BEFORE` do NOT need updating** — they are the
  pre-continuation baselines and prefix equality tolerates any number of appended headings. They
  must only change if a prior heading is legitimately reworded, which is the event they exist to
  make visible.
- **The claim correction did not wait on the run and does not depend on it.** No Phase 18 number is
  quoted on any of the three surfaces; the correction stands on its own if the audit is delayed.

## Self-Check: PASSED

- `scripts/personalize_demo.py` — FOUND (663 lines; contains `TOGGLE_IS_AVAILABILITY`, referenced
  by both `MEMORY_INFO` and `STATUS_OFF`; `RESET_LABEL` byte-unchanged)
- `README.md` — FOUND (218 lines, was 190; contains the sentence and the dated continuation heading)
- `docs/REPORT.md` — FOUND (1,060 lines, was 1,005; contains the sentence, the ATK-06 caveat and the
  dated continuation heading)
- `tests/test_phase18_docs.py` — FOUND (419 lines, ≥120 required; 5 tests, 3 of them this plan's,
  all node ids distinct)
- `809da9b`, `5ddb225`, `576e59b` — all FOUND in `git log`
- `git status --short` clean apart from this SUMMARY
- No `STATE.md`, `ROADMAP.md` or `REQUIREMENTS.md` touched — the orchestrator owns them
- No file deleted by any commit; zero deletions in either published document

---
*Phase: 18-black-box-adversarial-extraction-audit*
*Completed: 2026-08-16*
</content>
</invoke>
