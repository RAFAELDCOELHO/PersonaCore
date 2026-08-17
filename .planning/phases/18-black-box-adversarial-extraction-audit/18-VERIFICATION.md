---
phase: 18-black-box-adversarial-extraction-audit
verified: 2026-08-17T17:16:40Z
status: human_needed
score: 5/5 success criteria verified; 11/11 requirements evidenced
overrides_applied: 0
verified_at_commit: 39049a7
measured_baseline:
  collected: 728
  passed: 727
  skipped: 1
  exit_code: 0
human_verification:
  - test: "Record the Phase 18 ship decision. The report's `## Ship Decision` points at a dated continuation that does not contain one — the only continuation records D-21's exclusion. Use `append_addendum(EXTRACTION_REPORT_PATH, text, placeholder=EXTRACTION_SHIP_RECORDED_LINE)`; the default placeholder no longer occurs and `append_addendum` refuses at `found == 0`."
    expected: "A reader of `results/phase18_extraction_report.md` finds an actual ship/no-ship decision, not a pointer to a section about collateral collapse. `render_report` is never called — it would destroy LEAKAGE_DEMONSTRATED and every appended section."
    why_human: "A ship decision is a human judgement about a published privacy claim. The verifier can prove the pointer is broken and can prove which append path still works, but must not author the decision."
  - test: "Decide whether the report's `## Pre-Registration` paragraph is corrected by dated addendum. It attributes `K = 48`, `ASR_RUNGS (1, 4, 16, 48)`, the four attack templates, `null_result_is_admissible()` and the report generator to commit `13666c4`. Measured at that commit: the file is 272 lines, `K = 64`, `ASR_RUNGS = (1, 4, 16, K)`, and none of the templates, ladder, admissibility function or generator exist."
    expected: "A reader running `git show 13666c4:scripts/phase18_extraction.py` is not contradicted by the paragraph citing it. The ordering guarantee — which IS intact and is what the paragraph's next sentence actually claims — survives the correction."
    why_human: "Editorial decision on a write-once published artifact in a phase whose entire output is trust in a measurement. No Success Criterion or requirement requires the attribution sentence to be exact, and correcting it needs `append_addendum`, not a re-render."
  - test: "Bring the planning ledger into line with the executed phase: ROADMAP.md:455-456 still shows `- [ ] 18-15-PLAN.md` and `- [ ] 18-16-PLAN.md` unchecked, and STATE.md reads `stopped_at: Phase 18 context gathered`, `completed_plans: 22`, `Plan: 1 of 16`, `Status: Executing Phase 18`."
    expected: "The ledger reflects 16/16 plans complete and Phase 18 verifying/complete."
    why_human: "Explicitly excluded from this verifier's scope by the task brief — the developer sequences ROADMAP.md and STATE.md updates after reading this report."
---

# Phase 18: Black-Box Adversarial Extraction Audit — Verification Report

**Phase Goal:** Measure whether an adversary with black-box access can extract taught facts from the
adapter — and correct the claim wording so the demo's toggle reads as **availability, not
authorization**, which is the honest reading of what 36 boolean writes have always done
**Verified:** 2026-08-17T17:16:40Z at commit `39049a7`
**Status:** human_needed
**Re-verification:** No — initial verification

## Headline: the entire report was re-rendered, not read

The strongest available check was run first. This verifier reconstructed `run_report`'s whole
pipeline from the two committed arm JSONs — score, aggregate, ladder, curves, injection, uniques,
Holm family, verdict — and called the committed `render_report` into a **scratch path** (never
`results/`).

| Check | Result |
|---|---|
| Re-rendered prefix vs published prefix, byte-for-byte | **IDENTICAL — 48,511 bytes** |
| Re-rendered suffix vs published suffix | **IDENTICAL** |
| Only delta | the 2,403-byte 2026-08-17 dated addendum |
| Published artifact modified by this verification | **no** — `git status` clean throughout |

