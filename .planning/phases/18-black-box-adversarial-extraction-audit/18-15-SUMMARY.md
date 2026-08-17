---
phase: 18-black-box-adversarial-extraction-audit
plan: 15
subsystem: evaluation
tags: [measurement, paired-arms, negative-control, positive-control, provenance, decode-tolerance]

# Dependency graph
requires:
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-14's `0ba9179` — the committed `results/phase18_corpus.json` both arms dispatched, digest `ff8e6e3c…d0f7d67`"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-10's `--arm` mode, `run_arm`, `ARM_RECORD_PATHS` and the clobber refusal — the only sanctioned writer of either record"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-09's `family_zero_matches` and `parse_phase14_taught_rows` — the committed row-for-row D-01 comparison"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-13's `results/phase18_preflight_report.md` — the measured per-shape rates the realized wall clock is checked against"
  - phase: 14-teach-then-recall-demo
    provides: "results/phase14_recall_report.md — the 112 committed `core_taught` rows D-01 reproduces against"
provides:
  - "`results/phase18_arm_adapter-on.json` — 976 prompts / 42,480 draws with full provenance, corpus join key and per-slot NLL + exposure rank"
  - "`results/phase18_arm_adapter-off.json` — the ATK-02 negative control at the identical budget, adapter gated off through one loader"
  - "The D-01 positive control CONFIRMED: 0 of 112 per-question mismatches, so a privacy statement is admissible at all"
  - "`_decode_tolerant` (`c71bade`) exercised under real load: zero UnicodeDecodeError crashes across 84,960 draws"
affects: [18-16]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A paired contrast whose pairing is VERIFIED on the recorded artifacts rather than argued from the code that wrote them — five fields, checked after the fact"
    - "A commit freeze held by discipline where no guard enforces it, and the absence of that guard recorded rather than left implied"
    - "A crash COUNT distinguished from an event RATE when the run is deterministic: zero crashes after a fix means the fix held, not that the condition vanished"

# Metrics
duration: ~8.9h wall (two arms, sequential)
completed: 2026-08-17
---

# Phase 18 Plan 15: The Measurement Summary

**Both arms ran at the same budget in two separate processes on one unmoved tree, the pairing was
verified on all five fields the plan names rather than inferred, and the D-01 positive control
reproduced exactly — 0 of 112 per-question mismatches — so what 18-16 reads is interpretable.**

## Performance

- **Duration:** ~8.9 h wall across two sequential arms; 246.5 min (on) + 270.1 min (off) = **8.6 h
  of generation** against the pre-flight's projected **9.54 h**.
- **Realized throughput:** **172.3** draws/min (on) and **157.3** draws/min (off), both inside the
  pre-flight's measured **134.5–183.2** range. The projection was conservative by construction: it
  applied the slowest measured shape to family zero, and said so.
- **Files:** 2 created — `results/phase18_arm_adapter-on.json` (2,882,782 bytes) and
  `results/phase18_arm_adapter-off.json` (3,495,840 bytes). **Zero files deleted.**
- **Suite:** **726 passed / 1 skipped / 0 failed** (142.96s), re-run after the commit with both
  artifacts tracked. Unchanged before and after — this plan added no test node.
- **`scripts/phase18_extraction.py` byte-untouched:** blob `817df7a` at HEAD, the same blob
  `2d7151e` carried. `git diff --exit-code` on the driver and the corpus returned 0 across **both**
  arms, not just once.

## Task Commits

1. **Tasks 1 + 2 (both arm records)** — `9a923d6` (feat) — `results/phase18_arm_adapter-on.json`,
   `results/phase18_arm_adapter-off.json`
2. **Prerequisite, outside this plan's scope** — `c71bade` (fix) — `_decode_tolerant`, the decode
   defect that killed the first attempt at Task 1. See Deviations.

The two records are in **one** commit deliberately. Committing the on-arm record before the off arm
ran would have moved HEAD, and the off arm would then have recorded a different `git_sha`.

## Task 3 — the positive control, verbatim

`family_zero_matches` called on the recorded adapter-on arm against
`results/phase14_recall_report.md`, via the committed `score_records` → `parse_phase14_taught_rows`
path. The triple as returned:

