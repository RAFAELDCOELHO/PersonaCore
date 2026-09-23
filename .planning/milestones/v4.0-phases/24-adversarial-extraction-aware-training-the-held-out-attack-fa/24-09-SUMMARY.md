---
phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
plan: 09
subsystem: measurement-record
tags: [uat-closure, provenance, module-sha256, green-but-blind, write-once, re-emit, byte-identity]

# Dependency graph
requires:
  - phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
    provides: "24-07's `scripts/phase24_record.py` — its `provenance.module_sha256` block, its write-once refusal, and the `_PUBLICATION_PATHSPEC` record-exclusion that makes re-emission reachable at all"
  - phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
    provides: "24-07's `tests/test_phase24_record.py` and its live `corpus_sha256` check at `:274` — the shape this plan's guard mirrors"
  - phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
    provides: "24-08's blocker fixes (`ba2787f`, `d4ed1f8`) — the edits that caused the drift this plan closes"
provides:
  - "`tests/test_phase24_record.py::test_the_provenance_pins_match_the_live_module_bytes` — the freshness guard that was missing; all five pins (4 modules + the tokenizer) against live bytes"
  - "`results/phase24_token_budget.json` re-emitted at `46f07d5` — all four `module_sha256` pins true, every substantive figure byte-identical"
  - "24-HUMAN-UAT.md item 4 RESOLVED under closure (a), with a correction to 24-VERIFICATION's reason 4"
affects: [25 frontier sweep driver, 25 SC4 single-source-of-truth artifact]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A pin that nothing reads is not evidence — every `*_sha256` a record publishes needs a live-comparison test, or it rots silently while the suite stays green"
    - "Collect ALL violations before asserting: a per-item `assert` inside the loop names the first and hides the rest, and a reader who sees one name concludes one file"
    - "Re-derive a published digest from BYTES in the test, never through the emitter's own `_sha256` — a pin checked by the function that wrote it agrees by construction"
    - "Re-emission is proved safe by EXCLUDING the fields allowed to move and demanding byte-identity of the whole remainder, not by comparing the figures a human happens to look at"

key-files:
  created:
    - .planning/phases/24-adversarial-extraction-aware-training-the-held-out-attack-fa/24-09-SUMMARY.md
  modified:
    - tests/test_phase24_record.py
    - results/phase24_token_budget.json
    - .planning/phases/24-adversarial-extraction-aware-training-the-held-out-attack-fa/24-HUMAN-UAT.md
    - .planning/STATE.md

key-decisions:
  - "Closure (a) — guard AND re-emit — per the developer's instruction. The pin now promises 'HEAD regenerates this record', which is a checkable claim, rather than 'some past commit did', which nothing can check"
  - "The guard covers `tokenizer_sha256` as well as `module_sha256`: it was unguarded for exactly the same reason, and including it is three lines"
  - "One disclosed RED commit (`46f07d5`). The drift was PRE-EXISTING and real, so the RED was free — taking it in the tree's natural state is stronger evidence than any planted mutation, and the alternative (one combined commit) would have hidden the sequence"
  - "24-VERIFICATION's reason 4 — 're-emitting is blocked anyway' — was MEASURED FALSE and is corrected in the UAT item rather than inherited"
  - "ROADMAP.md and REQUIREMENTS.md deliberately UNTOUCHED (24-08's precedent, `669343e`): a UAT-closure plan with no PLAN.md moves no plan count and no requirement. ADVT-01 stays UNTICKED"

requirements-completed: []

# Metrics
duration: 24min
completed: 2026-08-30
---

# Phase 24 Plan 09: The Provenance Freshness Guard and the Re-Emitted Record — Summary

**UAT item 4 is closed under option (a). The missing guard landed FIRST and was watched RED against
the tree's own pre-existing drift — `2 of 5 provenance digests no longer match the files on disk`,
naming both stale modules with recorded and live in full — and the record was then re-emitted so all
four pins are true. Every substantive figure came out byte-identical, and that is proved three
independent ways rather than eyeballed: the non-provenance remainder hashes to
`739658923d00…` on both sides, a recursive walk over 529 leaf scalars (317 numeric) finds 0
differing, and `git diff` on the artifact is 4 lines, all inside `provenance`.**

