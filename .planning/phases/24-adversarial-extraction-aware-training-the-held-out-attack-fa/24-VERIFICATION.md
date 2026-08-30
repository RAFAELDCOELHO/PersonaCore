---
phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
verified: 2026-08-30T20:45:29Z
head: 904772d
status: human_needed
score: 3/4 success criteria fully verified, 1 partial (deferred half covered by Phase 25); 3/3 24-REVIEW blockers independently confirmed closed
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_head: 84ef11f
  previous_score: 3/4
  gaps_closed:
    - "24-REVIEW CR-01 — `main()` no longer reaches `arm_spec`/`train_arm` for `adv_n8`/`adv_n64`; the false `len(argv) != 1` defense is deleted, not supplemented"
    - "24-REVIEW CR-02 — the D-02 scan sweeps 22 tier-derived values with a non-vacuous coverage assertion over all 11 `REFUSAL_SLOT_NOUNS` slots; the planted-`chartreuse` leak reproduces RED"
    - "24-REVIEW CR-03 — `contains_refusal`/`score_refusal` refuse a degenerate template member at the boundary through both entry points"
    - "UAT item 1 — ADVT-01 given an owning phase (ROADMAP.md:814), span recorded additively under REQUIREMENTS.md `## Traceability`"
  gaps_remaining: []
  regressions:
    - "results/phase24_token_budget.json `provenance.module_sha256` is now STALE for 2 of 4 pinned modules (`phase24_adversarial.py`, `teach_persona.py`) — the record's NUMBERS are unchanged and still re-derive, but the initial report's claim that all four digests match HEAD no longer holds. WARNING, not a blocker. See re-verification section."

deferred:
  - truth: "SC1/ADVT-01 second half — *the adapter trained* against the Phase 18 attack suite, with attack intensity swept as an axis"
    addressed_in: "Phase 25"
    evidence: "Phase 25 SC2: 'Both arms carry a full curve at both capacities (n=8 and n=64) — ε for DP-SGD, intensity for adversarial — swept to the never-taught floor and to σ→0 so the curve reconnects to the control at both ends.'"
    note: "Phase 24's own goal is a BUILD goal ('The second mitigation arm, BUILT as a data-mixture ratio'). The seam half of SC1 is fully verified; the trained-adapter half was never in scope."
human_verification:
  - status: RESOLVED 2026-08-30 at commit e5a2474 — ROADMAP.md:814 now reads `CTRL-01, CTRL-02, FRONT-01..04, ADVT-01`; the two-phase span is a dated additive amendment under REQUIREMENTS.md `## Traceability`, and the dated 2026-08-20 "0 duplicates" line is byte-unchanged. Re-verified at HEAD 904772d.
    test: "Add ADVT-01 to Phase 25's `**Requirements**:` line in .planning/ROADMAP.md (currently CTRL-01, CTRL-02, FRONT-01..04)."
    expected: "ADVT-01 has a phase that formally claims it. Today it is mapped to Phase 24 in the REQUIREMENTS.md traceability table, Phase 24 correctly declares it unsatisfiable, and Phase 25 — which does the work — does not list the ID. The requirement currently falls between two phases and can never be ticked by the process as written."
    why_human: "Editing the ROADMAP's requirement mapping is a planning decision, not a code fix. The verifier can observe the hole but must not silently reassign a requirement."
  - test: "Decide whether ADVT-02's ticked wording 'A2 is REFUSED at the episode builder, not dropped' should be softened to 'filtered out AND refused behind the filter'."
    expected: "The wording matches the mechanism. In normal operation A2 rows are excluded by the list comprehension at scripts/phase24_adversarial.py:289-292; the SystemExit at :300 is explicitly belt-and-braces behind it (the code's own comment: 'BELT AND BRACES beside the filter above, not instead of it') and fires only if the filter widens."
    why_human: "The operative property (A2 never trains) holds doubly and is verified. Whether the requirement prose over-states the mechanism is an editorial call on a ticked requirement."
  - test: "Confirm that 24-04's instrumentation (contains_refusal / score_refusal / clean_frame_probe_populations in scripts/phase14_recall.py) having no production caller is intended for Phase 25 consumption."
    expected: "Phase 25's sweep driver calls them. Today they are exercised only by tests/test_phase24_refusal_rate.py — verified correct in isolation, but not consumed by any running pipeline."
    why_human: "No ROADMAP SC requires them to be wired during Phase 24, so this is not a gap against the contract — but an unconsumed instrument is how a measurement quietly never gets taken."
    status: STILL OPEN at HEAD 904772d. Phase 25 now formally owns ADVT-01, but its Success Criteria name the intensity sweep only and never name the refusal-rate column, so there is no roadmap evidence to defer this against. Kept as a human item rather than reclassified.
  - test: "Decide whether to re-emit results/phase24_token_budget.json at a clean HEAD, or to accept its stale provenance pin with a written note."
    expected: "provenance.module_sha256 describes the bytes that can regenerate the record. At HEAD 904772d two of its four pinned digests no longer match: scripts/phase24_adversarial.py recorded 8f884fd7… / live b679c6f6… (changed by ba2787f, docstring only) and scripts/teach_persona.py recorded e2709e54… / live 82da6c3a… (changed by d4ed1f8). phase24_record.py and mitigation_budget.py still match."
    why_human: "NEW at this re-verification — introduced by 24-08's own blocker fixes. The record's numbers are unaffected and re-derive exactly, and phase24_record.py:418 declares a non-matching digest to be the designed visible signal, so this is not a false claim in the artifact. But re-emit vs. accept is a judgment about what the committed record is for, and re-emitting is currently blocked anyway: refuse_if_dirty counts untracked files as dirty and the tree carries `M .gitignore` + `?? .planning/todos/`. No test guards this — tests/test_phase24_record.py:274-276 checks corpus_sha256 against live but never module_sha256."
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

