---
phase: 19-selective-memory-erasure
verified: 2026-08-19T21:19:00Z
status: human_needed
score: 6/6 must-haves verified
overrides_applied: 0
re_verification: null
gaps: []
deferred: []
human_verification:
  - test: "Confirm the five checkpoint decisions were made as recorded: 19-07 (approve the pin before it closes), 19-09 (the blind calibration run, floor NOT locked), 19-11 (approve all three severities knowingly, including that TARGET_FLOOR == wilson_upper_bound(0,27) makes (a) clear only on a perfect erasure), 19-12 (choose D8 clause 1 — the cliff — and elevate the rank-vs-NLL disagreement to co-headline), 19-16 (record DO NOT SHIP withholding exactly one claim)."
    expected: "Each decision was made by the human at the time recorded, and the artifacts reflect what was decided rather than what an agent proposed."
    why_human: "All five plans are `autonomous: false`. Every artifact I checked is consistent with these decisions, but the decisions themselves live in a conversation, not in the repository. No grep can distinguish 'the human approved this' from 'the agent recorded that the human approved this'."
  - test: "Decide whether `docs/REPORT.md` must carry the DO NOT SHIP reproducibility limitation. Read docs/REPORT.md:1229-1236 — the 'what it establishes is bounded' list names five bounds and does not include 'the verdict is not mechanically reproducible by the pinned CLI'."
    expected: "Either the limitation is added to that bounded list, or a documented reason why the portfolio-facing artifact may omit it while results/phase19_erasure_report.md and ROADMAP.md carry it."
    why_human: "This is an editorial judgement about publication posture, not a code fact. docs/REPORT.md does not assert the withheld claim, so it is not false — the question is whether omission is a softening under this project's own 'do not ship the weaker claim under the stronger word' standard. Only the operator can rule on that."
---

# Phase 19: Selective Memory Erasure — Verification Report

**Phase Goal:** Erase **one** taught fact from the weights and report what that cost, under the rule
committed at `23a830c` before any v3.0 number existed — auditable forgetting with a measurable
bound, plus representational consistency reported honestly.

**Verified:** 2026-08-19T21:19:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

---

## How this phase was judged

The phase goal is to **run** the erasure under a rule committed before the numbers existed and
publish whatever came out. The rule's three conditions — (a), (b), (c) — are the *gate's* pass
conditions, not the *phase's* deliverables. A verifier who marks (b) FAILED because the measurement
returned FAIL has inverted the contract: the phase promised a measurement, not a favourable one.

So each success criterion below is verified as: **was it measured under the committed rule, with its
denominators, and published unsoftened?** The empirical outcome is recorded beside it.