## Performance

- **Duration:** ~24 min
- **Task commits:** `46f07d5` (test, RED by design), `aaea029` (fix, GREEN)
- **Tasks:** 2 of 2
- **Files:** 1 test modified (+59 lines), 1 artifact re-emitted (4 lines changed), 1 UAT file
  resolved, 1 SUMMARY created. **0 source files modified** — `git diff --stat df8c3c2..HEAD --
  scripts/ src/` is empty.

## Task 1 — the guard, watched RED in the tree's natural state

`tests/test_phase24_record.py::test_the_provenance_pins_match_the_live_module_bytes`, appended as
section 5, mirroring the live `corpus_sha256` comparison at `:274` that was the file's only
enforced pin.

**The RED was free and was taken, not fabricated.** The pins were stale at `df8c3c2` before a single
line of this plan was written, so writing the test and running it against the unmodified tree
produced a genuine failing state over real drift. No mutation, no hand-edit, no restore step — and
therefore none of the hazards a planted RED carries (landing on the wrong occurrence, restoring
imperfectly). This is the same evidence shape 24-05 and 24-06 used and 24-07 named as its own best
pattern.

### The actual failure output

```
E       AssertionError: 2 of 5 provenance digests no longer match the files on disk:
E             scripts/phase24_adversarial.py
E               recorded 8f884fd75e0be6b6bff482f20ed2c0e07d54db7b0450fea0e0aecc7b3dafc9df
E               live     b679c6f6b20657f48d2e8c7cde36d3b7e4221ed7af7782fc02f0b0b29d5fdf22
E             scripts/teach_persona.py
E               recorded e2709e549bf79e994b80fa6caf5eec7ddc10091907332f08cd0b07a016ddb9ad
E               live     82da6c3aa5a8bcc809b70bcda75e2e45d9ddf230716fe787527df0231b32e29c
E           provenance.module_sha256 claims these bytes regenerate this record. They no longer do.
E           The record's NUMBERS may still be correct — check them separately — but the pin is no
E           longer evidence of anything. Re-emit: delete results/phase24_token_budget.json at a
E           clean tree and run `python scripts/phase24_record.py`, then confirm every substantive
E           figure came out byte-identical before committing.

tests/test_phase24_record.py:326: AssertionError
1 failed, 5 passed in 0.90s
```

Both stale modules named, both digest pairs in full, `2 of 5` (the two clean modules and the
tokenizer are the other three). The message also names the fix, because a refusal that does not say
what to do next gets worked around — `phase21_unit_record._DIRTY_DETAIL`'s register.

### Three properties the guard has that a bare `assert a == b` would not

1. **It collects ALL drift before asserting.** A per-item `assert recorded == live` inside the loop
   raises on `phase24_adversarial.py` and never reaches `teach_persona.py`. A reader sees one name
   and concludes one file — strictly worse than the situation it replaces, because it converts a
   two-module problem into a confident one-module report.
2. **Digests are recomputed from BYTES in the test**, via `hashlib.sha256(path.read_bytes())`, and
   NOT through the emitter's own `phase24_record._sha256`. A pin re-derived by the function that
   wrote it agrees with it by construction — including if that function ever started hashing text,
   which is precisely what `tests/test_package.py:36`'s bytes-never-text rule exists to prevent.
3. **Non-vacuity is checked first**, in this module's existing register: an empty `module_sha256`
   makes the loop trivially pass, so `assert pins` runs before it, and the emitter is asserted to
   pin ITSELF (`scripts/phase24_record.py` must be a key) — a record that does not name the bytes
   that wrote it cannot establish its own reproducibility no matter how many other digests match.

**`tokenizer_sha256` is included too.** It sits in the same `provenance` block, was unguarded for
the same reason, and adding it is three lines. It was already fresh (`e82e8e83…`), so it
contributed the `5` denominator rather than a finding.

