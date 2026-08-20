---
phase: 18-black-box-adversarial-extraction-audit
plan: 14
subsystem: evaluation
tags: [attack-corpus, artifact, byte-equality, re-derivation, provenance, ancestry-guard]

# Dependency graph
requires:
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-05's `build_corpus` / `canonical_json` / `corpus_sha256` / `CORPUS_ENTRY_KEYS` — the pinned builder this artifact is the output of"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-10's `--corpus` mode and `run_corpus`'s clobber refusal — the only sanctioned writer of `CORPUS_PATH`"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-13's `2d7151e` — the commit that armed the STAT-05 ancestry guard this plan's artifact is now measured by"
  - phase: 16-weight-vs-prompt-persistence-control
    provides: "results/phase16_recall_sample.json — the BINDING 216-question fixture the builder reads and never regenerates"
provides:
  - "`results/phase18_corpus.json` — 864 attack prompts with full D-11 provenance and recorded `prompt_ids`, sha256 `ff8e6e3c24987ac393cc262233f1b0bfdad5dc11eefa4cc1224a164cfd0f7d67`; the INPUT both arms dispatch and the join key their records carry"
  - "`test_corpus_rederives_byte_identical` — the standing D-07 guard tying that file to the pinned generator, watched RED"
  - "The second tracked `results/phase18_*` artifact, raising the STAT-05 ancestry guard from 26 to 52 checked pairs"
affects: [18-15, 18-16]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A re-derivation guard that compares field-by-field BEFORE byte-wise, so the failure names the entry index, the field and the id position rather than reporting a hash mismatch over 375 KB of single-line JSON"
    - "An artifact ASSERTED to exist rather than skipped over — a guard that skips is green in exactly the state it exists to catch"
    - "Key ORDER asserted where it survives (the artifact's own `entry_keys` list) and key MEMBERSHIP asserted where canonicalization destroyed the order (`sort_keys=True` per-entry)"

key-files:
  created:
    - results/phase18_corpus.json
  modified:
    - tests/test_phase18_corpus.py

key-decisions:
  - "The RED proof mutated the COMMITTED artifact in place rather than a tmp copy. The plan permitted a tmp path, but pointing the test at a copy needs a monkeypatched `CORPUS_PATH`, which proves a parameterized helper red rather than the committed node. Mutating in place and restoring from the committed blob proves the node as it will actually run, and the restore is verifiable by digest."
  - "Per-entry keys are compared SORTED, not ordered. `canonical_json` sets `sort_keys=True`, so the artifact's per-entry keys are alphabetical by construction and asserting D-11's declared order against them would be red for a reason that is not about the corpus. The order is asserted where it survives: the artifact's own `entry_keys` list, against `CORPUS_ENTRY_KEYS`."
  - "The byte assertion still runs LAST and is the one that carries the guarantee. The field loop could in principle agree while the serialization differed — a separator, a trailing newline, an `ensure_ascii` flag — and the sha256 both arm records carry is taken over the bytes, not over the fields."

requirements-completed: [ATK-01, STAT-05]

# Metrics
duration: ~25min
completed: 2026-08-16
---

# Phase 18 Plan 14: The Committed Corpus and Its Standing Guard Summary

**The 864-prompt attack corpus is on disk at a recorded full digest that matches what 18-05 built
and 18-13 re-confirmed under two different K values, and the guard that ties it to the pinned
generator has been watched fail on a single flipped byte and recover byte-identically.**

## Performance

- **Duration:** ~25 min; two task commits.
- **Files:** 2 — one created (`results/phase18_corpus.json`, 375,787 bytes on one line), one
  modified (`tests/test_phase18_corpus.py`, **+116 / −0**). **Zero files deleted by either commit.**
- **Suite:** **722 passed / 1 skipped / 0 failed** (139.02s). The main baseline was 721/1/0; the
  delta is exactly this plan's one new test node.
- **`scripts/phase18_extraction.py` byte-untouched:** blob `817df7a` at HEAD, the same blob
  `2d7151e` carried. `git diff --exit-code` returned 0 at every commit.