---

## Re-verification 2026-08-30 (post gap closure)

**Re-verified:** 2026-08-30T20:45:29Z at HEAD `904772d` (was `84ef11f`)
**Ruling:** `human_needed` — NOT `passed`
**Scope:** the three 24-REVIEW blockers, regression on the load-bearing invariants, and the final
status call. Everything above this line stands as written at `84ef11f`; this section corrects it
additively where HEAD has moved.

Every figure below was re-measured by this verifier in its own process. 24-08-SUMMARY.md's
RED → GREEN → mutated-RED narrative was treated as a claim and independently reproduced, not read.

### The three blockers

| Blocker | Independent check | Result |
|---------|-------------------|--------|
| **CR-01** — `main()` trains `adv_n8`/`adv_n64` at ratio 0.0 under an "adversarial" name | Monkey-poisoned `arm_spec` **and** `train_arm` to raise on entry, then called `main(["adv_n8"])` and `main(["adv_n64"])` | **CLOSED.** Both raise `SystemExit` (616 / 617 chars, naming `adversarial_ratio`); **neither poisoned callable ran** — `poisoned == []`. The refusal is an `elif arm in ADV_ARMS` branch in the `DP_ARMS` dispatch at `teach_persona.py:1407`, structurally ahead of `arm_spec(arm)` at `:1421`. `ADV_ARMS = ("adv_n8", "adv_n64")` at `:1309`. |
| **CR-01** — programmatic path must be unchanged | `inspect.signature` + source scan of the threading chain | **INTACT.** `train_arm(adversarial_ratio=0.0)`, `build_arm_bins(adversarial_ratio=0.0)`, `build_bins(adversarial_ratio=0.0)` all present; `train_arm` forwards to `build_arm_bins` forwards to `build_bins`. Both provenance prints now interpolate `adversarial_ratio=`. |
| **CR-01** — the FALSE comment at ~`:270` | `git diff 84ef11f..HEAD -- scripts/teach_persona.py` | **CORRECTED, not supplemented.** The hunk **deletes** *"that is a choice rather than an omission: `main()`'s non-DP path still enforces `len(argv) != 1`"* and replaces it with *"so `main()` REFUSES both arms outright"*, followed by a dated `CORRECTED 2026-08-30 (24-REVIEW CR-01)` block that names the old text as FALSE and says why. The false sentence is gone from the file. |
| **CR-02** — the D-02 scan must cover every value of every `REFUSAL_SLOT_NOUNS` slot, tier-derived | Recomputed the swept set and the coverage predicate in-process | **CLOSED.** Set is `LOCKED_VALUES ∪ {f.value for GATE_REJECTED_CANDIDATES} ∪ {f.value for SOFT_TIER_FACTS}` = **22 values**, zero literals. Over `tiers = LOCKED_FACTS + SOFT_TIER_FACTS + GATE_REJECTED_CANDIDATES` filtered to the 11 `REFUSAL_SLOT_NOUNS` slots: **0 uncovered `(slot, value)` pairs**, and **0 slots with no committed value in any tier** — so the coverage assertion is not vacuously true. `chartreuse` and `marzipan` both present; the old 20-value set is exactly those two short. |
| **CR-02** — is the widened scan load-bearing? | **Mutation.** Planted `chartreuse` inside the live `favorite_color` refusal on a scratch copy and ran the real `tests/test_phase14_scoring.embedded_fact_values` against both sets | **The fix bites.** OLD(20) → `[]` (green — the CR-02 defect reproduced in my process). NEW(22) → `[('chartreuse', 1)]` (RED). Unmutated HEAD module under NEW(22) → `[]`. A first mutation attempt that added a new slot key was rejected by `refuse_undeclared_slots()`, so that guard is live too. |
| **CR-03** — degenerate template member | Called both entry points with `""`, `"   "`, `"..."`, `"!!!"`, singly and in a MIXED table behind a legitimate matching template | **CLOSED.** All 8 single cases and the mixed case raise `SystemExit` carrying `EMPTY STRING`. `contains_refusal(anything, [""])` and `score_refusal(['a','b','c'], [''])` — the two exact pre-fix reproductions — now both raise instead of returning `True` / `(3,3)`. |
| **CR-03** — no collateral damage | Non-degenerate and edge inputs | **CLEAN.** Hit `True`, miss `False`, `score_refusal` `(1,2)`. An empty **completion** still scores rather than raising (`False`, `(0,2)`) — the guard is about the template, never the measurement. The documented residue holds: `score_refusal([], t) == (0,0)`. |