```
(matches, mismatching_seed_indices, derived_rate) =
(True, [], {'label': "DERIVED CONSEQUENCE of the row-for-row comparison, never an independent
assertion (D-01). …", 'scoping_note': "…", 'successes': 496, 'n_draws': 1008,
'n_questions': 112})
```

- **`matches` = `True`**
- **`mismatching_seed_indices` = `[]`** — empty; **0 of 112** questions diverged
- **`n_questions` = 112**, matching the 112 reference rows the parse returned

### The rate, as a consequence and not an assertion

**496 / 1008 = 0.492063.**

Numerator **496** successes, denominator **1008** draws (112 questions × 9 draws). This pair is
recorded because the 112-entry per-question vector matched row for row, and for no other reason.
Nothing in this phase asserted it, compared against it, or gated on it.

`derived_rate` is a dict rather than a float precisely so that provenance travels with the number:
its own `label` field states that it is a *"DERIVED CONSEQUENCE of the row-for-row comparison, never
an independent assertion"*, and gives the reason the weaker check is inadmissible — **a harness
asserting the totals would return PASS on a run that moved one hit from one question to another,
diverging on two of its 112 questions while summing to the identical numerator.** That failure mode
is committed as a test, not merely described.

The same `label` refuses a band: ATK-03/SC2 asks for reproduction *within a band*, and the quantity
reproduced **exactly** — 0 of 112 mismatches — so putting a width around it would discard measured
precision to buy a number nothing derives from.

`scoping_note` records the trap that was not fallen into: PERS-05's seeding defect is scoped to
`run_fairness_control`, **not** the scored adapter-on path this control reproduces. Reading
STATE.md's "does not reproduce bit-for-bit" as covering the taught headline manufactures a phantom
delta of 0.0048 against the *pooled* taught split (140 = 112 core + 28 soft) — a quantity Phase 14
never published. The comparison here is against the **112 core** taught rows, the split the report
prints per question.

**Consequence:** the harness is not declared broken, and a privacy statement is admissible. Had
`matches` been `False`, this summary would read HARNESS BROKEN and the phase would stop here.

## Task 2 — ATK-02 pairing, verified on the artifacts

Checked on the recorded files after both runs, not inferred from the code that wrote them:

| # | Field | Result |
|---|-------|--------|
| 1 | `corpus_sha256` | AGREE — `ff8e6e3c24987ac3…` |
| 2 | `forbid_ids_sha256` | AGREE — `79b55770f4dcfa94…` |
| 3 | prompt count | AGREE — **976** (864 attack + 112 family zero) |
| 4 | every `seed_index` | AGREE — all **976** positions identical, in order |
| 5 | every draw count | AGREE — **42,480** draws per arm |

Around those five:

- **`adapter_enabled` True / False** — the adapter gate is the only difference between the arms.
- **pids `89185` / `9267` — distinct.** No single process ran both, which `run_report` proves
  independently by refusing equal pids.
- **`git_sha` identical — `c71bade` in both records.** Recorded here as **discipline, not
  construction**: `run_report` cross-checks `corpus_sha256`, `forbid_ids_sha256`, `k`,
  `corpus_entries` and pid inequality, but it does **not** compare `git_sha`. A commit landing
  between the arms would have published two SHAs in the provenance table with nothing refusing it.
  The freeze was held manually for the full 8.6 h.
- **Every zero-extraction target is interpretable (ATK-04):** 8 slots × 3 frames (`ans1`,
  `f3_bare`, `f4_reversed`) × 2 reductions (`sum`, `mean`) = **48 NLL values, all finite**, no
  `None` and no NaN; **8** exposure ranks present, all `1`. Per-slot `exposure_bits` equals
  `ceiling_bits` on all 8 slots.

## Verification

- `.venv/bin/pytest -q` — **726 passed, 1 skipped** (142.96s), run after `9a923d6` with both
  artifacts tracked.
- `.venv/bin/pytest -q tests/test_phase16_prereg.py` — **4 passed**, re-run *after* the commit so
  the "all `results/phase18_*` artifacts tracked" clause is verified rather than inherited from the
  untracked-file run.
- `git ls-files` lists both records — tracked.
- `git diff --exit-code scripts/phase18_extraction.py results/phase18_corpus.json` — **0**, across
  both arms.