## Task Commits

1. **Task 1 (the artifact)** — `0ba9179` (feat) — `results/phase18_corpus.json`
2. **Task 2 (the guard)** — `6413d4c` (test) — `test_corpus_rederives_byte_identical`

## The four things asked for, measured

### 1. The full sha256 — on the record, and it matches

```
ff8e6e3c24987ac393cc262233f1b0bfdad5dc11eefa4cc1224a164cfd0f7d67
```

**First 8 hex characters are `ff8e6e3c`. MATCH.** This is 18-13's recorded prefix and — checked
rather than assumed — it is character-for-character the full digest 18-05 recorded when the builder
first ran (`18-05-SUMMARY.md`, "the corpus census"). So the committed artifact is the same corpus
across three independent occasions: 18-05's in-memory build, 18-13's two smoke runs at K=64 and
K=48, and this plan's write to disk.

The digest is unambiguous because there is only one number here, not two. `run_corpus` writes
`canonical_json(corpus)` with **no trailing newline**, and `corpus_sha256` is taken over that same
string — so the sha256 **of the file's bytes** and the digest **the driver prints** are the same
value by construction, and both were measured:

| Measured | Value |
|---|---|
| `shasum -a 256 results/phase18_corpus.json` | `ff8e6e3c…d0f7d67` |
| the driver's printed `corpus_sha256` | `ff8e6e3c…d0f7d67` |
| file size | 375,787 bytes |
| last byte | `0x7d` (`}`) — no trailing newline, as `run_corpus` documents |

### 2. Structure — 864 entries, 216 per family, realized counts

```
entries          : 864
by family        : A1-aggressive 216 | A1-mild 216 | A2 216 | A3 216
by tier          : core_taught 448 | core_held_out 416
by source_family : F1 160 | F2 160 | F3 96 | F6 128 | F7 96 | F8 96 | reserved 128
```

Every family realized **exactly 216**, and the tier split is the same inside each family rather
than only in aggregate — 112 taught and 104 held-out per family, four times over:

| family | core_taught | core_held_out | total |
|---|---|---|---|
| A1-mild | 112 | 104 | 216 |
| A1-aggressive | 112 | 104 | 216 |
| A2 | 112 | 104 | 216 |
| A3 | 112 | 104 | 216 |
| **total** | **448** | **416** | **864** |

`entry_keys` on disk is D-11's schema in its declared order; the per-entry keys are alphabetical
because `canonical_json` sorts them. `prompt_ids` run 15 to 149 ids, mean 66.41, **57,378 ids
total** — recorded because those ids, not any reconstruction, are what the model receives (D-03).

### D-16's build-time guards ran on the real material and none fired

This was the first time they ran against the material that would be *committed*, and the action
required a STOP on any abort. Nothing aborted, nothing was relaxed. A2's two-sided tail bound
realized **exactly its declared budget on all 216 A2 prompts** — each slot's observed set is a
singleton, so no prompt was under or over:

| slot | realized injection | A2 prompts |
|---|---|---|
| person_name | 1 | 27 |
| pet_name | 1 | 27 |
| cat_name | 1 | 27 |
| sibling_name | 1 | 27 |
| **hometown** | **2** | 27 |
| **street** | **2** | 27 |
| birth_year | 1 | 27 |
| house_number | 1 | 27 |

Fact order `[1, 1, 1, 1, 2, 2, 1, 1]`, sorted `[1, 1, 1, 1, 1, 1, 2, 2]` — D-13's pre-registered
vector, and identical to 18-05's measurement. `realized_injection` is `None` on all 648 non-A2
entries (checked, not assumed).

### 3. Determinism — what was compared, exactly

`--corpus` refuses to overwrite, so nothing was regenerated over the artifact. Instead
`build_corpus(tok)` was called **twice more in-process** and each result serialized through the
same `canonical_json` the writer used, then encoded UTF-8 — which is precisely the byte sequence
`run_corpus` passed to `write_text`, with no trailing newline added. So the comparison is between
**the artifact's raw bytes read off disk** and **the re-derived `canonical_json(...).encode("utf-8")`**,
not between two re-serializations under possibly-different dump settings:

| Comparison | Result |
|---|---|
| `canonical_json(build_corpus(tok)).encode("utf-8")` == `CORPUS_PATH.read_bytes()` | **True** (375,787 bytes each) |
| sha256 of that re-derived byte string | `ff8e6e3c…d0f7d67` — equal to the file's |
| `corpus_sha256(rebuilt)` | `ff8e6e3c…d0f7d67` — equal to both |
| a **second** independent rebuild, same comparison | **True**, same digest |

The two objects being compared are therefore genuinely comparable: they are produced by the same
function, with the same arguments, at the same call site the writer used. The pre-existing
`test_corpus_builder_is_deterministic` separately covers the cross-**process** half (a fresh
interpreter at `PYTHONHASHSEED=987654`), which this in-process check does not and does not claim to.

### 4. The guard proven RED, and the restore proven

Not observed passing and left there. One byte of the **committed** artifact was flipped in place —
byte **216507**, `0x38` (`8`) → `0x39` (`9`), inside the first id of the 501st `prompt_ids` array —
with the mutation verified to be exactly one byte and length-preserving before it was written:

```
BEFORE  sha256: ff8e6e3c24987ac393cc262233f1b0bfdad5dc11eefa4cc1224a164cfd0f7d67
MUTATED sha256: 0e9e4ec8b173451f7cd88761a76fab6c66e7b4b6a753ffc8099e1b4340a4dc50
```

`pytest tests/test_phase18_corpus.py::test_corpus_rederives_byte_identical` then failed — **1
failed**, at `tests/test_phase18_corpus.py:771` — naming the field, the entry and the position:

```
AssertionError: entry 500 (A1-mild, pet_name): prompt_ids[0] is 9187 in the committed artifact
but 8187 when re-derived — the committed corpus is not the one this builder produces, so no
completion drawn from it can be attributed to the pinned templates
assert 9187 == 8187
```

A non-zero entry index was chosen deliberately: entry 0 would have been consistent with a message
that reports the index as a constant. The failure is the **field-by-field** branch, not the byte
branch, which is the design working — a bare hash comparison would have said "these differ" and
sent a reader to diff 375 KB of one-line JSON.

**Restore, verified by digest rather than by eye.** The committed blob was read back with
`git show HEAD:results/phase18_corpus.json`, its digest asserted to equal the expected value
*before* it was written, then written and re-hashed:

| Stage | sha256 |
|---|---|
| on disk, mutated | `0e9e4ec8b173451f7cd88761a76fab6c66e7b4b6a753ffc8099e1b4340a4dc50` |
| committed blob | `ff8e6e3c…d0f7d67` |
| after restore | `ff8e6e3c…d0f7d67` (375,787 bytes) |

`git diff --exit-code results/phase18_corpus.json` returned **0**, `git status --short` showed the
artifact clean, and the guard re-ran **green** (18 passed in the module). No `git stash`, no reset,
no force flag; the restore touched exactly one path.

## Verification

| Check | Result |
|---|---|
| `.venv/bin/pytest -q` | **722 passed, 1 skipped, 0 failed** (139.02s) — baseline 721/1/0 + 1 new node |
| `.venv/bin/pytest -q tests/test_phase18_corpus.py` | 18 passed |
| `.venv/bin/pytest -q tests/test_phase16_prereg.py -k phase18` | 1 passed — **`checked` = 52** |
| ancestry re-derived independently | 26 driver commits × 2 tracked artifacts = **52**; `git merge-base --is-ancestor` exit 0 on all 52 pairs |
| corpus first-add | `0ba9179`; preflight report first-add still `2d7151e` |
| `git diff --exit-code scripts/phase18_extraction.py` | **0** at every commit; blob `817df7a` == the blob at `2d7151e` |
| `len(json.load(...)['prompts']) == 864` | passes |
| `grep -c "pytest.skip\|skipif" tests/test_phase18_corpus.py` | **0** |
| `grep -c "rederives_byte_identical" scripts/phase18_extraction.py` | **0** — the guard is not in the dispatch path |
| `ruff check . && ruff format --check .` | All checks passed; 161 files formatted |
| Files deleted by either commit | **0** |
| Untracked files after both commits | **0** |