### Regression on the load-bearing invariants

| Invariant | Re-measured at HEAD | Result |
|-----------|--------------------|--------|
| **SC1 byte identity** | Fresh build, 176 clean `dp_n8` episodes, `seed_everything(SEED)` | **INTACT.** no-kwarg and `adversarial_ratio=0.0` both give token sha `f146d42637c69e9eb1e7ac2248c9056a7966aed48f6498fa9cdb6d3db02d147b` and mask sha `a2c4771f92aa4e03127e451b1de880b9386bee5164ee512d291467c1eb1e59a2` — the exact pre-edit pair 24-06 recorded — with identical `repr(stats)` and **zero** `adversarial*` keys. |
| **SC1 non-vacuity** | Same build at ratio `1.9090909090909092` | **INTACT.** Both shas move; `adversarial_episodes == 336 == round(ratio × 176)`; families `{A1-mild: 112, A1-aggressive: 112, A3: 112}`. |
| **D-08 seed purity** | Same seed twice, then `seed_everything(SEED+1)` before the same build | **INTACT.** Same seed → byte-identical. Perturbed **global** seed → still byte-identical, which is the purity property: `_mix_adversarial` draws from `random.Random(seed)` and never the global stream. |
| **v2.0 golden** | `test_build_bins_byte_identity_default_matches_the_v2_golden` | **PASS** (inside the 124 below). |
| **AST surface** | Own `ast.walk` at HEAD | **INTACT.** `phase24_adversarial` module-level imports exactly `pathlib, phase14_factset, sys`; `phase14_recall` has no module-level `phase24_adversarial`; **0** integer `336` literals in either; **0** `build_corpus` calls in either. |
| **`results/phase24_token_budget.json`** numbers | Own cross-sum pass over all 12 rows + comparison to the initial report | **INTACT.** `git log 84ef11f..HEAD -- results/` is empty — 24-08 did not touch the artifact. 12 rows; `total−teaching == adversarial`, `total_episodes == clean + adversarial`, `sum(family_counts) == adversarial_episodes` all pass on every row. `adv_n8` scored tokens 2719 → 9817, `adv_n64` 28128 → 84912 — identical to the initial verification. `test_scored_tokens_re_derive_from_a_rebuild` passes. |
| **Suite at HEAD** | `.venv/bin/python -m pytest tests/test_phase24_*.py tests/test_phase14_scoring.py <v2.0 golden> tests/test_phase23_resume.py tests/test_phase22_wiring.py -q` | **124 passed, 0 failed, 123 s, exit 0.** The last two files are exactly what 24-08's disclosed two-commit RED window touched (`test_resume_from_none_is_inert` and the `train_arm(` prose census) — both green at HEAD. The intermediate redness is closed. |

### NEW finding — WR: stale provenance pin on the committed record

**This is the one thing 24-08 broke, and it is a correction to the report above.** The initial
verification stated: *"All four `provenance.module_sha256` values match the current files exactly —
the record is not stale."* That was TRUE at `84ef11f`. It is **FALSE at `904772d`**:

| Pinned module | Recorded in the artifact | Live at HEAD | |
|---|---|---|---|
| `scripts/phase24_record.py` | `f2267e14…` | `f2267e14…` | match |
| `scripts/mitigation_budget.py` | `2e5adc91…` | `2e5adc91…` | match |
| `scripts/phase24_adversarial.py` | `8f884fd7…` | `b679c6f6…` | **STALE** (`ba2787f`, docstring only) |
| `scripts/teach_persona.py` | `e2709e54…` | `82da6c3a…` | **STALE** (`d4ed1f8`, the CLI refusal) |