- `git status --short` — empty after the commit.

## Deviations from Plan

**The first attempt at Task 1 died and the fix is a separate commit outside this plan.**

The adapter-on arm launched at `17d46ef` crashed 6m37s in:

```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0x9d in position 3
  src/personacore/tokenizer/bpe.py:209 <- scripts/phase14_recall.py:661 (draw_all)
```

Root cause was **provenance, not only behaviour**, and is recorded in full in
`.planning/debug/draw-all-utf8-decode-crash.md` and the `c71bade` commit message. In short: Phase 14
explicitly required this harness to reuse `generate_text`'s tolerant cumulative decode and
explicitly forbade a second decode path (`14-RESEARCH.md:690` Gap G1, `14-PATTERNS.md:92`).
`generate_text_from_ids` **was** added with the tolerant decode (`generation/text.py:119`);
`draw_all` never used it and grew its own strict `tok.decode(gen_ids)`. That is the D-18-forbidden
second path, shipped in `121efb8`, drawn through unreviewed by phases 14, 16, 17 and 18.

`undecodable_ids_mask` could not have prevented it: it masks ids **absent from `vocab`** (stopping
`ValueError: unknown token id`), while **129 of the 547** sampleable ids are bare bytes 0x80–0xFF —
the pieces multi-byte glyphs are built from. Masking them would make every non-ASCII character
ungeneratable, which is why D-06 tolerates the truncation instead of forbidding it.

**Before this plan's arms were relaunched, the fix was proven not to move D-01:**

- generation untouched — 37 insertions / **2 deletions**, both deletions the
  `completions.append(tok.decode(gen_ids))` call sites; `_complete`, seeds, forbid mask and stop ids
  byte-identical;
- `_decode_tolerant` == `tok.decode` on **64,691 / 64,691** clean-decoding sequences, 0 divergences;
- **the 112 `core_taught` rows re-derived literally on the adapter with the fix applied** —
  112/112 rows identical, 496/1008 both sides, 0 mismatches, written to a temp path so
  `results/phase14_recall_report.md` stayed untouched (`git status --short results/` empty).

## Decode tolerance under real load — a count, not a rate

**Zero `UnicodeDecodeError` crashes across 84,960 real draws** (42,480 per arm).

That is a count of **crashes**, not of fragment-terminated generations, and the distinction is
load-bearing. The run is deterministic — each draw samples at `question_seed(index) + s` — so the
relaunched arm re-dispatched the very draw that killed the pre-fix arm. D-01 reproducing exactly
from a *different process* is direct evidence that generation is reproducible across processes on
this device. The truncated-glyph draw therefore **recurred and was absorbed** by `_decode_tolerant`
rather than avoided. Zero crashes means the fix held, not that the condition is absent.

**How often the tolerant branch fired inside these two records is UNMEASURED.** The driver does not
instrument it, and adding instrumentation between the arms would have broken the pairing above.
What *is* measured is the instrumented dry-run on the adapter-on path before relaunch:

| Family | Draws | Undecodable |
|--------|-------|-------------|
| A1-mild | 480 | 0 |
| A1-aggressive | 480 | 0 |
| A2 | 480 | 0 |
| A3 | 480 | 0 |
| **total** | **1,920** | **0** |

Point estimate **0.00000**; **95% one-sided Wilson upper bound 0.00141** via the committed
`erasure_gate.wilson_upper_bound`. At that bound, up to **~117** of the 82,944 attack draws across
both arms could carry a dropped trailing fragment. The true value in these records is not known,
and the sample evidently did not include the offending prompt. The denominator is **attack-family
draws only** — family zero's 2,016 bare-prompt draws across both arms are a different prompt shape
and are not covered by it.

## Threat register disposition

| Threat ID | Disposition | Evidence |
|-----------|-------------|----------|
| T-18-15-01 | mitigated | Five-field pairing verified on the artifacts; `git diff --exit-code` 0 across both arms; identical `git_sha` |
| T-18-15-02 | mitigated | No rerun occurred after either arm completed. The clobber refusal was never invoked because no record pre-existed |
| T-18-15-03 | mitigated | The checkpoint was read with `matches` True; no tolerance parameter exists to reach for, and none was added |
| T-18-15-04 | mitigated | 48/48 NLL values finite, 8/8 ranks present — asserted, not sampled |
| T-18-15-05 | mitigated | One loader plus `adapter_disabled`; `adapter_enabled` True/False recorded per arm and cross-checked by `run_report` |
| T-18-15-SC | accepted | Zero installs |

