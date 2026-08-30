---
phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
verified: 2026-08-30T19:20:14Z
head: 84ef11f
status: human_needed
score: 3/4 success criteria fully verified, 1 partial (deferred half covered by Phase 25)
overrides_applied: 0
deferred:
  - truth: "SC1/ADVT-01 second half — *the adapter trained* against the Phase 18 attack suite, with attack intensity swept as an axis"
    addressed_in: "Phase 25"
    evidence: "Phase 25 SC2: 'Both arms carry a full curve at both capacities (n=8 and n=64) — ε for DP-SGD, intensity for adversarial — swept to the never-taught floor and to σ→0 so the curve reconnects to the control at both ends.'"
    note: "Phase 24's own goal is a BUILD goal ('The second mitigation arm, BUILT as a data-mixture ratio'). The seam half of SC1 is fully verified; the trained-adapter half was never in scope."
human_verification:
  - test: "Add ADVT-01 to Phase 25's `**Requirements**:` line in .planning/ROADMAP.md (currently CTRL-01, CTRL-02, FRONT-01..04)."
    expected: "ADVT-01 has a phase that formally claims it. Today it is mapped to Phase 24 in the REQUIREMENTS.md traceability table, Phase 24 correctly declares it unsatisfiable, and Phase 25 — which does the work — does not list the ID. The requirement currently falls between two phases and can never be ticked by the process as written."
    why_human: "Editing the ROADMAP's requirement mapping is a planning decision, not a code fix. The verifier can observe the hole but must not silently reassign a requirement."
  - test: "Decide whether ADVT-02's ticked wording 'A2 is REFUSED at the episode builder, not dropped' should be softened to 'filtered out AND refused behind the filter'."
    expected: "The wording matches the mechanism. In normal operation A2 rows are excluded by the list comprehension at scripts/phase24_adversarial.py:289-292; the SystemExit at :300 is explicitly belt-and-braces behind it (the code's own comment: 'BELT AND BRACES beside the filter above, not instead of it') and fires only if the filter widens."
    why_human: "The operative property (A2 never trains) holds doubly and is verified. Whether the requirement prose over-states the mechanism is an editorial call on a ticked requirement."
  - test: "Confirm that 24-04's instrumentation (contains_refusal / score_refusal / clean_frame_probe_populations in scripts/phase14_recall.py) having no production caller is intended for Phase 25 consumption."
    expected: "Phase 25's sweep driver calls them. Today they are exercised only by tests/test_phase24_refusal_rate.py — verified correct in isolation, but not consumed by any running pipeline."
    why_human: "No ROADMAP SC requires them to be wired during Phase 24, so this is not a gap against the contract — but an unconsumed instrument is how a measurement quietly never gets taken."
---

# Phase 24: Adversarial Extraction-Aware Training + the Held-Out Attack Family — Verification Report

**Phase Goal:** The second mitigation arm, built as a data-mixture ratio with no new training seam,
and with its generalization question converted from a disclaimer into a measurement
**Verified:** 2026-08-30T19:20:14Z at HEAD `84ef11f`
**Status:** human_needed
**Re-verification:** No — initial verification