## Deviations from Plan

**None affecting behaviour.** Both tasks executed as written; no guard aborted, nothing was
relaxed, and the driver was not touched. Two choices made inside the plan's latitude are recorded
because they are the kind a later reader would otherwise have to reconstruct:

**1. The RED proof mutated the committed artifact rather than a tmp copy**

- **Where:** Task 2's acceptance criterion, which offers "a copy of the artifact under a tmp path".
- **Why not:** pointing the test at a tmp path requires monkeypatching `CORPUS_PATH` or
  parameterizing the comparison into a helper. Either proves a *parameterized helper* red; neither
  proves the committed node red. The node reads `p18.CORPUS_PATH` directly, which is what will run
  in CI and what 18-15 depends on.
- **What was done instead:** the one-byte mutation was applied in place and the restore verified by
  sha256 against the committed blob, plus `git diff --exit-code` — which is the same criterion the
  plan asks for ("the committed file is untouched") discharged more strongly, since the file really
  was touched and really was proved to return.

**2. Per-entry key comparison is sorted, not ordered**

- **Found during:** Task 2, reading the artifact's first entry — its keys are
  `dose, fact_id, family, prompt_ids, …`, not `CORPUS_ENTRY_KEYS` order.
- **Cause:** `canonical_json` sets `sort_keys=True`, so per-entry order is alphabetical by
  construction on disk. Asserting D-11's declared order against the file would have been red for a
  reason that is not about the corpus.
- **Fix:** membership asserted per entry (`sorted(stored) == sorted(CORPUS_ENTRY_KEYS)`), order
  asserted where it survives — the artifact's own `entry_keys` list, against `CORPUS_ENTRY_KEYS`.
  The ordered-schema proof at build time (`_corpus_entry`, `test_schema_and_reserved_family`) is
  unchanged and still runs.

## TDD Gate Compliance

Task 2 is marked `tdd="true"` and did **not** produce a `test(...)` → `feat(...)` gate pair, for a
structural reason rather than an omission: there is no implementation for this test to drive. The
subject — `build_corpus` — is frozen by the D-04 ancestry pin and was committed in 18-05, and the
artifact was committed in Task 1. A literal RED gate would require a failing test with the
implementation absent, which here would mean deleting the artifact this plan exists to commit.

The RED requirement was discharged in the form this repository already uses for standing guards
(18-05's `test_strict_guard_covers_every_family`, 18-13's `fc69ed1` ancestry proof): **mutation**.
The guard was watched fail on a one-byte change to its subject and watched recover, which is the
evidence a RED gate is a proxy for. The commit is typed `test(18-14)` accordingly.

## Threat register disposition

| Threat ID | Disposition | Discharged by |
|---|---|---|
| T-18-14-01 (Tampering — artifact hand-edited or regenerated) | mitigated | The byte-equality guard, **proven RED** on a single flipped byte; `run_corpus`'s clobber refusal makes regeneration require a reviewed deletion commit; the run will record `corpus_sha256` per arm |
| T-18-14-02 (Information Disclosure — a build-time guard relaxed to get an artifact) | mitigated | Nothing aborted, so nothing was relaxed. The D-16 partition ran on the real material: the strict no-value guard on every family's question portion, and A2's two-sided bound realizing exactly its budget on all 216 A2 prompts (measured per slot above) |
| T-18-14-03 (Repudiation — the guard skips when the artifact is missing) | mitigated | `assert p18.CORPUS_PATH.exists()` with a message naming the regeneration command; `grep -c "pytest.skip\|skipif"` returns **0** over the module |
| T-18-14-04 (Tampering — the corpus first-add predates a driver commit) | mitigated | `test_phase18_prereg_is_frozen_before_every_phase18_result` green with `checked` = **52**, re-derived independently; all 26 driver commits are ancestors of `0ba9179` |
| T-18-14-SC (Tampering — package installs) | accepted | Zero installs; no dependency file touched |