The verdict is `FAILURE` and the ship decision is `DO NOT SHIP`. Neither is scored as a defect.

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | **(a) TARGET FORGOTTEN** — one-sided 95% Wilson **upper** bound on post-erasure target recall, questions as the unit, against a floor from **blind calibration on a disjoint fact set**, run **before** the target was scored; floor not taken from TOFU/WMDP | ✓ VERIFIED | Reproduced independently: `wilson_upper_bound(0, 27)` = `0.09107873950450847` == `TARGET_FLOOR` **exactly**, headroom `0.0`. Target `cand_dog_zorp` reads 0/27 questions (0/13 held-out + 0/14 taught, 1,296 draws) from 27/27 pre-erasure. Blindness proven two ways: (i) `CALIBRATION_POOL` (10 facts) ∩ `LOCKED_FACTS` (8 facts) = ∅ computed at runtime; calibration fact `cal_person_varek`, target `cand_dog_zorp`, different pool and different slot; (ii) git ordering — cal arm added `2026-08-18 10:21`, floor locked `2026-08-18 12:50`, **target scored `2026-08-19 13:26`** (~24.6 h later). Rule-of-three `0.111111` published beside Wilson, never instead. **Outcome: (a) cleared, exactly on its boundary.** |
| 2 | **(b) NON-TARGET PRESERVED** — every non-target taught fact within k=2 × the same-run noise floor, reported **per fact with its denominator**, never pooled; `nontarget_deltas` non-empty | ✓ VERIFIED | 7 gated slots each with own denominator 27 and own Wilson bound; `nontarget_deltas_in_slot_order` = `[0.7407, 1.0, 1.0, 0.9630, 0.7037, 0.3704, 0.7778]`, floor `0.14814814814814814`, margin `0.2962962962962963`. No pooled path exists — `test_nontarget_deltas_is_per_fact_over_exactly_the_seven_and_has_no_pooled_path` green. Two soft-tier facts outside (b) by declared narrowing, published anyway. **Outcome: (b) FAILED on all seven, four at total generation loss — measured and published, not hidden.** |
| 3 | **(c) CAPABILITY PRESERVED** — dialogue PPL ≤ 4.5733 + k=2 × measured floor, retention PPL ≤ 3.891140 + 0.137860, evaluated **literally as pre-registered** | ✓ VERIFIED | Cap arithmetic reproduced from the gate itself: `4.5733 + 2 × 0.005214448168350039 = 4.5837288963367`; retention cap `4.029`. Measured `dialogue_ppl_post.adapter_on` = `4.851119149910443`, `retention_ppl_post[0]` = `3.6709177253236867`. Pre-erasure printed beside post in both artifact and report (`dialogue_ppl_pre.adapter_on` = `5.815445876712191`). `23a830c` unamended — 1 commit, confirmed. **Outcome: (c) FAILED on the dialogue leg (+0.2674), retention cleared. Root cause diagnosed in a dated continuation BESIDE the verdict, never over it.** |
| 4 | **Representational consistency REPORTED, never gated** — cross-persona ΔW cosine and Fisher overlap, each with its bounds | ✓ VERIFIED | Cross-persona: n=108 cosines over 3 personas × 36 cells, min `0.05118`, median `0.12535`, max `0.33687`, with the note naming n=3 as the exact n the rule says cannot support a threshold. Fisher: 22 ablated cells mean `1.6354877` vs 14 preserved mean `0.5136732`, **both denominators published, no ratio**. Not-gated enforced structurally, not in prose: `test_representational_read_is_not_gated` scans `DESCRIPTIVE_ONLY_FUNCTIONS` by AST and carries **three mutation-driven RED assertions** (bare threshold, second `sign_test_exact` call site, missing scan target) — I read them; the scan is non-vacuous. `status: "DESCRIPTIVE"`, zero verdict-shaped keys in either record. |
| 5 | **The verdict — SUCCESS / FAILURE / INCONCLUSIVE — returned by the committed rule and published unsoftened** | ✓ VERIFIED | **Independently reproduced.** Fed raw values straight out of `results/phase19_target_scores.json` through `erasure_gate.erasure_succeeded` (1 commit, `23a830c`) + `phase19_floor.py` (1 commit, `55009d0`): returned `FAILURE` with all three reason strings **byte-identical** to report lines 11-13. Single call site enforced by `test_verdict_is_called_never_reimplemented` — asserts `sites == ["render_verdict"]`, that the pin's `erasure_succeeded` **is** the gate's object (not a value-matching copy), and that no v2.0 baseline is retyped as a literal; two mutation RED assertions confirm non-vacuity. D8 publication posture (`D8_PUBLICATION_POSTURE`, pin line 2001) is inside the pin, which is an ancestor of every artifact — so the framing was locked before the number. |
| 6 | **ERASE-02 reference arm — run it, or state in writing why not** | ✓ VERIFIED | **Run, not explained.** `results/phase19_retrain_training.log` ends `rc=0 wall=81s`, M2 adapter sha256 `22e66552e92ec7d5f853a6b8d15f350cfc0f127f20ee85aaec1967147c375b57`, 331,776-parameter census, production adapter verified INTACT after the run. Scored A2/K=48 with `assert_phase18_parity` enforced. Five of seven bystander deltas exactly `0.0`; the two that move (`0.2593`, `0.1111`) both below the `0.2963` margin. `caveat` and `framing` fields carry `ERASE_02_REFERENCE_ARM` clauses 1, 2 and 4 verbatim — including the explicit prohibition on any "indistinguishable from" claim. The record also self-reports that its own `pre_erasure` block is M2 measured twice and substitutes the correct comparator (`pre_erasure_block_note`). |

**Score:** 6/6 truths verified.

---

## Key Invariants — Independently Re-derived

Every row below was run in this verification process. None is taken from a SUMMARY.