Every number in the published report body is re-derivable from the raw arm records by the committed
instruments. Nothing below was taken from a SUMMARY.

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC1 | Corpus programmatic from committed templates (A1/A2/A3), K as budget parameter not a fourth shape, no external API/hosted model, `assert_no_value_in_prompt` substring-aware across the entire corpus, A2's declared pre-registered injection budget with realized measured per prompt and only the unprompted remainder scored (ATK-01) | VERIFIED | 864 prompts = 216 core questions x 4 families; committed artifact **re-derives byte-identical** (`test_corpus_rederives_byte_identical` runs live, asserts existence rather than skipping). `ATTACK_FAMILIES` has exactly 4 members; K is `draw_all(n_samples=)`. `test_no_network_imports` passes. **Verifier swept all 864 committed prompts** through the frozen tokenizer and the clean-room guard: **0 violations even on the FULL ids including A2's injected tail** — stronger than D-16's partitioned requirement. Guard **mutation-proved substring-aware**: fires on `xxquillonxx`, silent on a clean prompt. Realized injection measured off the arm record — `hometown`/`street` = 2 on 27 prompts each, the other six = 1 on 27 each; **realized multiset == declared `[1,1,1,1,1,1,2,2]` exactly**. A2 is scored on `prefix_text + completion`, so the injected ids are not counted as extraction |
| SC2 | Attack family zero is a positive control — Phase 14's taught-template direct question at 0.4921; harness declared broken and no privacy statement admissible if it does not reproduce (ATK-03) | VERIFIED | `family_zero_matches` re-derived by this verifier from the raw arm record against `parse_phase14_taught_rows()`: **`(True, [])` — 0 of 112 per-question mismatches**. Derived totals **496/1008 over 112 questions** independently re-derived with a verifier-written predicate (0.492063 at the draw unit). **Falsified:** moving one hit between two questions returns **`False` with 2 named mismatches** while the derived totals stay `496/1008` — proving the vector, not the aggregate, is what is checked. `null_result_is_admissible(control_hit_vector_matches=False)` → **INCONCLUSIVE** |
| SC3 | No-adapter negative control at the *same* budget/prompts/seeds/`forbid_ids`/`stop_ids`; every ASR@{1,4,16,48} plus the cumulative curve reported on vs off, paired at the question level, denominator and bound; fact-level n=8 cluster resampling descriptive, Wilson labelled, `3/n` at zero, no bare `0%` (ATK-02, STAT-01, STAT-02, STAT-04, STAT-06) | VERIFIED | Both arms **42,480 draws** each — exactly `216x48x4 + 112x9`. Identical `corpus_sha256` `ff8e6e3c…` and `forbid_ids_sha256` `79b55770…`, **distinct pids 89185 / 9267**, one git SHA `c71bade5`. **All 32 published ladder cells re-derived exactly** from raw completions under BOTH the committed `contains_value` and a verifier-written naive predicate — the two agree cell-for-cell. Every adapter-off cell is 0/104 (held-out) and 0/112 (taught) at every rung. `grep` for a bare `0%` across every published artifact: **zero hits**. Rule-of-three `3/104 = 0.028846` and `3/8 = 0.375000` printed at both clustering ends on every zero cell |
| SC4 | Every zero-extraction target records its teacher-forced NLL; verdict returned by the committed `null_result_is_admissible()`, forcing INCONCLUSIVE unless the control passed, the budget was spent, the base arm was measured at the same budget and every zero carries an NLL; all verdict templates committed before the run (ATK-04, ATK-05, STAT-05) | VERIFIED | Exposure block: **8 slots x 3 frames x 2 reductions = 48 finite NLL values per arm, 0 `None`, 0 NaN/inf**, plus 8 ranks per arm (adapter-on all rank 1; adapter-off 3-5, the closed-book reading). **144 pre-registered admissibility cells; 73 measured zero and every one carries its rank** — re-derived, matching the published `(4)` reason verbatim. **Gate falsified on all four preconditions independently:** control failed → INCONCLUSIVE; `draws_spent=42479` → INCONCLUSIVE; base arm at 1000 draws → INCONCLUSIVE; one zero cell with `rank=None` → INCONCLUSIVE. All preconditions met with `attack_successes=0` → **NULL_ADMISSIBLE**, so the gate is genuinely one-directional and not a rubber stamp. `VERDICTS = ('LEAKAGE_DEMONSTRATED', 'NULL_ADMISSIBLE', 'INCONCLUSIVE')` present at the pin's add commit `13666c4`. **See W1 for the attribution defect** — the function itself was not at that commit, though it did precede every artifact |
| SC5 | README and `docs/REPORT.md` state the toggle as availability-not-authorization in one committed sentence reused verbatim (demo UI copy included), landed as a dated continuation; threats-to-validity records the LoRA-property caveat (ATK-06) | VERIFIED | **One** constant `TOGGLE_IS_AVAILABILITY` (`scripts/personalize_demo.py:317`), interpolated into the demo UI copy at lines 325 and 333, and present **verbatim** in `README.md:204` and `docs/REPORT.md:1026` — byte-compared by importing the constant, not by eye. Landed as dated continuations, not in-place edits: README `## Claim correction — what the memory toggle demonstrates (recorded 2026-08-16)` opening "**Appended, not edited.**", plus `docs/REPORT.md`'s `## Extraction Audit Result … (Phase 18, recorded 2026-08-17)` opening "*Appended additively. No line above this heading is altered.*" ATK-06's LoRA caveat (331,776 trainable parameters adapting a 13.9M base) appears in the report's Threats to Validity, in README and in `docs/REPORT.md` |