Every figure below was re-measured by the verifier in its own process against the codebase. No
SUMMARY.md claim was accepted as evidence.

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC1a | `build_bins(..., adversarial_ratio=0.0)` mixture ratio, default byte-identical to v2.0, no loop change / accountant / per-record machinery | VERIFIED | Independently rebuilt: default vs no-kwarg gives identical token sha `f146d426…`, mask sha `a2c4771f…` and `repr(stats)`; zero `adversarial*` keys on the default path. `tests/test_phase21_aligned_bins.py::test_build_bins_byte_identity_default_matches_the_v2_golden` passes against `tests/fixtures/golden_build_bins_v2.json`, last touched 2026-08-23 (Phase 21) and untouched by Phase 24 — a genuinely independent baseline. `train()` unmodified; mixture baked into the bin. |
| SC1b | *The adapter trained* against the attack suite, attack intensity as the **sweep axis** | PARTIAL — DEFERRED | No adapter exists. `results/` holds only `phase24_token_budget.json`; no adversarial arm output, no swept curve. `train_arm('adv_n8'/'adv_n64')` has never been invoked to produce an adapter. Covered by Phase 25 SC2. |
| SC2 | Leave-one-attack-family-out split committed, held-out family named before training, no family on both sides (superseded key replaced by two named assertions) | VERIFIED | Re-measured the superseded key independently: `(fact_id, seed_index)` gives **140/140** pairwise overlap across all four families; `(fact_id, seed_index, tier)` gives **216/216**. Complete overlap — the original clause is genuinely UNSATISFIABLE, exactly as the continuation claims. Both replacement assertions exist with non-vacuity guards (partition, non-empty, >1 family). Continuation commit `217c531` = **48 insertions / 0 deletions**; SC2's original sentence stands unamended. |
| SC3 | Attack intensity disclosed as also a token-budget axis, reported as scored-token counts per arm | VERIFIED | `results/phase24_token_budget.json`: 12 rows, integer counts with `*_denominator`/`*_source` on every figure. Re-derived live at 4 points — adv_n8 `scored_tokens` 2719 and adv_n64 28128 / 84912 all match a fresh rebuild exactly, as do all four `mask_fraction` values to full float precision. `cross_family_inflation_exact` 3.7307476110174256 re-counted off the corpus (A3 118.5179 / A2 31.7679, 112 rows each) — exact match. 3.73× and 1.40× kept explicitly distinct in prose and by `test_the_token_budget_confound_keeps_both_figures_distinct`. |
| SC4 | `phase18_extraction.py` imported read-only; attack trained against == attack scored by; inflation report ships with every new corpus | VERIFIED | `git log` over the phase window shows `scripts/phase18_extraction.py` untouched. AST walk by the verifier: **0** `build_corpus` calls in both Phase 24 modules. Prompt parity is enforced inside the builder (`ids != committed` → `SystemExit`, `phase24_adversarial.py:336-348`); my successful 336-episode build exercised it 336 times. Inflation obligation discharged explicitly: `new_attack_corpus: false`, `inflation_report_required: false`, with a written discharge in the record. |

**Score:** 3/4 fully verified; SC1 verified on its seam half, its trained-adapter half deferred to Phase 25.

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | SC1/ADVT-01 — the adapter *trained*, intensity *swept* | Phase 25 | Phase 25 SC2: "Both arms carry a full curve at both capacities (n=8 and n=64) — ε for DP-SGD, **intensity for adversarial** — swept to the never-taught floor and to σ→0." |

### Ruling on the ADVT-01 non-tick

**The non-tick is CORRECT.** This was the phase's most consequential judgment and it holds up.

ADVT-01's grammatical subject is *"The adapter **trained** against the Phase 18 attack suite"* — a
past participle naming a produced artifact — and the modifier *"with attack intensity as the **sweep
axis**"* requires a swept curve, not a single build. Neither exists at HEAD: `results/` contains no
adversarial arm output and no adapter. Ticking it would assert a trained adapter that does not
exist.

The alternative reading — that "implemented as a `build_bins` mixture ratio" is the whole content
and "the adapter trained" is scene-setting — fails on two counts: it makes "sweep axis" vacuous, and
it collapses ADVT-01 into a restatement of the seam's existence.

The asymmetry against ADVT-02 is the load-bearing part, and it is real: ADVT-02 asks for a split
*named before training*, which is best satisfied when no training has occurred; ADVT-01 asks for a
*trained adapter*, which cannot be satisfied when none has. Both calls are consistent.

**However**, see the escalation item: Phase 25's ROADMAP `Requirements:` line lists
`CTRL-01, CTRL-02, FRONT-01..04` and **not ADVT-01**. Combined with the traceability table mapping
ADVT-01 to Phase 24 (which correctly disclaims it), ADVT-01 currently has no phase that will tick it.

### Ruling on the ADVT-02 / ADVT-03 ticks

Neither over-claims on substance.

**ADVT-02 respects the boundary 24-07 conceded.** REQUIREMENTS.md line 477 states verbatim: *"and
equally means it may NOT be claimed as a deliberate leave-one-out choice."* The same concession
appears in the committed record's `held_out_reason`. The peek prohibition is satisfied structurally
(A2 excluded for value containment, a reason that precedes every run), not by a performance-blind
choice — and the text says so.