| Invariant | Claimed | Measured | Status |
|---|---|---|---|
| `scripts/erasure_gate.py` commit count | 1 | `git log --follow` → **1** | ✓ |
| `scripts/erasure_gate.py` SHA / date | `23a830c`, 2026-08-12 | `23a830c0181acf…`, **2026-08-12 16:27:43 -0300** | ✓ |
| Gate predates Phase 16 running | yes | first `results/phase16_*` add **2026-08-12 17:00:27** — 33 min later | ✓ |
| Gate is an ancestor of HEAD | — | `merge-base --is-ancestor` → YES | ✓ |
| `scripts/phase19_erasure.py` commit count | 15 | **15** | ✓ |
| `scripts/phase19_erasure.py` sha256 | `c407246de3c4…6303` | `c407246de3c470094ab0bdd868961b7b1c22529c5e00522fec67c3852cb6e303` | ✓ |
| No commit to the pin from 19-08 onward | none | last touch `3ba3e2c` (19-07, 2026-08-18 09:13); `3ba3e2c..HEAD` on that path → **empty** | ✓ |
| `scripts/phase18_extraction.py` frozen | 26 | **26** | ✓ |
| `scripts/phase19_floor.py` commit count | 1 | **1** (`55009d0`) | ✓ |
| Ancestry guard green | yes | `tests/test_phase16_prereg.py` → **6 passed** | ✓ |
| Ancestry guard non-vacuous | 225 at 19-09 | recomputed today: **15 pin commits × 27 tracked artifacts = 405 pairs, 0 violations**; guard ties `bool(checked) == bool(tracked_artifacts)` so an empty match set goes RED once artifacts exist | ✓ |
| Ship decision line | `DO NOT SHIP` | present; matched against the pin's own `ERASURE_SHIP_DECISIONS` | ✓ |
| Marker pair | PENDING ×0 / RECORDED ×1 | checked against `ERASURE_SHIP_PENDING_LINE` / `ERASURE_SHIP_RECORDED_LINE` → **0 / 1** | ✓ |
| Working tree | — | `git status --porcelain` → **clean** | ✓ |
| Full suite | 845 passed, 1 skipped | `.venv/bin/python -m pytest -q` → **845 passed, 1 skipped, 187.68s** | ✓ |

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Verdict reproduces from committed artifacts through the committed gate | `erasure_succeeded(**raw values from phase19_target_scores.json)` | `FAILURE` + three reason strings byte-identical to report lines 11-13 | ✓ PASS |
| `TARGET_FLOOR` is exactly the perfect-erasure bound | `TARGET_FLOOR == wilson_upper_bound(0, 27)` | `True`, headroom `0.0` | ✓ PASS |
| Calibration set disjoint from taught set | `CALIBRATION_POOL & LOCKED_FACTS` | `set()` — 10 ∩ 8 = ∅ | ✓ PASS |
| Defect A blocks the pinned path (DO NOT SHIP claim) | pass on-disk `zero_results_have_nll=False` | returns **`INCONCLUSIVE`**, not FAILURE | ✓ PASS (claim true) |
| Defect D blocks the pinned path (DO NOT SHIP claim) | pass `retention_ppl_post` as the `[ppl, n]` pair | raises **`TypeError`** | ✓ PASS (claim true) |
| Pin ancestry over every artifact | 405 `merge-base --is-ancestor` calls | 0 violations | ✓ PASS |
| Phase-19 test files | `pytest tests/test_phase19_*.py` | **108 passed** | ✓ PASS |
| Full suite | `.venv/bin/python -m pytest -q` | **845 passed, 1 skipped** | ✓ PASS |

**The DO NOT SHIP decision is correct and I confirmed it adversarially.** Reproducing the verdict
required me to know that `zero_results_have_nll_order_normalised` is the field to read and that
`retention_ppl_post[0]` is the scalar. That is precisely the hand-driven knowledge the pinned CLI
does not have. The withheld claim is genuinely unavailable; withholding it was the honest call.

---

## Published Defects — each verified present where claimed