**Score:** 5/5 Success Criteria verified.

### Re-derived Ladder (computed by this verifier from raw completions, gated tier)

Question unit, denominator 104 on every cell. Both predicates agree on all 16 cells.

| family | arm | @1 | @4 | @16 | @48 |
|---|---|---|---|---|---|
| `A1-mild` | on | 46 | 59 | 73 | 87 |
| `A1-aggressive` | on | 1 | 5 | 15 | 30 |
| `A2` | on | 33 | 42 | 68 | **92** |
| `A3` | on | 56 | 69 | 81 | 85 |
| all four | off | 0 | 0 | 0 | **0** |

Best attack family by the pre-registered rule (highest question-unit rate on the gated tier, ties to
the earlier member), re-derived independently: **A2** at 92/104 = 0.884615.

### Phase 19 Handoff — measured, not quoted

| Check | Result |
|---|---|
| Handoff tuple from `_handoff_counts` over the re-derived counts | **`(92, 104, 0, 104)`** |
| `erasure_gate.erasure_is_worth_attempting(92, 104, 0, 104)` | **`(True, 'target recoverable: attack 92/104 (rate 0.8846, 95% lower bound 0.8231) exceeds the no-adapter base rate 0.0000 (0/104)')`** — string-identical to the published line |
| Falsify `(0, 104, 0, 104)` | `(False, 'MOOT: … nothing demonstrably extractable')` |
| Falsify `(92, 104, 92, 104)` | `(False, 'MOOT: …')` |
| Falsify `(5, 104, 4, 104)` | `(False, 'MOOT: …')` |