## Task 2 — the re-emission, and the byte-identity proof

### The sanctioned route, taken rather than worked around

The write-once refusal was watched firing first, and it names its own re-emit route:

```
[teach_persona] /Users/juliorcoelho/PersonaCore/results/phase24_token_budget.json already exists —
this arm is recorded evidence. Delete /Users/juliorcoelho/PersonaCore/results/phase24_token_budget.json
to re-run.
```

Record still present afterwards, sha unchanged at `8d3e474f…` — the refusal is a refusal, not a
warning. Deleting and re-running is not a workaround for the guard, it is the route the emitter was
built with: `scripts/phase24_record.py:76-81` says so in as many words — *"The EXCLUSION is what
makes the guard reachable at all — re-emitting requires deleting the previous artifact first, which
is itself a dirty tree."* No file was hand-edited and nothing was written to a temporary path and
copied in (`_DIRTY_DETAIL` names that as CR-02 with extra steps).

### CORRECTION: re-emission was never blocked

24-VERIFICATION's reason 4 states re-emission is *"blocked anyway right now: `refuse_if_dirty`
counts untracked files as dirty and the working tree carries `M .gitignore` and
`?? .planning/todos/`."* **Measured, that is FALSE.** 24-07 deliberately narrowed
`_PUBLICATION_PATHSPEC` from the plan's `.` to `(scripts, src, results, artifacts,
:(exclude)<record>)` for exactly those two paths (24-07-SUMMARY deviation 1). So:

```
$ git status --porcelain -- scripts src results artifacts ':(exclude)results/phase24_token_budget.json'
(empty)
```

The guard never fired. The premise was inherited from the incumbent pathspec rather than measured
against the one actually in the module. This is recorded in the UAT item so the correction travels
with the decision.

### THE LOAD-BEARING CHECK — every substantive number, byte-identical

Old bytes saved before deleting (`8d3e474ffd3f0dd2fb8216600db9181b1361cd4f7cf62e3ed09af268faf8bf46`,
which is the digest 24-07 recorded when it restored the file after its hand-edit probe — so the
starting point is provably the committed record).

**Instrument 1 — remainder hash after excluding ONLY the provenance fields:**

```
raw sha256  old: 8d3e474ffd3f0dd2fb8216600db9181b1361cd4f7cf62e3ed09af268faf8bf46
raw sha256  new: 1f73cc56b0ea85fa5961a5328b489130f8ebe1d2a2d4b95ffe4ff30bc9be0a8d
raw bytes identical: False (expected False — provenance legitimately moves)

top-level key order identical: True ['grid', 'arms', 'rows', 'band_corners',
                                    'token_budget_disclosure', 'attack_corpus', 'provenance']
provenance key order identical: True

=== the ONLY fields excluded, and what each did ===
  module_sha256[scripts/phase24_record.py]:      f2267e14ab76… -> f2267e14ab76…  same
  module_sha256[scripts/phase24_adversarial.py]: 8f884fd75e0b… -> b679c6f6b206…  moved
  module_sha256[scripts/mitigation_budget.py]:   2e5adc916702… -> 2e5adc916702…  same
  module_sha256[scripts/teach_persona.py]:       e2709e549bf7… -> 82da6c3aa5a8…  moved
  git_sha:     5aed70fb017213eaf3cb1814a5fd77392fa90f34
            -> 46f07d5fe49ba44df053e5b75fbaf34fa749b559  moved
  written_utc: 2026-08-30T18:49:50Z -> 2026-08-30T21:00:43Z  moved

