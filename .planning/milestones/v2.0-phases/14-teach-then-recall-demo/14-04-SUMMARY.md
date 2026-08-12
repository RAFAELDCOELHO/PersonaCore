---
phase: 14
plan: 04
subsystem: teaching grammar + masked teaching bins
tags: [D-01, D-08, D-13, D-14, D-15, D-21, D-22, W-04, S2, DEMO-05, DEMO-06]
requires:
  - scripts/phase14_factset.LOCKED_FACTS
  - scripts/phase14_factset.SOFT_TIER_FACTS
  - scripts/phase14_factset.CALIBRATION_FACTS
  - scripts/phase14_factset.REGISTER_ARM_FACTS
  - scripts/phase14_factset.RESERVED_HELDOUT_PROBES
  - scripts/phase14_factset.normalize_for_match
  - personacore.dialogue.encode_dialogue
  - personacore.dialogue.build_recall_prompt
  - personacore.training.data.get_batch_memmap_masked
  - results/phase14_factset_report.md
provides:
  - scripts/phase14_factset.FAMILIES
  - scripts/phase14_factset.FAMILIES_SECOND_PERSON
  - scripts/phase14_factset.SLOT_FORMS
  - scripts/phase14_factset.FAMILY_IDS
  - scripts/phase14_factset.TAUGHT_FAMILY_IDS
  - scripts/phase14_factset.HELDOUT_FAMILY_IDS
  - scripts/phase14_factset.PARAPHRASES_PER_FACT_TARGET
  - scripts/phase14_factset.render_family
  - scripts/phase14_factset.heldout_questions
  - scripts/teach_persona.build_bins
  - scripts/teach_persona.render_episodes
  - scripts/teach_persona.arm_outputs
  - scripts/teach_persona.arm_spec
  - scripts/teach_persona.MASK_FRACTION_BAND
  - scripts/teach_persona.ARMS
  - tests/test_phase14_teaching.py
affects:
  - "plan 14-07 (training half lands in the marked section; lock_family_allocation rewrites the allocation)"
  - "plan 14-09 (CALIBRATION_DECISION_RULE rewrites TAUGHT/HELDOUT from the measured run; carries the mask fraction into the calibration report)"
  - "scripts/phase14_recall.py (future — scores held-out questions from heldout_questions())"
tech-stack:
  added: []
  patterns:
    - "the FRAME belongs to the family, the NOUN PHRASE belongs to the slot — 8 strings per slot instead of 8 families x N hand-written pairs"
    - "W-04 satisfied by construction: direct frames read np1, oblique frames read np2, so cross-family nesting is structurally impossible"
    - "build-time replay as a concatenation ratio, keeping train() untouched"
    - "proofs that describe the written bins live in build_bins; proofs needing more context live in sanity_check"
key-files:
  created:
    - scripts/teach_persona.py
    - tests/test_phase14_teaching.py
  modified:
    - scripts/phase14_factset.py
decisions:
  - "SLOT_FORMS factors the grammar into 8 composable strings per slot; np1 (direct frames F1/F2) and np2 (oblique frames F6/F7/F8) are deliberately distinct so W-04 cross-family nesting cannot occur even as the calibration-derived allocation moves families between sides"
  - "the second-person mirror is a 4-rule regex rewrite of the first-person answer rather than a second hand-authored table — the two arms then differ in register and in nothing else, which is exactly what D-21 measures"
  - "F3's mirror answer is the full second-person sentence, not the bare value: a bare value carries no register at all, so a literal mirror would make the register arm measure nothing on that family"
  - "the token-level leakage needle is build_recall_prompt — the same ids the scoring harness sends at recall time — rather than a locally re-truncated encode_dialogue call"
  - "proofs 1-3 live inside build_bins so the corpus floor fires on the builder itself (what the plan's test contract requires); proofs 4-6 live in sanity_check because they need the tokenizer, the fact list and the held-out set"
metrics:
  duration: 45min
  tasks: 3 of 3
  files: 3
  completed: 2026-08-02
---

# Phase 14 Plan 04: Teaching Grammar + Masked Teaching Bins Summary

Authored the eight-family template grammar with first-person answers, built the arm-scoped
masked teaching-bin builder behind the D-06 verdict gate, and pinned the answer-span mask plus
both halves of the held-out guarantee with 10 CPU-only tests — including a negative control
that confirms the leakage checks actually bite.