The gate returns True on the real numbers and fails closed on a null attack, on an equal base and on
a narrow margin. The four ints are the QUESTION unit, and the denominator was proved against a
derived quantity (`sum(n_questions)`), never a literal.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `results/phase18_corpus.json` | 864 prompts, byte-equality guard armed | VERIFIED | 864 prompts, 216/family, sha256 `ff8e6e3c…` matches the committed helper, the raw file bytes AND both arm records. `test_corpus_rederives_byte_identical` live |
| `results/phase18_arm_adapter-on.json` | attack arm at the declared budget | VERIFIED | 42,480 draws, 976 records, `adapter_enabled=True`, pid 89185, 246.5 min |
| `results/phase18_arm_adapter-off.json` | negative control at the identical budget | VERIFIED | 42,480 draws, 976 records, `adapter_enabled=False`, pid 9267, 270.1 min, same corpus + mask digests |
| `results/phase18_extraction_report.md` | verdict-bearing published evidence | VERIFIED (1 defect, W1; 1 broken pointer, W2) | 305 lines. Re-render byte-identical over 48,511 bytes |
| `results/phase18_preflight_report.md` | D-12 smoke, un-adapted base only, K evidence | VERIFIED | Four shapes measured (134.54-183.20 draws/min), non-overlap test against Phase 13/17 attractor priors, 168 NLL forward passes all finite, D-30 spread-0 control ran and agreed. Projection table totals **84,960 draws = 2 x 42,480**, matching what actually ran |
| `scripts/phase18_extraction.py` | the D-04 ancestry pin | VERIFIED | 4,867 lines, zero stubs, zero `NotImplementedError`, zero debt markers |
| `scripts/personalize_demo.py` | demo UI copy carries the committed sentence | VERIFIED | `TOGGLE_IS_AVAILABILITY` at :317, consumed at :325 and :333 |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| arm JSONs | published ladder | `score_records` → `asr_ladder` | WIRED | 32/32 cells re-derive exactly |
| arm JSONs | `## Verdict` | `assemble_verdict` → `null_result_is_admissible` | WIRED | `LEAKAGE_DEMONSTRATED` re-derived; falsifies to INCONCLUSIVE on each of the four preconditions |
| arm JSON (A0) | positive control | `family_zero_matches` vs `parse_phase14_taught_rows` | WIRED | `(True, [])`; falsifies on a single moved hit |
| question counts | Phase 19 | `_handoff_counts` → `erasure_is_worth_attempting` | WIRED | `(92, 104, 0, 104)` → `True`, message string-identical to the report |
| `TOGGLE_IS_AVAILABILITY` | README / docs/REPORT.md / demo UI | verbatim reuse | WIRED | Byte-identical in all three surfaces |
| pin commits | every `results/phase18_*` artifact | `git merge-base --is-ancestor` | WIRED | 3 pin commits x 4 artifacts = **12/12 ancestor checks pass** |
| `## Ship Decision` | a recorded decision | `append_addendum` pointer | **NOT_WIRED** | Pointer resolves to a section about D-21 collateral collapse. See W2 |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
|---|---|---|---|---|
| extraction report ladder tables | `ladders` | `asr_ladder` over `score_records(records["draws"])` | yes — 84,960 real completions | FLOWING |
| report `## Verdict` | `verdict["verdict"]` | `null_result_is_admissible` over measured admissibility inputs | yes — re-derived, falsifiable | FLOWING |
| report exposure table | `records["exposure"]` | 48 measured teacher-forced NLLs per arm | yes — all finite, no `None` | FLOWING |
| report `## Ship Decision` | the pointer line | `append_addendum`'s unconditional placeholder rewrite | **no** | **HOLLOW — the pointer names a section that carries no ship decision** |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Full suite | `.venv/bin/python -m pytest -q` (`make test`) | **727 passed, 1 skipped** in 153.94s, exit **0** | PASS |
| Collection | `pytest -q --collect-only` | **728 collected** | PASS |
| The one skip | `pytest -q -rs` | `test_train_loop.py::test_amp_fp16_smoke` — needs a CUDA GPU; unrelated to Phase 18 | PASS |
| Phase 18 + prereg guards | `pytest -q tests/test_phase18_*.py tests/test_phase16_prereg.py` | **75 passed**, exit 0 | PASS |
| Addendum guards | `pytest -q -k addendum` | **5 passed** | PASS |
| Full report re-render | committed `render_report` over the two arm JSONs into a scratch path | **byte-identical prefix, 48,511 bytes** | PASS |
| Clean-room guard sweep | verifier-written sweep of all 864 committed prompts | **0 violations**, even on A2's full ids | PASS |
| Guard substring-awareness | mutation with `xxquillonxx` | guard **fired**; silent on a clean prompt | PASS |
| Admissibility gate | 4 independent precondition mutations | **INCONCLUSIVE on all 4**; NULL_ADMISSIBLE at zero successes | PASS |
| Positive control | one hit moved between two questions | **False, 2 mismatches**, totals unchanged at 496/1008 | PASS |
| Remaining append path | `append_addendum(..., placeholder=EXTRACTION_SHIP_RECORDED_LINE)` on a **copy** | succeeded, prefix preserved, verdict unchanged | PASS |
| Working tree | `git status --porcelain` | empty, before and after every check | PASS |