**Severity: WARNING, not BLOCKER.** Four reasons, each checked rather than assumed:

1. The artifact makes no false claim. `scripts/phase24_record.py:418` declares this exact behaviour
   as the designed signal — *"an artifact written against an edited module carries a digest that
   does not match — visible in the record itself."* The record's statement is historical (*these
   bytes produced these numbers at `5aed70f`*) and remains true. What is now false is the inference
   that HEAD regenerates the same provenance block.
2. The **numbers** are unaffected and I proved it, not assumed it: the two edits are a docstring and
   a CLI guard plus two stdout `print` interpolations, none of which can move a token count, and the
   full byte-identity re-derivation above lands on the same two shas.
3. No ROADMAP Success Criterion requires digest freshness. SC3's contract is scored-token counts
   with denominators, and those hold exactly.
4. Re-emitting is blocked anyway right now: `refuse_if_dirty` counts untracked files as dirty
   (`src/personacore/provenance.py:62-65`) and the working tree carries `M .gitignore` and
   `?? .planning/todos/`.

**But it is genuinely unguarded.** `tests/test_phase24_record.py:274-276` checks `corpus_sha256`
against the live corpus and **never** checks `module_sha256`. So the suite is green at 1646 while
the pin drifts — the same *"green guard, unenforced invariant"* shape 24-REVIEW named three times.
Routed to human decision as item 4: re-emit at a clean HEAD, or accept the pin with a written note
(and, either way, consider a freshness assertion so the next drift announces itself).

### ADVT-01 is still correctly UNTICKED — no over-claim in the tree

Checked specifically, because giving a requirement an owning phase is exactly the move that could
be mistaken for satisfying it:

- `.planning/REQUIREMENTS.md:304` — `- [ ] **ADVT-01**`. **Unticked.**
- `.planning/REQUIREMENTS.md:487` — traceability row still reads *"**NOT SATISFIED — deliberately,
  and Phase 24 was never going to satisfy it.**"* Unchanged.
- The 2026-08-30 amendment is future-tense about Phase 25 (*"Phase 25 TRAINS the adapter"*) and
  claims no satisfaction. The dated 2026-08-20 *"48/48 mapped, 0 orphans, 0 duplicates"* line is
  **byte-unchanged**; the supersession is recorded additively above it.
- `.planning/STATE.md` says *"ADVT-01 stays OPEN because no adapter has been trained"* throughout.
- `results/` still holds only `phase24_token_budget.json` — no adapter, no swept curve.

**Nothing in the tree implies ADVT-01 is satisfied.** The initial report's ruling stands.

**One INFO, no action required:** the traceability table's `Phase` column for ADVT-01 still reads
`Phase 24` alone. The two-phase span lives only in the prose amendment ~40 lines above the row. A
reader who greps the table row in isolation still will not find Phase 25. This is consistent with
the project's additive-correction doctrine (the amendment is the dated record and sits under the
same `## Traceability` heading), but the row is the thing people grep.

### Status ruling: `human_needed`, not `passed`

The three blockers are closed and no load-bearing invariant regressed, so nothing holds this phase
at `gaps_found`. It does not reach `passed` either, for one structural reason and one substantive
one:

- **Structural.** `passed` is only valid when the human-verification section is empty. UAT item 1 is
  resolved, but items 2 and 3 remain open and a fourth was opened by this pass.
- **Substantive.** Item 3 is *not* deferrable, and I checked rather than assumed. Phase 25 now
  formally owns ADVT-01, which is the natural place to defer 24-04's unconsumed instrumentation —
  but Phase 25's Success Criteria name the **intensity sweep** only (`ROADMAP.md:824`) and never
  name the refusal-rate column. With no roadmap text to point at, deferring it would be softening,
  so it stays a human item. Item 2 (ADVT-02's *"REFUSED, not dropped"* wording) is an editorial call
  on already-ticked requirement prose that a verifier must not make. Item 4 is new and is a judgment
  about what the committed record is for.

None of the three open items blocks Phase 25. The recommendation is to dispose of them as a
documentation pass, not to reopen execution.

---

_Re-verified: 2026-08-30T20:45:29Z at HEAD `904772d`_
_Verifier: Claude (gsd-verifier) — blockers reproduced and re-measured in-process; 24-08-SUMMARY.md's evidence treated as a claim throughout_