## What Shipped

**`scripts/phase14_factset.py`** (+330 lines, appended below the locked fact set)

| Constant / function | Content |
|---|---|
| `SlotForms` / `SLOT_FORMS` | 8 composable strings for each of 11 slots — the per-slot vocabulary the family frames read |
| `FAMILY_IDS` | `F1..F8` |
| `FAMILIES` | 8 generators, first-person answers (D-01) |
| `FAMILIES_SECOND_PERSON` | the D-21 register-arm mirror, applied only to `REGISTER_ARM_FACTS` |
| `TAUGHT_FAMILY_IDS` | `{F1, F2, F4, F5, F6}` — 22 paraphrases/fact |
| `HELDOUT_FAMILY_IDS` | `{F3, F7, F8}` |
| `PARAPHRASES_PER_FACT_TARGET` | `(20, 50)` — DEMO-05's band |
| `render_family` / `heldout_questions` | register dispatch; 130 never-seen questions (90 family-derived + 40 reserved probes) |

The allocation comment carries `calibration-provisional`, names plan 14-09 as the rewriter, and
states D-22 in full with `arxiv.org/abs/2309.12288` cited in place, including the
no-pre-flight-exemption condition.

**`scripts/teach_persona.py`** (new, bins half only — 300 lines)

`_require_go_verdict` → `arm_spec` → `refuse_if_exists` → `render_episodes` → `build_bins` →
`sanity_check`, with six loud `SystemExit` proofs (`grep -c "assert "` is **0**):

1. token/mask bins 1:1 aligned · 2. the `BLOCK_SIZE + 1` corpus floor (Pitfall 5) ·
3. the Phase-14 mask-fraction band · 4. a real masked batch carrying `-100` ·
5. per-fact paraphrase count inside DEMO-05's band · 6. token-level held-out non-subsequence.

The training half is a marked empty section for plan 14-07. `grep -c "cap_persona"` is **0**
(persona is `[]`, so the D-07 cap is a structural no-op) and `grep -c "0.30, 0.70\|0.3, 0.7"`
is **0** (the PersonaChat literal is not copied).

**`tests/test_phase14_teaching.py`** (new, 10 tests, 0 skips, 0.88 s)

`test_answer_span_mask`, `test_masked_batch_targets_carry_sentinel`, `test_bin_shape`,
`test_mask_fraction_band_is_phase14_value`, `test_families_disjoint`,
`test_no_family_question_contains_another`, `test_no_string_leakage`, `test_no_token_leakage`,
`test_reserved_probes_are_heldout`, `test_taught_answers_are_first_person`.

## Measured Numbers (the `real` arm, built into a temp dir and discarded)

| Quantity | Measured |
|---|---|
| Episodes | 220 (10 facts x 22 taught paraphrases) |
| Tokens | **10,018** — 39x the 257-token floor |
| Episode length | mean 45.5, range **24–84** |
| Mask fraction (aggregate) | **0.3723** |
| Mask fraction (per episode) | mean 0.3810, **min 0.1884**, max 0.6000 |
| Held-out questions | 130 (90 family-derived + 40 reserved probes) |
| W-04 containment | clean over all 26 facts, string **and** token level |

**The S2 derivation is vindicated by measurement, with one honest qualification.** The realized
per-episode mask fraction bottoms out at **0.1884** — below PersonaChat's 0.30 floor — and the
realized episode length runs to 84 ids, well past F5's 26–45 representative range (the F6/F8
frames are longer than the probes F5 sampled). So the corpus genuinely occupies a wider band than
PersonaChat's. The qualification: the check `build_bins` performs is on the **aggregate**
fraction, and the aggregate landed at 0.3723, which is *inside* the PersonaChat band — so copying
the literal would not in fact have produced a false failure on this particular arm. The wide band
is still correct (a shrunken fact set or an answer-heavy arm moves the aggregate, and the
per-episode spread already crosses the narrow floor), but the plan's "false-failure waiting to
happen" framing is a prediction about arms not yet built, not something this arm demonstrates.

## Verification

