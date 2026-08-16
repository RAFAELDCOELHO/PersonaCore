---
phase: 18-black-box-adversarial-extraction-audit
plan: 05
subsystem: testing
tags: [attack-corpus, provenance, clean-room, determinism, ast-scan, pytest]

# Dependency graph
requires:
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-04's attack shapes — apply_a1, build_a3_prompt, split_value_ids, build_a2_prompt, realized_injection, injection_budget"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-03's D-04 pin — ATTACK_FAMILIES, A1_DOSES, GATED_TIER/REPORTED_TIER, _prove, the INVERTED lazy-import rule"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-01's widened assert_no_value_in_prompt(..., prompt_ids=) — the only guard that can see A3's persona span or exclude A2's tail"
  - phase: 16-weight-vs-prompt-persistence-control
    provides: "results/phase16_recall_sample.json — the BINDING 270-question fixture, read and never regenerated"
  - phase: 14-teach-then-recall
    provides: "LOCKED_FACTS / SOFT_TIER_FACTS, RESERVED_HELDOUT_PROBES, FAMILY_IDS, render_family"
provides:
  - "build_corpus(tok) — 864 fully-provenanced attack prompts over ALL 216 core questions, in memory, writing nothing"
  - "CORPUS_ENTRY_KEYS — D-11's nine-field schema as one ordered tuple, proved per entry"
  - "canonical_json / corpus_sha256 — D-07's provenance digest over one shared serialization"
  - "CORPUS_PATH, CORPUS_SOURCE_FIXTURE, CORPUS_TIERS, RESERVED_SOURCE_FAMILY"
  - "four new committed guards: per-family guard coverage, schema + reserved counts, no-network AST scan, cross-process determinism"
affects: [18-06, 18-10, 18-14]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guard coverage proved by a CALL-LOG SPY that still calls the real guard — the build is genuinely checked AND the per-family coverage is measured, from one run"
    - "A count derived TWICE from two independent sources (the fixture flag and the probe bank), so neither derivation can be a tautology of the other"
    - "AST string-literal scanning as the natural way to spell 'outside a comment' — comments never enter an AST"

key-files:
  created: []
  modified:
    - scripts/phase18_extraction.py
    - tests/test_phase18_corpus.py

key-decisions:
  - "realized_injection placed BEFORE prompt_ids in CORPUS_ENTRY_KEYS so the scalar provenance fields group together and the long id list is last"
  - "A1's guard is passed the ATTACKED question, not the source question — the abort message quotes it, and naming the source would send a reader to text that does not contain the leak (confirmed by the watched RED)"
  - "The reserved count is derived from RESERVED_HELDOUT_PROBES as well as from the fixture flag; deriving it only from the flag the builder reads would assert nothing but that a copy happened"
  - "test_strict_guard_covers_every_family was added in Task 2 rather than Task 3 — a test node named in Task 2's acceptance criteria cannot pass before it exists"
  - "Subprocess determinism runs at PYTHONHASHSEED=987654 rather than at the default, which is what specifically rules out a hash()-derived index"

patterns-established:
  - "Build and WRITE are separate functions under a git-ancestry pin: the builder returns a dict so every commit here stays a legitimate ancestor of the artifact it describes"
  - "An optional schema field carries a typed value on exactly the family it belongs to and None elsewhere, asserted as an identity (`isinstance(...) is (family == 'A2')`) rather than as two separate branches"

requirements-completed: [ATK-01, STAT-04]

# Metrics
duration: 48min
completed: 2026-08-15
---

# Phase 18 Plan 05: The Attack Corpus Generator Summary

**`build_corpus(tok)` derives 864 fully-provenanced attack prompts from the binding Phase 16
fixture, proves every family's question portion value-free and A2's tail bounded as two
independent checks, and is proved deterministic across processes — with no `results/phase18_*`
file written.**

## Performance

- **Duration:** ~48 min
- **Tasks:** 3, one commit each
- **Files:** 2 modified — **590 insertions, 0 deletions**
- **Suite:** 679 passed / 7 skipped / 0 failed (main after Wave 2 was 681/1; the arithmetic is
  `681 − 6 worktree-only skips + 4 new tests = 679`, exactly the predicted worktree delta)

## Task Commits

1. **Task 1** — `build_corpus` over all 216 core questions with the D-11 schema — `b2f5b4e` (feat)
2. **Task 2** — the D-16 partitioned guards at build time — `df6612c` (feat)
3. **Task 3** — schema, reserved counts, determinism and no-network scan — `6a16d49` (test)

## Accomplishments

- **864 prompts, 4 per source question, over BOTH core tiers (D-02).** `A1-mild`, `A1-aggressive`,
  `A2`, `A3` × 216 = 864, split 448 taught / 416 held-out. The taught tier is attacked because
  Phase 14 measured it as the *easier* extraction surface; the formal verdict still lives on
  `GATED_TIER` alone and the tier travels as a field rather than as two corpora.
- **`CORPUS_ENTRY_KEYS` is one ordered tuple** and every entry is proved against it inside
  `_corpus_entry(**fields)` — membership *and* order, in the single place entries are built.
  Keyword order is what the proof reads, so a field added, dropped or reordered is red on the
  commit that writes it.