### Probe Execution

Step 7c: **SKIPPED** — `find scripts -path '*/tests/probe-*.sh'` returns nothing, and no Phase 18
plan or summary references a probe. Verification used direct pytest execution, independent
re-derivation and mutation-based falsification instead.

### Requirements Coverage — 11/11 evidenced

The union of all 16 plans' `requirements` frontmatter is exactly the 11 IDs ROADMAP.md assigns to
Phase 18. **No orphans.** ATK-01..06 were marked complete by `68f7552` (18-16). STAT-01/02/04/05/06
are carried from Phase 16, so each was verified against Phase 18's own evidence directly rather than
accepted on the carry.

| Req | Status | Evidence measured by this verifier |
|---|---|---|
| ATK-01 | SATISFIED | 864-prompt corpus re-derives byte-identical from committed templates; `test_no_network_imports` passes; realized injection multiset == declared |
| ATK-02 | SATISFIED | 42,480 draws on the off arm at the identical corpus digest, mask digest and K; every gated cell 0/104, re-derived |
| ATK-03 | SATISFIED | `family_zero_matches` → `(True, [])`, 0 of 112; falsifies on one moved hit |
| ATK-04 | SATISFIED | 48 finite NLLs + 8 ranks per arm; 73 zero cells all carrying a rank |
| ATK-05 | SATISFIED | Committed one-directional gate RETURNED a verdict and forces INCONCLUSIVE on each of its four preconditions independently |
| ATK-06 | SATISFIED | One committed sentence verbatim in 3 surfaces + LoRA-capacity caveat in report, README and `docs/REPORT.md` |
| STAT-01 | SATISFIED | Question unit declared on every rate; `_handoff_counts` proves the denominator against a derived question count, not a literal |
| STAT-02 | SATISFIED | Every proportion carries denominator + Wilson (labelled as independence-assuming) + rule-of-three at zero, at BOTH clustering ends. **Zero bare `0%` across all published artifacts** |
| STAT-04 | SATISFIED | `pyproject.toml` / `requirements.txt` untouched during the whole phase (`git log --since=2026-08-15` on both: empty) |
| STAT-05 | SATISFIED | All 3 pin commits are ancestors of the first-add commit of all 4 result artifacts — 12/12 verified with `git merge-base --is-ancestor`. **See W1 for a prose defect that does not touch this property** |
| STAT-06 | SATISFIED | Cluster bootstrap, unique successes and exposure all labelled DESCRIPTIVE and structurally outside the Holm family; no branch reads the bootstrap bounds — `rejected` comes from `holm` alone |

### Anti-Patterns Found

| File set | Pattern | Severity | Impact |
|---|---|---|---|
| all 18 phase-modified non-planning files | `TBD` / `FIXME` / `XXX` | — | **Zero found.** Debt-marker gate passes |
| all 18 phase-modified non-planning files | `TODO` / `HACK` / `PLACEHOLDER` | — | **Zero found** |
| all 18 phase-modified non-planning files | "not yet implemented" / "coming soon" | — | **Zero found** |
| `scripts/phase18_extraction.py` | `pass`-only bodies, `NotImplementedError` | — | **Zero found** across 4,867 lines |
| all published artifacts | bare `0%` (STAT-02) | — | **Zero found** |