## Issues Encountered

The decode crash above, and one process-level lesson worth keeping: **`run_arm` prints exactly two
lines** — the preflight summary and the final `wrote …`. A ~4 h silence is the expected behaviour,
not a hang, and the crashing draw's index is therefore **not recoverable from the log**. The first
crash could only be localised to "within the first ~6.6 min of corpus order".

## Deferred Issues

- **Sibling decode sites with the same latent exposure, deliberately not fixed** (out of `c71bade`'s
  scope, none blocking this phase): `scripts/phase14_recall.py:1423-1424`,
  `scripts/phase14_factset_gate.py:95,107`, `scripts/make_transcripts.py:155,159`,
  `scripts/make_retention_samples.py:188`. All decode *generated* ids strictly. Enumerated in
  `.planning/debug/draw-all-utf8-decode-crash.md`.
- **`draw_all`'s docstring still says "Phase 18 passes `n_samples=K-1` so 1 greedy + 63 seeded
  equals its K=64 attack budget"** — stale since 18-13 reduced K to 48. The code reads the constant;
  only the prose is wrong.
- `make lint` remains red from **DEF-17-01** (pre-existing). `.venv/bin/ruff check .` and
  `ruff format --check .` are clean on all 162 files.

## Known Stubs

None.

## User Setup Required

None for 18-16 — `run_report` is CPU-only and reads the two tracked records. Note that both arms
required the **local M3/MPS** path with a loaded adapter and ~4.3 h each; neither can be run from a
git worktree, and both need the detached-run protection (`caffeinate -ims`, PID 58309 ppid 1, plus
`nohup … & disown` verified at ppid 1) that covered them here.

## Threat Flags

None new. Two new file-access patterns, both the plan's declared artifacts, both **write-once by
design** via the clobber refusal.

## Next Phase Readiness

- **The two records exist, are tracked, and are paired.** `run_report` will find them, and its own
  cross-checks (corpus sha256, forbid digest, `k`, `corpus_entries`, pid inequality, per-arm
  `adapter_enabled`, the D-18 A2 realized-injection identity) will re-prove the pairing from its
  side rather than trusting this summary.
- **The positive control is confirmed, so a null result is admissible rather than uninterpretable.**
  Every zero carries a finite NLL and an exposure rank, which is what
  `null_result_is_admissible` requires to avoid forcing INCONCLUSIVE.
- **`assert_extraction_report_not_clobbered` is armed** and `results/phase18_extraction_report.md`
  does not exist. The report is write-once with no force flag.
- **The commit freeze is over.** Both arms are recorded and committed together; nothing further is
  held by it.
- **`run_report` must not be handed a `git_sha` expectation this phase cannot meet.** Both records
  carry `c71bade`, which is *not* the SHA the pre-flight report (`99716e08`) or the corpus commit
  (`0ba9179`) carry. That is correct and expected — the driver blob is identical (`817df7a`) — but
  any future guard comparing SHAs across `results/phase18_*` artifacts would fire on it.

## Self-Check: PASSED

- `results/phase18_arm_adapter-on.json` — FOUND (2,882,782 bytes, tracked, first-add `9a923d6`,
  976 draw entries, `corpus_sha256` `ff8e6e3c…`, `git_sha` `c71bade`, pid 89185, 246.5 min)
- `results/phase18_arm_adapter-off.json` — FOUND (3,495,840 bytes, tracked, first-add `9a923d6`,
  976 draw entries, `adapter_enabled` false, pid 9267, 270.1 min)
- `.planning/phases/18-black-box-adversarial-extraction-audit/18-15-SUMMARY.md` — FOUND
- `9a923d6`, `c71bade` — both FOUND in `git log`
- `scripts/phase18_extraction.py` — blob `817df7a`, identical to the blob at `2d7151e`
- D-01 triple recorded verbatim, `matches` True, mismatch list empty, rate recorded as a consequence
  with numerator 496 and denominator 1008
- Suite **726 passed / 1 skipped**, verified after the commit
