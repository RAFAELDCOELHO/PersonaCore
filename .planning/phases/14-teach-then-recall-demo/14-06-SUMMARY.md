---
phase: 14
plan: 06
subsystem: scored recall harness (model load, clean-room proof, transcripts)
tags: [DEMO-05, DEMO-06, D-08, D-10, D-13, D-18, D-19, D-22, clean-room, lora, weights-only]
requires:
  - personacore.checkpoint.load_slim
  - personacore.checkpoint.load_adapter
  - personacore.lora.inject_lora
  - personacore.lora.load_adapter_weights
  - personacore.lora.adapter_disabled
  - personacore.generation.collect
  - personacore.generation.undecodable_ids_mask
  - personacore.dialogue.build_recall_prompt
  - personacore.preflight.preflight_device
  - personacore.provenance.git_sha
  - scripts/phase14_recall.py (plan 14-05 pre-registration + D-10 scoring rules)
  - scripts/phase14_factset.py (plan 14-04 locked fact set + template families)
provides:
  - scripts/phase14_recall.load_adapted_model
  - scripts/phase14_recall._complete
  - scripts/phase14_recall.complete_question
  - scripts/phase14_recall.echo_provenance
  - scripts/phase14_recall.RecallItem
  - scripts/phase14_recall.build_question_sets
  - scripts/phase14_recall.run_scored_recall
  - scripts/phase14_recall.run_closed_book_control
  - scripts/phase14_recall.write_transcripts
  - scripts/phase14_recall.main
  - scripts/phase14_recall.SAMPLE_TEMPERATURE / SAMPLE_TOP_P
  - scripts/phase14_recall.CORE_TAUGHT_TIER / CORE_HELDOUT_TIER / CLOSED_BOOK_TIER / SOFT_TIER
  - scripts/phase14_recall.CONTEXT_DUMP_SOURCE
affects:
  - "plan 14-07 (teach_persona must export checkpoints/persona_adapter.pt via export_adapter)"
  - "plan 14-09 (rewrites TAUGHT_FAMILY_IDS/HELDOUT_FAMILY_IDS — the self-naming filter is allocation-agnostic by design)"
  - "plan 14-10 (D-11 controls + results/phase14_recall_report.md read the tier records and provenance lines)"
  - "plan 14-11 (executes the run this plan ships)"
  - scripts/personalize_demo.py (plan 14-08 — now inherits a torch import from this module)
tech-stack:
  added: []
  patterns:
    - "question sets carried as fact-BOUND RecallItems, never parallel question/value sequences"
    - "mechanical self-naming filter (contains_value) instead of a hardcoded family denylist"
    - "context dump recorded BEFORE the model is called, so committed evidence is not a reconstruction"
    - "closed-book control = same process, same weights, same prompts, same per-question seeds — only the LoRA flags differ"
    - "raw-evidence file owns no verdict: no tier rate, ranking, or threshold comparison"
key-files:
  created: []
  modified:
    - scripts/phase14_recall.py
    - tests/test_phase14_scoring.py
key-decisions:
  - "Taught questions that name their own fact value (F4 reversed-direction, F5 yes/no verification — 80 of 220) are excluded from SCORING by a mechanical contains_value filter, reported in the transcripts, and never fed to the model"
  - "The closed-book control re-runs on the FULL final question set (all 270 questions), not on the reserved gate probes alone (D-08)"
  - "Constructed held-out items are proven set-equal to phase14_factset.heldout_questions() rather than replacing it — the harness needs the fact binding the flat tuple drops"
  - "Per-question seed index is the question's position in ITS tier, so the closed-book control replays identical streams and the arms are paired"
  - "SAMPLE_TEMPERATURE=0.8 / SAMPLE_TOP_P=0.95 carried over verbatim from the shipped Phase-12 transcripts rather than re-tuned"