`deferred-items.md` records one out-of-scope discovery — a stale parenthetical in
`phase16_persistence.py:1605`'s docstring, correctly analysed as prose that no test reads. Legitimate
deferral, not a hidden gap.

### Findings Requiring a Human Decision

**W1 — The `## Pre-Registration` paragraph misattributes 6 of the 8 items it names.**
The report's opening paragraph states that "The four attack templates, `K = 48`, the A2 injection
budget, the ASR ladder rungs (1, 4, 16, 48), the Holm family, the verdict domain,
`null_result_is_admissible()` and the closing paragraph's own generator were all committed in
`scripts/phase18_extraction.py` at `13666c4`". Measured at `13666c4`:

| Named item | At `13666c4` |
|---|---|
| `K = 48` | **`K = 64`** |
| `ASR_RUNGS (1, 4, 16, 48)` | **`(1, 4, 16, K)` = (1, 4, 16, 64)** |
| the Holm family | present |
| the verdict domain | present |
| the A2 injection budget (`INJECTION_FRACTION`) | present |
| the four attack templates (`apply_a1`, `build_a2_prompt`, `build_a3_prompt`) | **absent** — landed in 18-04 |
| the ASR ladder | **absent** — landed in 18-08 (`3b1660f`) |
| `null_result_is_admissible()` | **absent** — landed in 18-07 (`836409a`) |
| the closing paragraph's generator (`licensed_conclusion`) | **absent** — landed in 18-07 (`84241d7`) |

The file was **272 lines** at `13666c4`; it is 4,867 today. `K` became 48 at `99716e0`
("feat(18-13): reduce K 64 -> 48 in the pin, on pre-flight evidence").

*Structural cause, not a typo:* `render_report` (lines 3973-3976) interpolates the **live** `K` and
`ASR_RUNGS` constants alongside `prereg_commit()`, which resolves the **earliest add** commit
(`--diff-filter=A`, oldest entry). The generator therefore pairs today's constant values with the
file's add commit and asserts a co-location that never existed.

*What is NOT affected, verified independently:* the load-bearing property is ordering, and it holds.
All three commits touching the pin are git ancestors of the first-add commit of all four
`results/phase18_*` artifacts (12/12 checks). The K reduction was itself a pre-registered checkpoint
— ROADMAP lists 18-13 as "measured throughput, the K decision" — taken on a pre-flight that D-12
restricts to the un-adapted base, so it gave zero preview of adapter-arm behaviour. D-04 explicitly
permits post-pin change as "a reviewed dated commit that reddens the guard". STAT-05's actual
requirement ("pushed before the run it judges") is satisfied. The paragraph's own next sentence
states the ancestry property correctly.

**Assessment: the first sentence does mislead a reader who checks it.** It affects no gate, no
requirement and no published number. It is the same class as Phase 17's W1/W3, and this project's
practice is to retract weak claims in place by dated note.

**W2 — The ship decision is CONFIRMED absent, and the default append path is exhausted.**
`## Ship Decision` reads *"recorded in the dated continuation at the end of this file."* The file's
only dated continuation is `## Dated continuation — 2026-08-17: D-21's exclusion, quantified`, which
records collateral-collapse magnitudes and contains no ship decision. Grep across the whole report
for ship/no-ship language returns only the section heading and the pointer line itself.

*Root cause, measured:* `append_addendum` (line 4326) builds
`before + EXTRACTION_SHIP_RECORDED_LINE + after` **unconditionally**, whatever the addendum
contains. Appending the D-21 quantification therefore silently converted "not yet recorded" into
"recorded in the dated continuation" without a decision ever being written. The 18-16 SUMMARY's own
self-check treats "pending ship-decision line absent, recorded form present exactly once" as a PASS,
which is why this did not surface during execution.

*Consequence, measured on a copy — the published artifact was not touched:*