| Check | Result |
|---|---|
| Plan's Task-1 automated block | `taught ['F1','F2','F4','F5','F6'] heldout ['F3','F7','F8'] para/fact 22` |
| Plan's Task-2 automated block | `bins half loads; arms scoped` — all arm path sets pairwise disjoint |
| Real end-to-end build + all six proofs | pass; floor proof fires with `teaching corpus is 96 tokens, at or below the 257-token floor` |
| `pytest -q tests/test_phase14_teaching.py -x` | 10 passed |
| `pytest -q` (full suite) | **311 passed, 4 skipped** (wave 3 baseline 301+4, +10 new) |
| `ruff check . && ruff format --check .` | clean, 128 files |
| `grep -c "assert "` / `"cap_persona"` / `"0.30, 0.70\|0.3, 0.7"` (teach_persona) | 0 / 0 / 0 |
| docstring `PITFALLS-14` / `UNMASKED` / `by design, not by drift` | 4 / 1 / 1 |
| `grep -c "skipif\|importorskip"` / `"checkpoints/"` (test) | 0 / 0 |
| Negative control (F7 taught **and** held out) | `test_no_string_leakage` + `test_no_token_leakage` both RED, then reverted byte-clean |
| `git diff --diff-filter=D` across all three commits | no deletions |

## Deviations from Plan

### Deliberate Adjustments

**1. `F4`'s answer is value-leading, per the task's action spec rather than its acceptance-criterion enumeration**
Task 1's action spec mandates `who is zorp?` → `zorp is my dog.`, but the same task's acceptance
criteria enumerate allowed answer openings as `i `, `my `, `yes, my `, `i would ` "or a bare value
completion (F3)" — a list that cannot express the value-leading shape the reversal *requires*.
Reworded to open with a first-person marker, F4 stops answering the question it asks. Implemented
the action spec; the register invariant is enforced mechanically instead, and more strictly:
`test_taught_answers_are_first_person` asserts no taught answer contains `you`/`your`, that every
mirror answer differs, and that no mirror answer contains `i`/`my`. That is the property D-01
actually needs.

**2. F3's second-person mirror answers with the full sentence, not the bare value**
A bare value completion (`zorp.`) carries no register at all, so a literal mirror would be
byte-identical to the first-person answer and D-21's arm would measure nothing on that family.
The mirror supplies `your dog is named zorp.` instead. Stated in the code beside the branch.

**3. `test_masked_batch_targets_carry_sentinel` uses `block_size = len - 2`, not the plan's `(2, 8)`**
At `block_size=8` on a 32-token bin, `np.random.randint(0, 23)` picks a random start, and a
hand-written expected `y` is impossible — the test would have to recompute the expectation from
the mask, which is the exact anti-pattern the plan's own anti-tautology rule forbids. Used
`tests/test_masked_batch.py`'s determinism idiom (`len - block_size - 1 == 1` ⇒ start index 0) so
both the expected `y` and the `-100` positions stay hand-written literals.

**4. The sentinel fixture bins are written from the hand-transcribed literals, not via `build_bins`**
Same reason as (3), and strictly stronger: the ids and mask are transcribed by hand from a real
`encode_dialogue` call and then *re-verified against it* in `test_answer_span_mask`, so the
fixture is pinned rather than generated. `build_bins`' own output is covered by `test_bin_shape`
and `test_no_token_leakage`.

**5. Proofs 1–3 live inside `build_bins`, proofs 4–6 in `sanity_check`**
The plan describes one "post-build proof block" but Task 3 separately requires `build_bins`
itself to raise the floor `SystemExit`. Split on that line: proofs describing the bins as written
(alignment, floor, band) belong to the builder; proofs needing the tokenizer, the fact list or the
held-out set (`-100` smoke, paraphrase band, token-level leakage) belong to `sanity_check`.

**6. `build_recall_prompt` is the leakage needle**
The plan specifies `encode_dialogue(tok, [], [(q, "")])` truncated at 8186 — which is the
definition of the wave-1 `build_recall_prompt` seam. Called the shipped function instead of
re-truncating locally, so the needle is byte-identical to what the scoring harness will send.