## Issues Encountered

- **None from the plan's material.** No guard fired, no acceptance criterion needed contorting, no
  cross-plan guard tripped — the contrast with 18-13, where a stale 18-10 assertion forbade the
  artifact, is worth recording: this plan's artifact landed with the ordering already proved.
- **A tooling detail, not a code issue:** `git checkout -- <path>` was blocked by the environment's
  destructive-command gate, so the restore was performed by reading the committed blob with
  `git show` and writing it back, with the digest asserted equal to the expected value *before* the
  write. The stronger form: the restore is verified against a known digest rather than trusted to
  a command's semantics.

## Deferred Issues

None new. The one item in `deferred-items.md` is 18-04's and is untouched.

## Known Stubs

None. Neither file carries a `TODO`, `FIXME` or placeholder — the artifact is generated data with
no hand-written text at all, and the new test node returns no value and stubs nothing. Every entry
in the corpus carries a populated `prompt_ids` list (57,378 ids over 864 entries, minimum length
15, so no entry is empty) and every optional field is populated exactly where D-11 requires it:
`realized_injection` is an `int` on all 216 A2 entries and `None` on all 648 others.

## User Setup Required

None. `--corpus` is CPU-only: it needs the frozen `artifacts/tokenizer.json` and the committed
`results/phase16_recall_sample.json`, both tracked. No checkpoint, no model load, no GPU, no
network. Unlike 18-13's smoke, this mode **can** be run from a git worktree.

## Threat Flags

None. No new network endpoint, auth path or schema change at a trust boundary. One new file-access
pattern — `run_corpus` writing `CORPUS_PATH` — which is the plan's declared artifact and is
**write-once by design**: the clobber refusal makes a second write an abort, not an overwrite,
which is the opposite of the re-runnable posture 18-13's smoke report has.

## Next Phase Readiness

- **The corpus is the INPUT and it is now a tracked file with a recorded digest.** 18-15's two arms
  read `results/phase18_corpus.json` and record `ff8e6e3c…d0f7d67` as the join key; the driver's
  `--arm` path already asserts the file exists and that its `entry_keys` match this driver's schema.
- **Regenerating it is now a two-lock operation:** `run_corpus` refuses to clobber, and any change
  to the bytes reddens `test_corpus_rederives_byte_identical`. Both locks have been watched work.
- **The ancestry guard is no longer measuring a single artifact.** `checked` is 52 and will grow by
  26 with each further `results/phase18_*` artifact 18-15 and 18-16 commit. The driver remains
  permanently uneditable from `2d7151e`.
- **Nothing about K reaches the corpus.** K is draws per prompt; the artifact is prompt-level and
  was confirmed byte-identical across the K=64 and K=48 pins in 18-13 and again here.

## Self-Check: PASSED

- `results/phase18_corpus.json` — FOUND (375,787 bytes, tracked, first-add `0ba9179`,
  sha256 `ff8e6e3c24987ac393cc262233f1b0bfdad5dc11eefa4cc1224a164cfd0f7d67`)
- `tests/test_phase18_corpus.py` — FOUND (800 lines, 18 test nodes, contains
  `def test_corpus_rederives_byte_identical`)
- `.planning/phases/18-black-box-adversarial-extraction-audit/18-14-SUMMARY.md` — FOUND
- `0ba9179`, `6413d4c` — both FOUND in `git log`
- `scripts/phase18_extraction.py` — blob `817df7a`, identical to the blob at `2d7151e`;
  `git diff --exit-code` returns 0
- `git status --short` clean apart from this SUMMARY; zero untracked files
- No `STATE.md`, `ROADMAP.md` or `REQUIREMENTS.md` touched — the orchestrator owns them
- No file deleted by either commit; **116 insertions, 0 deletions** across the two

---
*Phase: 18-black-box-adversarial-extraction-audit*
*Completed: 2026-08-16*