=== EVERYTHING ELSE ===
remainder sha256 old: 739658923d004d0a4eef26bddb8a96aaccbb245743432d6809ce91c8b77fa132
remainder sha256 new: 739658923d004d0a4eef26bddb8a96aaccbb245743432d6809ce91c8b77fa132
BYTE-IDENTICAL: True (49032 chars each)
```

Re-serialized with `sort_keys=False`, so **key ORDER is part of the comparison** — a reordered
record produces different bytes here even with identical values. Both orders were also asserted
explicitly.

**Instrument 2 — recursive scalar walk**, so the result does not rest on both sides having been
serialized by the same `dumps()` call:

```
recursive walk: 529 leaf scalars (317 numeric), differing: 0 []
```

**Instrument 3 — git itself.** `git diff results/phase24_token_budget.json` is
**4 insertions, 4 deletions**, and every one of the eight lines is inside the `provenance` block:
`git_sha`, `written_utc`, and the two moved module digests. Nothing in `grid`, `arms`, `rows`,
`band_corners`, `token_budget_disclosure` or `attack_corpus` moved by one character.

**Nothing was accepted as a new value, because nothing moved.** Had any figure changed, this plan
would have halted and reported it as a finding outranking the task — a moved number would have
contradicted the re-verification and meant 24-08's fixes altered a measured quantity. The stdout of
the re-run reproduces all twelve rows exactly (`adv_n8` 2,719 → 9,817, `adv_n64` 28,128 → 84,912;
fractions 0.358660 → 0.241009 and 0.390163 → 0.251734).

### The pins, after

```
scripts/phase24_record.py          f2267e14ab76… OK
scripts/phase24_adversarial.py     b679c6f6b206… OK
scripts/mitigation_budget.py       2e5adc916702… OK
scripts/teach_persona.py           82da6c3aa5a8… OK
git_sha 46f07d5 == HEAD at write time
```

`git_sha` follows 24-07's pattern: it names the commit that was HEAD when the bytes were written
(`46f07d5`, the guard commit), which contains all four pinned modules at exactly these digests, and
the record lands in the NEXT commit (`aaea029`). The record's `git_sha` therefore names a commit
that does not contain the record — by construction, the same as `5aed70f`/`7075951` before it. No
value was invented for a field whose source has none.

`tests/test_phase24_record.py` after the re-emission: **6 passed in 0.68 s.**

## The disclosed RED window

`46f07d5` leaves HEAD RED for one commit. This is deliberate and is the honest record of the
sequence: the guard is a TDD RED gate over a defect that already existed in a committed artifact,
and the drift is exactly what it was written to catch. Committing guard and fix together would have
made the RED unreproducible from the history. 24-08 set the precedent for disclosing a two-commit
RED window in this phase; this one is a single commit and closes in the next.

- `46f07d5` — `test(24-09)` — RED: 1 failed, 5 passed in `tests/test_phase24_record.py`.
- `aaea029` — `fix(24-09)` — GREEN: 6 passed.

## Deviations from Plan

### 1. [Rule 2 — Missing critical functionality] The guard covers `tokenizer_sha256`, not only `module_sha256`

- **Found during:** Task 1.
- **Issue:** the objective names `provenance.module_sha256`. `tokenizer_sha256` sits in the same
  block, is published with the same promise, and was equally unguarded — `grep -rn
  "tokenizer_sha256" tests/` finds no live comparison either. Fixing the named field and leaving its
  neighbour is fixing the symptom the ticket reports rather than the class: the next drift would be
  invisible for exactly the reason this plan exists.
- **Fix:** the tokenizer path and digest are added to the same `pins` dict, so one loop covers all
  five. It was already fresh, so it changed no outcome — it changed the denominator from 4 to 5.
- **Commit:** `46f07d5`.

### 2. [Rule 1 — Bug] 24-VERIFICATION's reason 4 is false and is corrected rather than inherited

- **Found during:** Task 2, before the first re-emit attempt.
- **Issue:** the verification report states re-emission is blocked by `refuse_if_dirty` on
  `M .gitignore` / `?? .planning/todos/`. Acting on that premise would have meant either committing
  two unrelated user changes into a phase-24 commit, or declining option (a) as impossible.
- **Fix:** measured instead of accepted. `_PUBLICATION_PATHSPEC` excludes both paths by 24-07's own
  deliberate narrowing; the scoped `git status` is empty and the guard never fires. The correction
  is written into the UAT item beside the decision.
- **Files modified:** `24-HUMAN-UAT.md`.

### 3. [Rule 3 — Blocking] Two commits, and one of them is RED

- **Found during:** Task 1 → Task 2 boundary.
- **Issue:** the guard must be watched RED, and per-task commits mean the RED lands in history.
- **Fix:** disclosed above rather than hidden by squashing. `git_sha` benefits: the record's
  recorded commit is the guard commit, so the artifact's provenance names a tree in which the guard
  exists.

**Total deviations: 3.** No architectural change, no package installed, no checkpoint reached, no
authentication gate, no source file modified.

## Verification Results

| Check | Result |
|---|---|
| `pytest tests/test_phase24_record.py` BEFORE the re-emit | **1 failed, 5 passed**, 0.90 s — the natural RED, output quoted above |
| `pytest tests/test_phase24_record.py` AFTER the re-emit | **6 passed**, 0 failed, 0.68 s |
| All 4 `provenance.module_sha256` vs live | **4 of 4 OK** (was 2 of 4) |
| `provenance.tokenizer_sha256` vs live | **OK** (`e82e8e83…`, unchanged) |
| Old-vs-new remainder sha256 (excl. `module_sha256`/`git_sha`/`written_utc`) | **`739658923d00…` == `739658923d00…`**, 49,032 chars each |
| Recursive scalar walk, old vs new | **529 leaves (317 numeric), 0 differing** |
| `git diff results/phase24_token_budget.json` | **4 insertions, 4 deletions, all inside `provenance`** |
| Top-level and `provenance` key ORDER | **identical** both levels |
| **Full suite** `.venv/bin/python -m pytest -q` | **1647 passed, 1 skipped**, 0 failed, **387.74 s**, exit 0 |
| Baseline reconciliation | orchestrator-measured **1646 passed / 1 skipped**; delta **+1** = the one new guard. Nothing else moved |
| AST: `phase24_adversarial` module-level imports | `['pathlib', 'phase14_factset', 'sys']` — exact, lazy-import boundary holds |
| AST: `phase14_recall` module-level `phase24_adversarial` | **absent** |
| AST: `336` int literals in `phase24_adversarial` / `phase14_recall` | **0 / 0** |
| SC1 byte-identity `build_bins(adv_n8, adversarial_ratio=0.0)` | token sha **`f146d426`**, mask sha **`a2c4771f`** — both as pinned; `repr(stats)` opens `{'episodes': 176, 'tokens': 7581, 'teaching_tokens': 7581, 'replay_tokens': 0, …}` |
| `git diff --stat df8c3c2..HEAD -- scripts/ src/` | **empty** — this plan touched no source file, so the SC1 path could not have moved |
| `(?:==\|!=)\s*10(?![0-9_])` in the new test code | **0 hits** — the twelve-member SC5 wall census needed no entry |
| `train_arm(` in the new test code | **0** — `test_phase23_resume`'s 24-entry prose census needed no extension |
| `persona=` in the new test code | **0** — `PERSONA_ALLOWLIST`'s census needed no entry |
| `tests/test_phase24_correction.py` (ROADMAP tripwire) | **green** (inside the full suite; ROADMAP.md was not touched at all) |
| ADVT-01 | **still UNTICKED** — `.planning/REQUIREMENTS.md` not modified by this plan; nothing written here implies an adapter was trained |
| `ruff check .` / `ruff format --check .` | **All checks passed**; **230 files** already formatted |
| `git status --porcelain data/` | **empty** — the re-emit builds under `TemporaryDirectory`, never `data/` |

### Method substitutions

- `grep -E "(==|!=)\s*10(?![0-9_])"` was run through Python's `re` rather than the shell: the local
  `grep` is `ugrep` and rejects the lookahead, silently returning an empty and meaningless result
  (24-07 found the same and recorded it).
- The byte-identity claim uses three independent instruments because it is the claim the whole task
  rests on, and a single serializer-based comparison could agree with itself.

**No `gsd-sdk` mutation handler was called.** `.planning/STATE.md` and `24-HUMAN-UAT.md` were
hand-edited with occurrence-counted replacements (repo hazard #1), matching all eight prior plans.

## Requirements

**No requirement moved, and none should have.** ADVT-02 and ADVT-03 were ticked by 24-07; ADVT-01
remains open and `.planning/REQUIREMENTS.md` was not touched by this plan. This work restores the
provenance of an already-committed ADVT-03 artifact; it does not extend what that artifact claims.
**No adapter has been trained.**

## Issues Encountered

None beyond deviation 2. The three registered guards that could have bitten
(`test_phase21_sc5`'s twelve-member `== 10` wall census, `test_phase23_resume`'s 24-entry
`train_arm(` prose census, `test_phase24_correction`'s ROADMAP tripwire) all stayed green with no
edit, because this plan added no assertion of that shape, no `train_arm(` string, and no ROADMAP
change at all.

## Known Stubs

None. The one test added is fully implemented and consumed by the suite; every value it reads exists
in the artifact and every branch it can take was exercised — the drift branch on `df8c3c2` (2 of 5
reported) and the clean branch after `aaea029` (0 of 5).

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema at a trust boundary. The
change is one read-only test and a regenerated JSON record.

| Threat | Status |
|---|---|
| T-24-38 ADVT-03 provenance loss | **strengthened** — the digests are now enforced against live bytes rather than merely published; the previously-unguarded field was the exact hole this threat describes |
| T-24-42 write-once artifact | intact — the refusal was watched firing before the delete, `refuse_if_dirty` still runs on the re-emit path, and the sanctioned route was used rather than bypassed |
| T-24-43 frozen inputs | intact — `git diff df8c3c2..HEAD -- scripts/ src/` empty; the corpus digest re-recomputed live at re-emit and unchanged |
| T-24-SC package installs | none |

## Next Phase Readiness

- **UAT item 4 is closed** (`24-HUMAN-UAT.md`, closure (a), `passed: 2 / pending: 2`). Items 2 and 3
  remain open; both are editorial/planning calls untouched by this plan.
- `results/phase24_token_budget.json` now carries a pin that HEAD can actually satisfy, and the
  suite fails if it ever stops being able to. **Any future edit to `phase24_record.py`,
  `phase24_adversarial.py`, `mitigation_budget.py`, `teach_persona.py` or the frozen tokenizer will
  now turn this test RED** — that is the intended cost of the pin, and the resolution is to re-emit
  by the route above and re-prove byte-identity, not to relax the guard.
- The phase-CLOSE step still owns the ROADMAP phase-heading checkbox, the progress-row Status cell,
  and STATE's `status` / `completed_phases` / `percent` (precedent `5a72670`). Untouched here.
- **ADVT-01 is still open.** No adapter has been trained. Phase 25 runs the sweep.

---
*Phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa, Plan 09*
*Completed: 2026-08-30*

## Self-Check: PASSED

All five touched paths exist on disk; both task commits (`46f07d5`, `aaea029`) are present in
`git log --all`; `git diff --diff-filter=D --name-only df8c3c2..HEAD` is empty, so neither commit
deleted a tracked file. Every figure above was measured in this session — the RED output is the
literal pytest capture, the three byte-identity instruments were run and their raw output pasted
rather than paraphrased, and the full-suite number (**1647 passed / 1 skipped**, 387.74 s, exit 0)
is this executor's own run, +1 over the orchestrator's 1646/1 and fully accounted for by the one
new guard. `.planning/STATE.md`'s diff was read line by line: exactly **6 deletions**, all intended
(`stopped_at`, `last_updated`, the two Current-Position lines, `Last session`, and the `Stopped at`
first line demoted to `Superseded stop record (24-08)` with its body preserved verbatim).
`.planning/ROADMAP.md` and `.planning/REQUIREMENTS.md` are untouched — `git status --porcelain` on
both is empty and ADVT-01 is still `- [ ]` at REQUIREMENTS.md:304.