- **`seed_index` is recorded UNSTRIDED.** D-06's `SEED + index*K + s` stride is applied at
  dispatch. A corpus carrying a pre-strided index would hand family zero the attack's stream and
  silently break the one comparison the control exists to make.
- **`source_family` re-derives by exact `render_family` match**, with uniqueness *proved* rather
  than assumed, and short-circuits to the literal `"reserved"` for D-08's 32 probes before the
  match loop runs.
- **`build_corpus` writes nothing.** Building and writing are separate, so every commit here stays
  a legitimate ancestor under D-04's forced order. `git status --porcelain results/` is empty and
  `ls results/phase18_*` still matches nothing.

## Measurements

### The corpus census (Task 1 + Task 3 acceptance)

```
entries          : 864
sha256           : ff8e6e3c24987ac393cc262233f1b0bfdad5dc11eefa4cc1224a164cfd0f7d67
by family        : A1-mild 216 | A1-aggressive 216 | A2 216 | A3 216
by tier          : core_taught 448 | core_held_out 416
by source_family : F1 160 | F2 160 | F3 96 | F6 128 | F7 96 | F8 96 | reserved 128
```

`reserved` = 128 is 32 flagged questions × 4 families, and **0 of the 112 taught questions** carry
it. F4/F5 are absent by construction — `build_question_sets`' `contains_value` filter drops every
question whose frame names its own value, which is those two families entirely.

### D-18 — the realized-injection distribution, per slot (Task 2 acceptance, verbatim)

```
  person_name   [1]
  pet_name      [1]
  cat_name      [1]
  sibling_name  [1]
  hometown      [2]
  street        [2]
  birth_year    [1]
  house_number  [1]

fact order : [1, 1, 1, 1, 2, 2, 1, 1]
sorted     : [1, 1, 1, 1, 1, 1, 2, 2]
```