patterns-established:
  - "Harness-local keys attached to the loaded adapter artifact (loaded_base_fingerprint, fingerprint_warnings) instead of a wider return tuple; never re-exported"
  - "Multi-line completions quoted line-by-line so 'verbatim' survives markdown"
requirements-completed: [DEMO-05, DEMO-06]
duration: 78min
completed: 2026-08-02
---

# Phase 14 Plan 06: Scored Recall Harness Summary

**The executable half of `scripts/phase14_recall.py`: `weights_only=True` load-before-inject model
loading, a process-boundary provenance echo, a 270-question four-tier scored loop that dumps every
prompt's ids before the model is called and aborts on any value in a prompt, and an unfiltered
transcripts writer.**

## Performance

- **Duration:** ~78 min
- **Tasks:** 3
- **Files modified:** 2
- **Test suite:** 338 passed, 4 skipped (was 337/4); `ruff check .` + `ruff format --check .` clean

## Accomplishments

- `load_adapted_model` loads the shareable base and adapter through the `load_slim` / `load_adapter`
  `weights_only=True` choke points in the **load-before-inject** order, proves `inject_lora` wrapped
  `6 * n_layer` projections, and **captures rather than swallows** the D-02 fingerprint-mismatch
  `UserWarning` so plan 14-10's report can state it. `grep -c "torch.load(" scripts/phase14_recall.py`
  returns **0**.
- `run_scored_recall` records each question's exact prompt ids via `render_context_dump` **before**
  `complete_question` is called, then runs `assert_no_value_in_prompt` — a `SystemExit`, not a warning.
  Verified: all **270** scored questions clear the clean-room proof at both the string and id level.
- `run_closed_book_control` re-runs the full question set under `adapter_disabled(model)` — same
  process, same weights, same prompts, same per-question seeds, only the 36 boolean flags flipped.
- `write_transcripts` emits four labelled tiers (core taught, core held-out, closed-book control,
  soft tier) with every completion verbatim behind a "failures included and unfiltered" opener, one
  `write_text`, no aggregation or ranking.

## Task Commits

1. **Task 1: Model load, fresh-process provenance, completion helper** — `65fc1a5` (feat)
2. **Task 2: Scored recall loop with context dumps and the clean-room proof** — `23922a7` (feat)
3. **Task 3: `results/phase14_recall_transcripts.md` writer** — `1649df4` (feat)

## Files Created/Modified

- `scripts/phase14_recall.py` — +~460 lines: the harness half. Module-level `import torch` and the
  `personacore` seams added after the pre-existing `PYTORCH_ENABLE_MPS_FALLBACK` preamble (14-05
  deliberately deferred this import to here). The LAZY-IMPORT RULE is intact: `phase14_factset` is
  imported inside `build_question_sets`, `run_scored_recall`, `echo_provenance`, `write_transcripts`,
  and `main()` — never at module level.
- `tests/test_phase14_scoring.py` — one added CPU-only test pinning the two contracts
  `build_question_sets` exists to hold (see Deviation 1).

## Measured Shape of the Run (CPU-only, derived from the committed fact set)

| Tier | Questions | Completions (1 greedy + 8 seeded) |
|---|---|---|
| core taught | 112 | 1,008 |
| core held-out | 104 (40 of them reserved D-08 probes) | 936 |
| soft taught + held-out | 54 | 486 |
| closed-book control (all of the above) | 270 | 2,430 |
| **total** | **270 unique** | **4,860** |

Excluded from scoring by the self-naming filter: **80** taught phrasings (64 core + 16 soft), all
from families `F4` and `F5`.

## Decisions Made

- **The excluded phrasings are named in the transcripts, not dropped silently.** Each tier section
  lists every excluded `(family, fact, split, question)` with the reason, so the record shows what
  was taught but not scored.
- **`echo_provenance` returns its lines as well as printing them**, so the transcripts embed the
  identical block rather than a re-rendered one — the same one-source discipline D-18 applies to the
  context dump.