**One over-precision, not an over-claim:** *"A2 is REFUSED at the episode builder, not dropped."* In
normal operation A2 rows are excluded by the list comprehension at `phase24_adversarial.py:289-292`;
the `SystemExit` at `:300` is belt-and-braces behind it, per the code's own comment. The refusal
fires only on a widened filter. The operative property (A2 never trains) holds doubly and is
verified — this is a wording call, surfaced for a human decision.

**ADVT-03 does not over-claim.** The disclosure obligation is discharged by a committed record whose
figures re-derive live. One INFO note: ADVT-03's own 35/49-token, 1.40×/1.17× per-sentence figures
are inherited from the requirement text and are **not re-measured** by this phase. The requirement
asks for disclosure, not re-measurement, and the record quotes them as ADVT-03's figures with a test
forbidding their substitution as a value — so this is within contract, but those two numbers remain
the only figures in the artifact not verifiable from the repo.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/phase24_adversarial.py` | Refusal table, A2 refusal, episode builder, family list | VERIFIED | 413 lines. 11 refusals, slot parity with `SLOT_FORMS` (11 == 11) verified live; 0 published-value hits; scored-token counts 18–26 all clear `MIN_REFUSAL_SCORED_TOKENS = 15`. `TRAINED_FAMILIES` / `HELD_OUT_FAMILY` present. Pool built: 336 episodes, 112/112/112. |
| `scripts/mitigation_budget.py` | `ADVERSARIAL_RATIO_GRID` + provenance | VERIFIED | `(0.0, 0.25, 0.5, 1.0, 1.5, 1.9090909090909092)`. Upper == `336/176` exactly. AST: all six elements are `ast.Constant` — float literals, no `BinOp`, so the Phase 23 budget guard stays green. |
| `scripts/teach_persona.py` | `adversarial_ratio` seam, seed interleave, additive stats, arm rows | VERIFIED | Seam at `build_bins:491`, gated `if adversarial_ratio > 0`. `_mix_adversarial:839` uses `random.Random(seed)` — pure. `n_want = round(ratio * n_clean)` where `n_clean = len(episodes)`; `teaching_tokens` computed before and never read in the mixture. Threaded to `build_arm_bins` and `train_arm`. `adv_n8`/`adv_n64` outside `DP_ARMS` → pack flat. |
| `scripts/phase14_recall.py` | `contains_refusal` / `score_refusal` / clean-frame probe | ORPHANED (see below) | Substantive and correct in isolation — 112 vs 112 distinct questions, budget-matched, disjoint, 0 of 10 published values across all 224, `reading_rule` pinned in code. **No production caller outside its own module.** |
| `scripts/phase24_record.py` | `TOKEN_BUDGET_RECORD`, write-once dirty-refusing emitter | VERIFIED | 503 lines. Imports `ADVERSARIAL_RATIO_GRID` rather than retyping it; records `corpus_sha256` live. |
| `results/phase24_token_budget.json` | Per-arm × per-point counts, multiplicity, band, provenance | VERIFIED | 667 lines, 12 rows. All four `provenance.module_sha256` values match the current files exactly — the record is not stale. Emitter commit `5aed70f` contains `phase24_record.py` but **not** the artifact: the emitter genuinely preceded its output. |
| `.planning/ROADMAP.md` | 24-03 dated continuation, additive, original standing | VERIFIED | Commit `217c531`: 48 insertions / 0 deletions. Sentinels present. Original SC2 sentence intact. |
| 9 × `tests/test_phase24_*.py` | The guards | VERIFIED | 49 tests, all passing in 4.04 s when run by the verifier. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `teach_persona.build_bins` | `phase24_adversarial.adversarial_episodes` | lazy import in the `ratio>0` branch | WIRED | Verified by execution: a build at ratio 1.909 produced 512 episodes / 336 adversarial. |
| `teach_persona._mix_adversarial` | `adversarial_episode_families` | lazy import, positional pairing | WIRED | `adversarial_family_counts` returned `{A1-mild: 112, A1-aggressive: 112, A3: 112}` at the selected prefix. |
| `build_arm_bins` / `train_arm` | `build_bins` | `adversarial_ratio=` threaded | WIRED | `teach_persona.py:1237`, `:1683`. |
| `phase24_adversarial` | `results/phase18_corpus.json` | `p18.CORPUS_PATH`, read-only | WIRED | 0 `build_corpus` calls (AST); 336 prompts proved byte-equal on the live build. |
| `phase24_adversarial.attack_prompt_ids` | `build_recall_prompt(persona=)` | 4th `PERSONA_ALLOWLIST` entry | WIRED | Entry landed in the SAME commit `c10d017` as the call site (222 + 15 insertions). |
| `phase24_record` | `ADVERSARIAL_RATIO_GRID` / `corpus_sha256` | imported, never retyped | WIRED | Grid and digest both resolve from the owning modules. |
| `phase14_recall.contains_refusal` etc. | *any production consumer* | — | **ORPHANED** | Referenced only by `tests/test_phase24_refusal_rate.py`. No caller in `scripts/` or `src/`. |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real Data | Status |
|----------|------|--------|-----------|--------|
| `results/phase24_token_budget.json` | `scored_tokens`, `mask_fraction` | `int(np.fromfile(mask_bin).sum())` off the bin actually written | Yes — matches a live rebuild exactly at 4 independent points | FLOWING |
| `adversarial_family_counts` | selected-prefix per-family counts | `selected_families.count(...)` over the real selection | Yes — 112/112/112 at UPPER, non-empty at every grid point | FLOWING |
| `token_budget_disclosure.cross_family_inflation` | 3.7307476110174256 | live per-family means off `phase18_corpus.json` | Yes — verifier re-counted, exact match | FLOWING |
| `band_corners` | four mask fractions | four real `build_bins` calls | Yes — n=64 column measured (1408 clean episodes), not carried from n=8 | FLOWING |
| `clean_frame_probe_populations()` | 112 locked + 112 filler questions | live render over `F1,F2,F6` | Yes, but consumed by nothing | HOLLOW (unconsumed, not hollow-valued) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Default path byte-identical to no-kwarg | `build_bins(...)` vs `build_bins(..., adversarial_ratio=0.0)`, sha256 both bins + `repr(stats)` | identical; `f146d426…` / `a2c4771f…`; 0 adversarial keys leaked | PASS |
| Kwarg genuinely read (non-vacuity) | same build at ratio 1.909 | both bin shas move; 336 adversarial episodes placed | PASS |
| D-06 sizing unit | `adversarial_episodes == round(1.909… × 176)` | 336 == 336 | PASS |
| D-08 permutation purity | same seed twice, then `SEED+1` | same→identical bytes; different→different bytes | PASS |
| D-05 band, worst corner | four-corner rebuild | adv_n8@upper = 0.24100851889131664, clears 0.15+0.05 by 0.041009; all four clear | PASS |
| SC2 superseded key | pairwise overlap on both readings | 140/140 and 216/216 — unsatisfiable, as claimed | PASS |
| D-01 refusal value-freedom | `contains_value` over 11 refusals × published values | 0 hits; scored tokens 18–26 ≥ 15 | PASS |
| Record re-derivation | live rebuild vs committed rows, 4 points | `scored_tokens` and `mask_fraction` exact `==` | PASS |
| Phase 24 test files | `.venv/bin/python -m pytest tests/test_phase24_*.py -q` | 49 passed, 4.04 s | PASS |
| v2.0 golden identity | `pytest ...::test_build_bins_byte_identity_default_matches_the_v2_golden` | 1 passed | PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` exist in this repository and no PLAN declares one. Probe execution
is **SKIPPED (no probe convention in this project)**. Its role is filled by the pytest guards, which
the verifier ran directly rather than reading pass counts out of a SUMMARY.

### Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
|-------------|-------------|--------|----------|
| ADVT-01 | 24-01, 24-02, 24-04, 24-05, 24-06, 24-07 | BLOCKED (correctly) → deferred to Phase 25 | Seam, pool, grid, band and record all verified. No trained adapter exists, so the requirement's subject does not exist. Non-tick ruled CORRECT. |
| ADVT-02 | 24-03, 24-05, 24-07 | SATISFIED | Split disjoint on both keys with partition + non-vacuity guards; A2 named before any training for a structural reason; ticked text respects the "may not be claimed as a deliberate choice" boundary. |
| ADVT-03 | 24-02, 24-06, 24-07 | SATISFIED | Committed record with integer counts, denominators and live-re-derivable figures; 3.73× and 1.40× kept distinct in prose and by test. |

**Orphaned requirements:** none. REQUIREMENTS.md maps exactly ADVT-01/02/03 to Phase 24 and all
three appear in plan frontmatter.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | `TBD` / `FIXME` / `XXX` / `TODO` / `HACK` / `PLACEHOLDER` | — | **None found** in any Phase 24 file, nor in the Phase 24 additions to `teach_persona.py`, `phase14_recall.py` or `mitigation_budget.py`. |
| `scripts/phase14_recall.py` | 325, 361, 391 | Unconsumed public API | WARNING | `contains_refusal` / `score_refusal` / `clean_frame_probe_populations` have no production caller. Correct in isolation; nothing runs them. |