| Defect | Location in code | Published in | Verified |
|---|---|---|---|
| **A** — `zero_results_have_nll` ordered-tuple vs `sort_keys=True` | `phase19_erasure.py:1562` vs `:2948` | `phase19_calibration_correction.json` `defects.A`; `phase19_target_scores.json` `defect_a` + **both readings side by side** (`False` on disk / `True` order-normalised, 10 gaps / 0 gaps); report §"three published defects"; ship-decision §2 | ✓ code confirmed at both lines; both readings confirmed in the artifact; `INCONCLUSIVE` short-circuit reproduced |
| **B** — `_calibration_rate()` reads Phase 18 candidates | `phase19_erasure.py:3850-3855` | `phase19_calibration_correction.json` `defects.B` + `pin_internal_is_superseded: true`, `governs: corrected_target_floor`; `phase19_floor.py` docstring; report §"THREE numbers" | ✓ code confirmed reading `record["pre_erasure"]["per_fact"]`; both floors (0.2 superseded / 0.091079 governing) published with which governs |
| **C** — `rows.update(per_fact_rows(...))` tier collapse | `phase19_erasure.py:2922` | `phase19_calibration_correction.json` `defects.C`; report; recovery pinned as `test_the_pinned_report_subcommand_cannot_reach_the_committed_arm_records` | ✓ code confirmed; crash pinned as a green committed test |
| **D** (report's "a FOURTH") — `_cmd_report` passes `[ppl, n]` to a scalar param | `phase19_erasure.py:3811` | report §"three published defects" closing para; ship-decision §2 | ✓ code confirmed; `TypeError` reproduced |
| **E** (`reference_set_correction.md`'s "the FOURTH") — \|R\|=6 in the pin's `erase` subcommand | `phase19_erasure.py:3576` | `results/phase19_reference_set_correction.md`, own dated continuation, **with a full re-sweep**: k=78 under \|R\|=8 vs k=120 under the twin, all 78 addresses identical, `intact_nll` identical, dispersion census identical → nothing retracted | ✓ artifact `phase19_collateral_curve.json` independently carries `reference_set_size: 8`, `reference_set_source: "phase18_extraction.reference_set_for (NOT the calibration twin)"` **and** `calibration_twin_reference_set_size` beside it, so the defect is recorded in the data, not only in prose |

All five are published, none is silently fixed in the closed pin, and the D3 dated-continuation
discipline held. Treated as recorded limitations, per the phase's explicit and correct choice.

---

## Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|---|---|---|---|---|
| **ERASE-01** | 19-01…19-12, 19-14, 19-15, 19-16 (14 plans) | Selective erasure of a taught fact from the weights; goal framing fixed as auditable forgetting with a measurable bound, **not** indistinguishability | ✓ SATISFIED | `REQUIREMENTS.md:239` Traceability row, with 5 artifact paths. I opened all five: `phase19_arm_erased.json`, `phase19_collateral_curve.json` (k=78/288), `phase19_target_scores.json` (0/27, 1,296 draws, Wilson 0.091079), `phase19_representational_reads.json`, `phase19_erasure_report.md`. All three `ERASURE_GOAL_FRAMING` deliverables produced. No indistinguishability claim anywhere — the prohibition is a required *field* of the M2 record, not report prose. |
| **ERASE-02** | 19-06, 19-13, 19-15, 19-16 | TOFU-style retrain-without-the-forget-fact reference arm | ✓ SATISFIED | `REQUIREMENTS.md:240`. Discharged by a **run**: `wall=81s`, rc=0, adapter sha256 recorded, A2/K=48 with parity asserted. The ROADMAP's permitted written-explanation alternative is named explicitly as *not used*. |
| STAT-01 | 15 of 16 plans | Question as the unit of analysis, never the draw | ✓ SATISFIED | `phase19_target_scores.json` `unit: "question, never the draw"`; every published rate is `N/27 questions (… 1,296 draws)` |
| STAT-02 | 15 of 16 plans | Every proportion with a confidence bound and its denominator | ✓ SATISFIED | Wilson upper bound + denominator on every rate in report §2, §3 and the M2 table; rule-of-three published beside Wilson at zero |
| STAT-05 | 11 plans | Gate as a module-level literal in a committed driver, pushed before the run | ✓ SATISFIED | `erasure_gate.py` 1 commit predating Phase 16; `phase19_floor.py` literal assignments only, guarded by `test_floor_lock_holds_only_literal_constants_and_nothing_else`; ancestry enforced against git's object graph over 405 pairs |
| STAT-06 | 6 plans | Nothing gated that the sample size cannot support | ✓ SATISFIED | Representational read DESCRIPTIVE-only, AST-guarded with three mutation REDs; soft tier descriptive by declared narrowing; exposure descriptive and feeds no branch |

**Orphans:** none. All 28 in-scope v3.0 requirements are mapped (`REQUIREMENTS.md:242`).

### Is the ERASE-01 / ERASE-02 discharge adequate? — asked plainly, answered plainly

ERASE-01 is a scoped bullet at `REQUIREMENTS.md:179`, ERASE-02 at `:185`. Neither is a checkbox, so
`requirements mark-complete ERASE-01` returns `not_found`. Three agents declined to manufacture one.

**The discharge is adequate, and it is a stronger record than a ticked box would have been.** A
checkbox carries one bit. The Traceability rows carry the mechanism (M1 rank-1 ablation, 78 of 288),
the measured outcome (0/27 over 1,296 draws, Wilson `0.091079`, from 27/27), which conditions cleared
and which failed, the pin identity and call count (`erasure_succeeded` called exactly once against
`23a830c`, one commit, unamended), the three `ERASURE_GOAL_FRAMING` deliverables, and five artifact
paths. I opened all five and every number in the row is in the artifact it points at.
`REQUIREMENTS.md:174-177` declares the Traceability table the status of record for *every*
requirement, so these two are not being held to a weaker standard than the other 26 — they are being
held to the same one, with more evidence attached.

Declining to manufacture the checkbox was correct. Adding a `- [ ]` purely so a tool could tick it
would substitute a weaker record for a stronger one, and manufacturing an affordance to satisfy
tooling is the exact class of move this phase's entire discipline exists to refuse.

**The one real cost:** `mark-complete` can never confirm these two IDs, so any future tooling that
reads checkbox state will under-count v3.0 by two. Worth one line of note in REQUIREMENTS.md if that
tooling ever ships. Not worth converting the bullet.

---

## Anti-Patterns Found

| Scope | Pattern | Result | Severity |
|---|---|---|---|
| All 36 files touched since 2026-08-17 | `TBD` / `FIXME` / `XXX` | **zero** | — |
| `phase19_erasure.py`, `phase19_floor.py`, `phase19_run.py`, `phase14_recall.py`, 4 test files | `TODO` / `HACK` / `PLACEHOLDER` | zero real hits — all 15 "placeholder" matches refer to the ship-decision **marker** mechanism (`append_addendum` replaces exactly one placeholder line), which is the feature, not a stub | ℹ️ Info |
| Same | `coming soon` / `not yet implemented` | zero | — |
| `scripts/phase14_recall.py` modified during the phase | scoring-instrument change after numbers existed? | **No** — single commit `af214c7` at **19-06**, before the pin closed at 19-07 and 3 days before the target was scored. It threads `adapter_path` through `run_bit_identity_control` so the control provably reads the adapter it claims to (report line 220). Strengthens the audit rather than weakening it. | ℹ️ Info |

**Debt-marker gate: PASSED.** Zero unreferenced `TBD`/`FIXME`/`XXX` across every file this phase
touched. Completion is auditable.

---

## Findings for the operator

### W1 — PLAN frontmatter names five artifacts that exist under different names

`gsd-sdk query verify.artifacts` reports 5 missing artifacts across 19-08, 19-09, 19-12, 19-13:

| Plan predicted | Actually produced |
|---|---|
| `results/phase19_cal_corpus.json` | `results/phase19_calibration_corpus.json` |
| `checkpoints/phase19_cal_adapter.pt` | `checkpoints/phase19_erase_calibration_adapter.pt` |
| `results/phase19_calibration_arm.json` | `results/phase19_arm_cal-erased.json` |
| `results/phase19_arm_m1.json` | `results/phase19_arm_erased.json` |
| `results/phase19_arm_m2.json` | `results/phase19_arm_retrain.json` |
| `checkpoints/phase19_m2_retrain_adapter.pt` | `checkpoints/phase19_erase_reference_adapter.pt` |

Every one exists, is tracked, and I verified its contents. The names produced follow the pin's own
`_load_arm(arm)` convention (`phase19_arm_{arm}.json`), which was committed **before** the plans
guessed at names — so the code is right and the frontmatter is stale. Plus 19-16's `contains:
"Dated continuation"` misses only on capitalisation (the report has `(dated continuation,
2026-08-19)` at lines 355 and 468).

**Impact:** an automated must-have check on this phase reports 6 missing artifacts that all exist.
Cosmetic today, misleading to any future audit. Not a goal failure.

### W2 — `DO NOT SHIP` is absent from `docs/REPORT.md`

19-16 modified `docs/REPORT.md` and carried the result in properly: the `FAILURE` verdict with its
three reasons, the cliff headline, the rank-vs-NLL co-headline, the (c) diagnosis. It closes with a
bounded-claims list at `docs/REPORT.md:1229-1232` naming five bounds — one fact, one mechanism, one
adapter at 331,776 params, no relearning attack, retrain-is-a-different-adapter.

**That list does not include the reproducibility limitation.** `grep -n "DO NOT SHIP\|reproducib"`
over `docs/REPORT.md` returns nothing about Phase 19. A reader of the portfolio-facing document
alone learns the verdict but not that the pinned CLI cannot return it.

`results/phase19_erasure_report.md` §2 and `ROADMAP.md` both carry it in full, so nothing is hidden
from the record. And docs/REPORT.md does not *assert* the withheld claim, so it is not false. The
question is whether omission from the outward-facing artifact is a softening under this project's
own standard — *"this project does not ship the weaker claim under the stronger word."* That is an
editorial call, not a code fact. **Routed to the operator, not scored as a gap.**

### W3 — two different defects are each labelled "the fourth"

`results/phase19_reference_set_correction.md:20` calls the \|R\|=6 defect "This is the FOURTH pin
defect this phase." `results/phase19_erasure_report.md:191` calls the `retention_ppl` `[ppl, n]`
defect "A FOURTH, found by driving the path…". The ship decision then says "all four published
defects — **A**, **B**, **C** and the fourth", counting the second one.

Five distinct pin defects are published across two continuation documents; two carry the same
ordinal. Every defect is published in full with its own dated correction — nothing is missing. But a
reader reconciling the two documents will miscount. One clarifying sentence in either document fixes
it; under D3 that would itself be a dated continuation.

### I1 — Traceability phase column omits 19 for STAT-01/02/05/06

Fifteen of sixteen plans declare STAT-01, STAT-02, STAT-05 or STAT-06. The Traceability table reads
`16, 17, 18` for all four, and `REQUIREMENTS.md:251` declares that column "the authoritative
allocation." I verified all four hold substantively in Phase 19's artifacts (see the Requirements
Coverage table above). Documentation staleness in the allocation column, not an unmet requirement —
all four rows already read Complete.

---

## Key Link Verification

`gsd-sdk query verify.key-links` reports 9 unverified links. **I checked every one by hand and none
is a broken wire.** Breakdown:

| Reported failure | Actual cause | Real status |
|---|---|---|
| 19-05 `erasure_succeeded\(` | SDK: "Invalid regex pattern" — unescaped paren in the tool | WIRED — single call site at `phase19_erasure.py:1961` inside `render_verdict`, AST-enforced |
| 19-03 `wilson_upper_bound(0, N_TARGET_QUESTIONS)` | SDK resolved `scripts/erasure_gate.wilson_upper_bound` as a file path | WIRED — verbatim at `phase19_erasure.py:770` and `:822` |
| 19-14 `adapter_cells` | SDK searched a JSON artifact as the source file | WIRED — `scripts/extract_deltas.py:174` defines it, `phase19_erasure.py:1818` calls it |
| 19-07 `from: "the human"` | Pseudo-source; not a file | N/A — checkpoint gate |
| 19-08/09/12/13/16 "Source file not found" | Same naming drift as W1, plus `module.function` used as a path | WIRED — all targets verified present and called |

**Substantive key links, verified directly:**

| From | To | Via | Status |
|---|---|---|---|
| `phase19_erasure.render_verdict` | `erasure_gate.erasure_succeeded` | the one verdict call in the phase | ✓ WIRED — `sites == ["render_verdict"]`, identity-checked against the gate's object |
| `phase19_floor.TARGET_FLOOR` | `phase19_erasure.lock_erasure_floor` | re-derived on every suite run from the committed artifact | ✓ WIRED — `test_floor_lock_re_derives_all_three_constants_from_their_evidence_artifacts` green |
| `phase19_erasure` | `phase18_extraction.assert_phase18_parity` | asserted inside every arm run, not compared by eye | ✓ WIRED — 8 parity keys, corpus digest recomputed not pasted |
| `scripts/_addendum.append_addendum` | `results/phase19_erasure_report.md` | PENDING/RECORDED marker pair | ✓ WIRED — PENDING ×0, RECORDED ×1, decision line from the closed set |
| `phase19_erasure.delta_w_cosine` / `fisher_overlap` | *nothing* | must reach no gate | ✓ CORRECTLY UNWIRED — AST scan over producers, consumers in both files, and record keys |

---

## Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data? | Status |
|---|---|---|---|---|
| `phase19_erasure_report.md` §1 verdict | 3 reason strings | `erasure_succeeded` at `23a830c` | Yes — reproduced byte-identical from raw artifacts | ✓ FLOWING |
| `phase19_target_scores.json` | 0/27, per-tier 0/13 + 0/14 | `run_erasure_arm` A2/K=48 draws | Yes — 1,296 draws, pid + wall clock recorded | ✓ FLOWING |
| `phase19_floor.py` `TARGET_FLOOR` | `0.09107873950450847` | `lock_erasure_floor(0/23)` on `phase19_arm_cal-erased.json` | Yes — re-derives through the pinned function every suite run | ✓ FLOWING |
| `phase19_collateral_curve.json` | k=78, 8 checkpoints | `select_ablation_prefix` on `mps` | Yes — re-swept address-for-address, identical | ✓ FLOWING |
| `phase19_arm_retrain.json` | M2 scores | real 81 s training run | Yes — adapter sha256, training log, distinct pid | ✓ FLOWING |
| `phase19_representational_reads.json` | 6 reads with bounds | pinned `delta_w_cells` / `delta_w_cosine` | Yes — 108 cross-persona cosines, Fisher both denominators | ✓ FLOWING |

No hollow props, no static returns, no disconnected sources. Every published number traces to a
committed artifact produced by a recorded run with a pid, a wall clock and a git SHA.

---

## Gaps Summary

**No gaps.** All six roadmap success criteria are verified: each was measured under the rule
committed at `23a830c` before any v3.0 number existed, reported with its denominators and bounds,
and published unsoftened.

**The phase met its goal by producing a negative result, and the negative result is the achievement.**
The rule was written first. The calibration ran blind on a disjoint fact set, and the floor was
locked a full day before the target was ever scored — I confirmed both against git's object graph,
not against prose. The floor that came out of that calibration made (a) clearable only by a perfect
erasure, and a human approved that severity knowingly before seeing the target. The erasure then
cleared (a) exactly on its boundary with zero headroom, destroyed all seven gated non-targets, and
missed (c)'s dialogue cap. `erasure_succeeded` was called once and returned `FAILURE`. That FAILURE
is what shipped, at full strength, with the co-headline — that the rank instrument and the generation
instrument disagree on the same weights — published at equal weight and carrying an explicit
retroactive scope limit back onto Phase 18's own rank-based readings.

Then the phase did the harder thing: it withheld a claim it could not support. `DO NOT SHIP` retracts
no measurement and withholds exactly one assertion — that the verdict is mechanically reproducible by
the pinned CLI alone. **I verified that withholding is correct rather than performative.** Passing the
pin's on-disk `zero_results_have_nll` returns `INCONCLUSIVE`; passing the pin's own `retention_ppl`
pair raises `TypeError`. The pin genuinely cannot return this verdict, and the phase says so instead
of repairing the pin to make the claim true — which would have voided the pre-registration ordering
and every number resting on it.

Five pin defects are published, none silently fixed. Zero debt markers across 36 touched files. The
full suite is green at 845 passed, 1 skipped. Four documentation-level findings (W1, W2, W3, I1) are
recorded above; none blocks the goal, and W2 is an editorial judgement only the operator can make.

**Status is `human_needed`, not `passed`, for two reasons only:** the five checkpoint decisions were
made by a human and no grep can confirm a human made them, and W2 asks the operator to rule on
whether `docs/REPORT.md` must carry the reproducibility limitation. Nothing in the codebase is
missing, stubbed, or unwired.

---

_Verified: 2026-08-19T21:19:00Z_
_Verifier: Claude (gsd-verifier)_