- **No subprocess per question** (14-RESEARCH Pattern 8). One fresh process, each question an
  independent `build_recall_prompt` id sequence; the pid + wall clock + adapter SHA-256 are what make
  the boundary auditable.
- **`assert_values_fit` is called once in `main()`** immediately after the question sets are built and
  before any `run_*` call, matching the plan's "done once at the top of `main()`".

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Taught families `F4`/`F5` name the fact value inside the question, which would have aborted the run**

- **Found during:** Task 2 (question-set construction)
- **Issue:** The plan says taught questions are "every question `render_family` produces for every id
  in `TAUGHT_FAMILY_IDS`". Measured against the committed fact set, **80 of those 220 questions
  contain their own fact's value**: `F5` is yes/no verification (`is your name quillon?`) and `F4` is
  the D-22 reversed direction (`who is quillon?`) — naming the value is the *definition* of both
  frames, per `phase14_factset._render_family`'s own docstring. Feeding one to
  `assert_no_value_in_prompt` raises `SystemExit`, so the run would have aborted on its first
  taught question; suppressing the abort instead would have scored a question that already contains
  the answer, which measures copying from context, not memory in the weights — falsifying the claim
  at the moment it is demonstrated (PITFALLS-11).
- **Fix:** `build_question_sets` drops any question satisfying `contains_value(question, fact.value)`,
  returns the dropped set, and `run_scored_recall` reports it in the transcripts. The filter is
  **mechanical and allocation-agnostic** on purpose — hardcoding "skip F4 and F5" would silently
  break when plan 14-09 rewrites `TAUGHT_FAMILY_IDS` from the calibration run. A per-fact `_prove`
  guarantees no fact loses all its taught coverage, and `assert_no_value_in_prompt` stays armed over
  **all** locked values so a genuine leak still aborts.
- **Files modified:** `scripts/phase14_recall.py`, `tests/test_phase14_scoring.py`
- **Verification:** All 270 surviving questions pass `assert_no_value_in_prompt`; the excluded set is
  exactly `{F4, F5}` (80 items); `test_scored_question_sets_are_value_free_and_match_the_committed_seam`
  pins both properties CPU-only.
- **Committed in:** `23922a7` (Task 2), test in `1649df4` (Task 3)

**2. [Rule 3 - Blocking] Held-out set built fact-bound instead of from the flat `heldout_questions()` tuple**

- **Found during:** Task 2
- **Issue:** The plan specifies held-out questions come from `heldout_questions()`, but that function
  returns a deduplicated flat tuple of strings with the fact binding dropped. `score_question` needs
  the value to search for, so a bare string cannot be scored.
- **Fix:** `build_question_sets` reconstructs the held-out items fact-bound (held-out families +
  `RESERVED_HELDOUT_PROBES`, the latter flagged `reserved=True`), and `main()` `_prove`s the
  constructed question set is **set-equal** to `set(heldout_questions())`. The committed seam becomes
  the contract rather than the source, so the two constructions cannot drift.
- **Files modified:** `scripts/phase14_recall.py`
- **Verification:** Set equality holds against the committed fact set; pinned by the added test.
- **Committed in:** `23922a7` (Task 2)

**3. [Rule 3 - Blocking] Signature adjustments the scoring contract forces**

- **Found during:** Task 2
- **Issue:** The plan's `run_scored_recall(..., facts, *, tier_label)` and
  `run_closed_book_control(..., questions, values)` cannot score: neither shape carries the
  question-to-fact binding, and `values` duplicates material `run_scored_recall` must lazily import
  anyway to build the D-10 contradiction lexicon.
- **Fix:** Both take `items` — a tuple of `RecallItem(fact, question, split, reserved)` —
  and `run_scored_recall` gains `excluded=()` so the Deviation-1 exclusion list travels into its tier
  record instead of being poked in from `main()`. `values` is dropped; the values come from the same
  lazy `phase14_factset` import that already builds the lexicon inside the function.