| Path | Result |
|---|---|
| `EXTRACTION_SHIP_PENDING_LINE` occurrences in the report | **0** |
| `EXTRACTION_SHIP_RECORDED_LINE` occurrences | **1** |
| `append_addendum(path, text)` — the committed default | **REFUSED**: "carries 0 occurrence(s) of the placeholder line" |
| `append_addendum(path, text, placeholder=EXTRACTION_SHIP_RECORDED_LINE)` | **SUCCEEDS** — prefix preserved byte-identically, `LEAKAGE_DEMONSTRATED` unchanged |

The developer has exactly one working path, and it is not the obvious one. `render_report` must not
be used: `assert_extraction_report_not_clobbered` would refuse, and forcing past it would destroy
the verdict and both appended sections.

**W3 — Planning ledger is stale.** `ROADMAP.md:455-456` still shows `- [ ] 18-15-PLAN.md` and
`- [ ] 18-16-PLAN.md` unchecked though both are executed and committed (`9a923d6`, `6db37f7`,
`72470d7`, `68f7552`). `STATE.md` frontmatter reads `stopped_at: Phase 18 context gathered`,
`completed_plans: 22`, `percent: 58`; its body reads `Plan: 1 of 16` / `Status: Executing Phase 18`.
Left untouched per this task's explicit instruction that the developer sequences these updates.

### Claims Checked Against Committed Artifacts

Every load-bearing number the SUMMARYs and the report assert about themselves was re-measured:

| Claim | Source | Measured | Verdict |
|---|---|---|---|
| 42,480 draws per arm | report `## Verdict` (2) and (3) | 42,480 both arms | backed |
| 92/104 headline, A2 adapter-on `core_held_out` | report Conclusion | 92/104 under two independent predicates | backed |
| 0/104 adapter-off base | report ladder | 0/104 at every rung, all four families | backed |
| 496/1008 over 112 questions | report Positive Control | 496/1008 over 112 | backed |
| 0 of 112 per-question mismatches | report Positive Control | `(True, [])` | backed |
| 144 cells / 73 zeros / all carrying a rank | report `## Verdict` (4) | 144 / 73 / all | backed |
| `(92, 104, 0, 104)` handoff | report Phase 19 handoff | identical, gate returns True with the identical message string | backed |
| 48,511-byte byte-identical prefix | 18-16-SUMMARY additivity table | 48,511 | backed |
| Suite 727 passed / 1 skipped | 18-16-SUMMARY | 727 passed / 1 skipped / 728 collected / exit 0 | backed |
| `K = 48` … committed at `13666c4` | report `## Pre-Registration` | `K = 64` at that commit | **NOT backed — W1** |
| ship decision "recorded in the dated continuation" | report `## Ship Decision` | no ship decision in any continuation | **NOT backed — W2** |

### Gaps Summary

**No gaps. The phase goal is achieved.** All five Success Criteria are verified against the codebase
and the published artifacts by independent re-derivation, mutation and falsification — never by
reading a SUMMARY. The entire report body re-renders byte-identically from the raw arm records. The
headline `LEAKAGE_DEMONSTRATED` verdict is produced by a gate that fails closed on each of its four
preconditions independently, and the positive control fails closed on a single moved hit. All 11
requirement IDs carry shipped, re-measured evidence.

Status is `human_needed` rather than `passed` because three items need a developer decision, not
because any must-have failed:

1. **W2** — the ship decision the report claims to carry does not exist, and only one non-obvious
   append path remains open to record it.
2. **W1** — the pre-registration paragraph's commit attribution is measurably wrong for 6 of the 8
   items it names, in a phase whose entire value rests on the auditability of that ordering.
3. **W3** — ROADMAP and STATE have not been advanced past 18-14.

None blocks the Phase 19 handoff: `(92, 104, 0, 104)` is measured, consistent with both arm records,
and `erasure_is_worth_attempting` returns `True` on it.

---

_Verified: 2026-08-17T17:16:40Z at commit 39049a7_
_Verifier: Claude (gsd-verifier) — goal-backward, FORCE stance_
_Every number in this report was measured by the verifier in this session. Nothing was taken from SUMMARY.md. No published artifact was modified; the working tree was clean before and after._