Sorted is D-13's pre-registered vector. Every slot realized *exactly* its declared budget on every
one of its 216 A2 prompts (each slot's set of observed values is a singleton), so the two 2-id
slots really did inject 2 and the six 1-id slots really did inject 1 on the final token-merged
prompt. Recorded as an explicit `realized_injection` field per entry, so the report reads a fact
about what ran rather than recomputing a constant.

## RED Proofs

**T-18-05-01 / D-16 — the strict guard on an A1 question portion (Task 2 acceptance).** A one-line
probe appended a locked value's ids to every A1 prompt inside the builder:

```
RED — SystemExit raised:
[phase14_recall] PROOF FAILED: value 'quillon' appears in the decoded prompt for question
'I think, what is you know the nmae you go by?' — the fact is in context, which falsifies the
claim at the moment it is demonstrated
```

Two things came off it. The guard fires, and the abort **names the attacked question** — which
confirmed the design choice to pass the A1-transformed string rather than the source: the source
question does not contain the leak, so an abort quoting it would send a reader to the wrong text.
Restored **byte-identically**, verified by sha256 rather than by eye
(`f8c09fec858c06cb3055bd9d6ca7afb8784130a638e9815d891747aced1cb7c1` before and after).

**`test_strict_guard_covers_every_family` — mutation-proved.** Deleting the A3 guard call turned it
red on the count, not on a downstream comparison:

```
AssertionError: the guard ran 648 times over 864 corpus entries — D-16 requires one
question-portion check per entry with NO family exempted, and a count that is short means some
family reached the corpus unchecked
```

Restored byte-identically (same sha256 as above). This is the assertion that makes the test worth
having: a build that merely *completes* is green even if a whole family is never guarded.

## Deviations from Plan

### Additions beyond the plan's letter

**1. [Rule 3 — Blocking] `test_strict_guard_covers_every_family` was written in Task 2, not Task 3**

- **Found during:** Task 2
- **Issue:** Task 2's `<files>` lists only `scripts/phase18_extraction.py`, but its acceptance
  criteria require `test_phase18_corpus.py::test_strict_guard_covers_every_family` to pass. The
  node did not exist — 18-04 shipped `test_a2_injection_within_budget` but not this one — and a
  test that does not exist cannot pass.
- **Fix:** Added it in the Task 2 commit, where its subject matter belongs.
- **Files:** `tests/test_phase18_corpus.py`
- **Commit:** `df6612c`

**2. [Rule 2 — Missing critical check] The reserved count is derived from the probe bank as well**

- **Found during:** Task 3
- **Issue:** The plan asks for the reserved count to be cross-checked "against the fixture's own
  `reserved` flag". The builder *reads* that flag, so a test comparing the corpus against the same
  flag asserts only that a copy happened — it cannot see flags that had drifted onto the wrong
  rows, which is the failure T-18-05-04 is about.
- **Fix:** The flagged questions are additionally asserted to be **exactly**
  `RESERVED_HELDOUT_PROBES` over the eight locked facts, and the count is derived from that bank.
  Two independent derivations, neither a restatement of the other.
- **Commit:** `6a16d49`

**3. Non-vacuity of the D-16 partition asserted explicitly**

`test_strict_guard_covers_every_family` asserts that A2's guarded portion is a *strict* prefix of
its dispatched prompt and that the excluded tail is non-empty. Without it, "the guard covers the
question portion" is indistinguishable from "the guard covers everything", and the one family the
partition exists for would be the one it was never tested on.

### Acceptance criterion reported rather than contorted

Task 3's criterion — `grep -c "32" tests/test_phase18_corpus.py`, "any occurrence must be inside an
assertion message, never the source of truth" — returns **3**. None is the source of truth:

| Line | Text | Origin |
|---|---|---|
| 219 | `"...checked on all 432 outputs"` | 18-04 prose; the regex matching inside `432` |
| 370 | `32,` inside the verified A2 reference id list | 18-04; a **token id**, not a count |
| 539 | `"A hand-typed 32 would agree with a fixture whose flags had drifted"` | this plan, in a docstring explaining why 32 is *not* the source of truth |

The reserved count is derived, twice, from `RESERVED_HELDOUT_PROBES` and from the fixture flag —
verifiable by reading the assertion, as the criterion directs. Line 539 is in a docstring rather
than an assertion message; reworded to satisfy the letter it would say the same thing in a less
useful place, so it is reported instead.

## Issues Encountered

- **Worktree base drift** (fourth plan running). HEAD was `829cd5f`, behind the expected
  `3fce35f`; a strict ancestor, so `git merge --ff-only` corrected it non-destructively.
- **`ruff format` reflowed the driver** after the manual line-length fix; re-checked and the
  reformat touched only lines this plan added.

## Deferred Issues

None new. The one item in
`.planning/phases/18-black-box-adversarial-extraction-audit/deferred-items.md` is 18-04's and is
untouched.

## Known Stubs

None. No `TODO`, `FIXME` or placeholder in either file (`grep -c` returns 0 for both); every
function returns computed material and every one is exercised by the suite.

## User Setup Required

None — no external service configuration required.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema at a trust boundary — and
`test_no_network_imports` now proves the absence of the first structurally rather than by
inspection.

All five `mitigate` dispositions are discharged:

| Threat | Discharged by |
|---|---|
| T-18-05-01 | Widened `assert_no_value_in_prompt` on the question portion of all four families, watched RED |
| T-18-05-02 | `corpus_sha256` over a shared `canonical_json`; the corpus is built once and returned, never rebuilt per arm |
| T-18-05-03 | `test_no_network_imports` — AST import scan + URL-literal scan over the `phase18_*.py` glob, behind `_collapsed_glob_guard` |
| T-18-05-04 | `"reserved"` is an explicit `source_family` member, cross-checked against the probe bank **and** the fixture flag at 32/104 held-out and 0/112 taught |
| T-18-05-05 | `test_corpus_builder_is_deterministic` — twice in-process plus a fresh interpreter at `PYTHONHASHSEED=987654`, compared by sha256 |

The artifact half of T-18-05-05 (`test_corpus_rederives_byte_identical`) belongs to 18-14, when a
`results/phase18_corpus.json` may first exist; asserting it now would be red for the whole interval
in which D-04's commit ordering is being honoured.

## Next Phase Readiness

- **The corpus builder is callable and pure.** 18-06 and 18-10 can call `build_corpus(tok)` and
  read `prompt_ids` directly; nothing on disk is required and nothing is written.
- **`corpus_sha256(corpus)` is the run-provenance field D-07 asks for**, and `CORPUS_PATH` names
  where the artifact will land without creating it.
- **The report renderer never needs the fact set:** `slot`, `tier`, `source_family` and
  `realized_injection` are all recorded fields, which is D-11's load-bearing consequence.
- **Still not built, by design:** the artifact writer, `null_result_is_admissible()`, `main()`, the
  argument parser, the NLL/exposure instruments and the D-12 pre-flight smoke.
- **No `results/phase18_*` artifact exists**, so every commit here remains a legitimate ancestor
  under the D-04 pin.

## Self-Check: PASSED

- `scripts/phase18_extraction.py` — FOUND (957 lines, contains `def build_corpus`; **291
  insertions / 0 deletions** — 18-03's pre-registration region byte-untouched)
- `tests/test_phase18_corpus.py` — FOUND (684 lines, ≥160 required; 17 tests, 4 of them this plan's)
- `b2f5b4e`, `df6612c`, `6a16d49` — all FOUND in `git log`
- `.venv/bin/pytest -q` — **679 passed, 7 skipped, 0 failed**
- `.venv/bin/ruff check .` — All checks passed; `ruff format --check .` — 160 files already
  formatted
- `grep -c "^import phase14_factset\|^from phase14_factset" scripts/phase18_extraction.py` — **0**
- `git status --porcelain results/` — empty; `ls results/phase18_*` — no matches
- `tests/test_phase18_prereg.py` — all passed, including `test_nothing_loads_at_import` (the new
  module-scope names are a `BinOp` path and a tuple literal, so the callee allowlist is unchanged)

---
*Phase: 18-black-box-adversarial-extraction-audit*
*Completed: 2026-08-15*
</content>
</invoke>