- **Files modified:** `scripts/phase14_recall.py`
- **Verification:** Plan verify snippets pass unchanged (they inspect behavior, not parameter names).
- **Committed in:** `23922a7` (Task 2)

**4. [Rule 2 - Missing Critical] `SAMPLE_TEMPERATURE` / `SAMPLE_TOP_P` committed as named constants**

- **Found during:** Task 1
- **Issue:** The plan specifies `N_SEEDED_SAMPLES` seeded draws but never says what a seeded draw
  *is*. Decode settings materially move the measured recall rate, and an unnamed inline literal is
  the same category of error as a threshold chosen after seeing results.
- **Fix:** Named constants beside `N_SEEDED_SAMPLES`, carrying the shipped Phase-12 transcript
  values (`0.8` / `0.95`) verbatim rather than re-tuned, with the rationale in the comment. They are
  echoed in the provenance block and in `## Measured Proxies`.
- **Files modified:** `scripts/phase14_recall.py`
- **Verification:** `test_preregistration_constants` still passes; both values appear in the
  provenance echo and the transcripts header.
- **Committed in:** `65fc1a5` (Task 1)

---

**Total deviations:** 4 auto-fixed (1 bug, 2 blocking, 1 missing critical)
**Impact on plan:** Deviation 1 is load-bearing — without it the plan as written aborts on its first
taught question. Deviations 2 and 3 are the mechanical consequence of scoring needing a value per
question. No scope creep: no new dependency, no new file, no change to any pre-registered constant or
rule from plan 14-05.

## Issues Encountered

- Two plan `<verify>` snippets use `src.index('X') < src.index('Y')` on function source, which sees
  **comment and docstring** occurrences too. Both `load_adapted_model` and `write_transcripts` needed
  a comment reworded (`inject_lora` → "Injection"; ``ONE `write_text` `` → "ONE write") so the
  ordering/count checks measure code rather than prose. No behavior change.

## Known Stubs

None. Every function this plan ships is fully wired; `main()` runs end to end. The two remaining
placeholders in the file are pre-existing and belong to plan 14-10 (the three D-11 controls and
`results/phase14_recall_report.md`), marked in their own section comment.

## Threat Flags

None. The plan's `<threat_model>` surface is unchanged: no new network endpoint, no new
deserialization path (both artifacts go through the existing `weights_only=True` choke points), no
schema change, no new package.

## Next Phase Readiness

- **Blocked on plan 14-07:** the harness requires `checkpoints/persona_adapter.pt`, which
  `scripts/teach_persona.py` does not yet export. A missing adapter produces a `SystemExit` naming
  `scripts/teach_persona.py`, as specified.
- **Plan 14-09** rewrites the taught/held-out family allocation. The self-naming filter and the
  `heldout_questions()` set-equality proof are both allocation-agnostic, so no change is needed here —
  but if 14-09 makes every taught family for some slot value-naming, the per-fact `_prove` fires
  loudly rather than silently shrinking the taught tier.
- **Plan 14-10** consumes the tier records (`k`, `n`, `by_split`, `contradictions`, `hedging`,
  `n_stopped`, `excluded`) and `echo_provenance`'s returned lines, plus
  `adapter_artifact["fingerprint_warnings"]` for the D-02 statement.
- **Plan 14-11** executes the run: ~4,860 completions at `max_new_tokens=48` on the M3, single fresh
  process.

## Self-Check: PASSED

- `scripts/phase14_recall.py` — FOUND (contains `def run_scored_recall`, `def write_transcripts`,
  `TRANSCRIPTS_PATH.write_text`, `load_slim(`, `load_adapter_weights(`)
- `tests/test_phase14_scoring.py` — FOUND (27 tests, all passing)
- Commits `65fc1a5`, `23922a7`, `1649df4` — FOUND on `worktree-agent-a8d50420ea9d3d19a`
- Full suite: 338 passed, 4 skipped. `ruff check .` and `ruff format --check .`: clean.

---
*Phase: 14-teach-then-recall-demo*
*Completed: 2026-08-02*