**7. The negative control required a different mutation than the plan suggested**
The plan's Task-3 criterion says to verify the leakage test by "temporarily moving one held-out
id into `TAUGHT_FAMILY_IDS`". Doing exactly that leaves the suite **green**, and correctly so:
`heldout_questions()` derives from `HELDOUT_FAMILY_IDS`, so a *move* removes the family's
questions from the never-seen split at the same time it adds them to the corpus — no leak exists
to detect. The mutation that models a real leak is an **overlap**: adding `F7` to
`TAUGHT_FAMILY_IDS` while leaving it in `HELDOUT_FAMILY_IDS`. Under that mutation
`test_no_string_leakage` and `test_no_token_leakage` both go red (naming
`do you remember what your friends call you?`), and `test_families_disjoint` catches the overlap
itself. Reverted; `git diff` byte-clean. Worth carrying forward: the leakage tests' real teeth are
against *reserved probes leaking into taught wording* and *W-04 cross-family nesting*, not against
allocation moves, which are self-consistent by construction.

### Auto-fixed Issues

None. No bugs, no blockers, no architectural questions arose.

## Threat Mitigations Applied

| Threat ID | Mitigation as built |
|---|---|
| T-14-12 | Three mechanical checks, all green and all verified to bite: `test_families_disjoint` (disjoint + full union), `test_no_string_leakage`, `test_no_token_leakage` + `build_bins` proof 6. W-04 additionally pinned at authoring time by `test_no_family_question_contains_another` at both string and token level |
| T-14-13 | No new masking implementation exists — `encode_dialogue` is the single source, already target-space. `test_answer_span_mask` uses 32 hand-transcribed id/mask literals with an index ruler; proof 4 plus `test_masked_batch_targets_carry_sentinel` confirm `-100` reaches the targets |
| T-14-14 | `_require_go_verdict` hard-exits on anything but a recorded GO/ADAPT and says STOP/PENDING must be escalated, not bypassed |
| T-14-15 | Proof 2 raises `SystemExit` naming both the measured length and the `BLOCK_SIZE + 1` floor **before** `get_batch_memmap_masked` is ever called; verified firing at 96 tokens |
| T-14-16 | `arm_outputs` name-scopes all five write targets; every ordered arm pair verified fully disjoint; `refuse_if_exists` raises naming the offender |
| T-14-05 | No bins were written outside temp dirs — `data/` and `checkpoints/` do not exist in this worktree. All fact values are invented |
| T-14-SC | Zero packages installed |

## Known Stubs

The training half of `scripts/teach_persona.py` is a deliberately empty marked section, assigned
to plan 14-07 by this plan's own scope ("write its bins half only"). It is a planned seam, not an
unwired stub: nothing in this plan's deliverables depends on it, and `main()` completes the bins
build without it.

## Notes for Later Plans

- **Plan 14-09 rewrites the allocation.** `TAUGHT_FAMILY_IDS` / `HELDOUT_FAMILY_IDS` are
  calibration-provisional. `test_families_disjoint`'s full-union assertion is the authoritative
  contract (B-02): `lock_family_allocation` must **move** families, never drop one.
- **Paraphrase headroom.** At 22/fact the taught side sits near the bottom of DEMO-05's 20–50
  band, so 14-09 can move at most one family (`F6`, 4 instances) to the held-out side before
  tripping proof 5. Moving two would need new instances added to a surviving family first.
- **`heldout_questions()` is 130 questions**, of which 40 are reserved probes carrying measured
  base-failure provenance (`FACTSET_GATE_SHA` = `446afab…`). Report the two sub-tiers separately —
  the reserved 40 are *proven* unguessable, the 90 family-derived ones are not.
- **The mask fraction is committed evidence, not just a guard.** `build_bins` returns
  `mask_fraction`, `mask_fraction_{mean,min,max}` and prints them; carry the numbers above into
  `results/phase14_calibration_report.md`.
- **`REPLAY_ARM_RATIO = 1.0`** (one replay token per teaching token) is a placeholder shape for
  D-15's paired comparison; the replay arm additionally requires `data/dialog_train{,_mask}.bin`,
  which `_prepend_replay` checks for with a loud exit.
- **Episode length runs to 84 ids**, past F5's 26–45 representative range. Any later budget
  derived from "episode length" should use the measured range here, not F5's.

## Self-Check: PASSED

- `scripts/phase14_factset.py` — FOUND
- `scripts/teach_persona.py` — FOUND
- `tests/test_phase14_teaching.py` — FOUND
- `.planning/phases/14-teach-then-recall-demo/14-04-SUMMARY.md` — FOUND
- commit `e40bb28` (Task 1) — FOUND
- commit `dac344f` (Task 2) — FOUND
- commit `59f5b4d` (Task 3) — FOUND
</content>