### Human Verification Required

**1. ADVT-01 has no phase that will tick it (traceability hole)**
- **Test:** Add `ADVT-01` to Phase 25's `**Requirements**:` line in `.planning/ROADMAP.md`.
- **Expected:** ADVT-01 is claimed by the phase that does its work. Today it is mapped to Phase 24
  (which correctly disclaims it) while Phase 25 — whose SC2 explicitly sweeps adversarial intensity
  — lists only `CTRL-01, CTRL-02, FRONT-01..04`.
- **Why human:** Reassigning a requirement is a planning decision. The verifier can observe the hole
  but must not silently move the mapping.

**2. ADVT-02's "REFUSED, not dropped" wording**
- **Test:** Read `scripts/phase24_adversarial.py:289-292` beside `:300` and decide whether the
  ticked prose should say "filtered out AND refused behind the filter".
- **Expected:** Wording matches mechanism. The filter drops A2; the `SystemExit` is belt-and-braces
  behind it and fires only on a widened filter.
- **Why human:** The safety property holds doubly and is verified — this is an editorial call on
  already-ticked requirement text.

**3. 24-04's instrumentation is unconsumed**
- **Test:** Confirm Phase 25's sweep driver will call `contains_refusal`, `score_refusal` and
  `clean_frame_probe_populations`.
- **Expected:** They have a consumer. Today only their own tests reference them.
- **Why human:** No ROADMAP SC requires them wired in Phase 24, so this is not a contract gap — but
  an unconsumed instrument is how a planned measurement quietly never gets taken.

### Gaps Summary

**No blockers.** Every artifact this phase claimed to ship exists, is substantive, and — with one
scoped exception — is wired into a real consumer. Critically, the two claims most at risk of being
vacuous both survived independent re-measurement:

- **The byte-identity guard is not vacuous.** `adversarial_ratio` is genuinely read: the same build
  at 0.0 and at 1.909 produces different token and mask bins, so the identity at the default is a
  property of a live parameter rather than of dead code. The v2.0 baseline is a fixture from
  Phase 21 that this phase never touched.
- **The SC2 supersession is a measurement, not an excuse.** The original `(fact_id, seed_index)`
  clause really is unsatisfiable — 140/140 and 216/216 pairwise overlap, re-counted by the verifier
  — and the correction landed as 48 insertions / 0 deletions with the original sentence standing.

The one unachieved success criterion, SC1's *"the adapter trained … attack intensity as the sweep
axis"*, is not a gap: Phase 24's goal is explicitly a **build** goal, and Phase 25 SC2 names the
sweep verbatim. The ADVT-01 non-tick is correct and the phase was right to refuse it.

What needs a human is not code. It is that ADVT-01, having been correctly refused here, is not
claimed anywhere else — so the requirement is presently unownable by the process. That is the
escalation.

---

_Verified: 2026-08-30T19:20:14Z at HEAD 84ef11f_
_Verifier: Claude (gsd-verifier) — all figures re-measured in-process; no SUMMARY.md claim accepted as evidence_
