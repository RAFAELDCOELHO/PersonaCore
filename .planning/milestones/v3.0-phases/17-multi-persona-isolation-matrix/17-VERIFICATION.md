---
phase: 17-multi-persona-isolation-matrix
verified: 2026-08-15T16:33:06Z
status: human_needed
score: 5/5 success criteria verified; 13/13 requirements evidenced
overrides_applied: 0
verified_at_commit: afd86ea
measured_baseline:
  collected: 652
  passed: 651
  skipped: 1
  exit_code: 0
human_verification:
  - test: "Decide whether §Categories in results/phase17_isolation_report.md is amended to state that the base row's base_prior and confabulation counts are ALSO structurally forced, not only leak and diagonal"
    expected: "A reader of §Categories cannot mistake `base | 0 | 0 | 104 | 0` for an empirical finding. Verifier proved all four counts are invariant under total mutation of the base completions."
    why_human: "Editorial decision on a published artifact. The defect is real and measured, but no must_have or Success Criterion requires the note to be complete, and amending a published report is a judgment call the developer owns."
  - test: "Decide whether the collateral-collapse limitation belongs in a published results/phase17_* artifact rather than only in planning docs"
    expected: "The +211.60%/+225.95%/+241.37% collapse and the 'NOT shippable demo substrate' conclusion are discoverable by a reader of the phase's published evidence."
    why_human: "Trade-off between report scope discipline (the report is deliberately about isolation only) and discoverability of a conclusion that constrains reuse of the seven Phase 17 adapters. No SC requires it."
  - test: "Correct the replay_ratio figure in 17-09-SUMMARY.md — it states Phase 14's real arm trained at replay_ratio=0.5; measured value is 1.0"
    expected: "The recorded limitation quotes the parameter value that teach_persona.py actually uses."
    why_human: "A wrong number inside a recorded limitation. Project practice is to retract weak prior numbers in place; the developer decides the retraction wording."
  - test: "Decide whether the two malformed YAML frontmatters (17-10-SUMMARY.md, 17-11-SUMMARY.md) are fixed"
    expected: "yaml.safe_load parses all 11 Phase 17 summary frontmatters."
    why_human: "GSD's file-glob detection still finds 11/11 summaries, so nothing is currently broken; whether to fix depends on which downstream consumers parse summary frontmatter."
---

# Phase 17: Multi-Persona Isolation Matrix — Verification Report

**Phase Goal:** Measure whether separately-taught personas stay isolated when they are built to
collide — N=3 adversarial personas with contradictory values in the *same* slots, scored as a full
cross-matrix against the base model's own prior
**Verified:** 2026-08-15T16:33:06Z at commit `afd86ea`
**Status:** human_needed
**Re-verification:** No — initial verification

## Headline: the gate was re-derived, not quoted

The claimed result (six Holm comparisons rejected at `p = 0.0078125`, `gate_cleared` → `True`) was
**independently re-derived by this verifier**, not read from prose. `gate_cleared` lives at
`scripts/phase17_personas.py:300` — not in the driver — and was fed the report's own six published
table rows, parsed out of the markdown:

| Check | Method | Result |
|---|---|---|
| `gate_cleared(published rows)` | Parsed the six rows from `results/phase17_isolation_report.md`, handed to the imported function | **`True`** |
| Family membership | Published cell pairs vs pre-registered `HOLM_FAMILY_CELLS` | Identical, symmetric difference `[]` |
| **Falsification — truncated family** | `gate_cleared(rows[:5])`, all five rejecting | **`False`** — correct |
| **Falsification — single non-rejection** | Flipped each of the six rows to `rejected=False`, one at a time | **`False`** in all 6 cases — correct |
| Holm step alphas | Re-derived `0.05 / (6 - i)` from scratch | Exact match to published `0.0083333 … 0.0500000` |
| `p = 0.0078125` | `phase16_persistence.sign_test_exact([1]*8)` called directly | `0.0078125` — real, not transcribed |
| Arithmetic independent of the `rejected` column | `p < alpha` recomputed per row | 6/6 agree with published |

The headline holds and the gate is not a rubber stamp: it fails closed on both a short family and
on any single non-rejection.

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC1 | W1 fixed (ISO-06) + adapter-swap canary (ISO-04) before any adapter trains | VERIFIED | ISO-06 AST guard **mutation-tested**: reverting `scripts/phase14_recall.py:557` to `LoRAConfig()` turned `test_every_inject_lora_consumer_reads_the_artifact_config` red (file restored, `git status` clean). ISO-04 `assert_sweeps_ran_on_distinct_weights` raised `SystemExit` on all 5 mutations: identical `lora_B`, shared pid, `base adapter_enabled=True`, split git SHA, dropped base record. No-op-swap shape confirmed by `test_no_op_swap_produces_the_recorded_shape` |
| SC2 | N=3 personas, contradictory values in the same slots, gate + human GO/ADAPT verdict (ISO-01) | VERIFIED | 24 minted values, **8/8 core slots fully contradictory** (3 distinct values each), all 24 unique, zero substring violations. `results/phase17_personas_report.md:744` carries `## Verdict` = **GO** with a human semantic read. `_require_go_verdict` **mutation-tested**: raises on `PENDING` and `STOP`, accepts `GO`/`ADAPT` (per SC2's own "GO/ADAPT" wording) |
| SC3 | N sweeps scored N ways, cell-blind scorer, adapter-off base column, confabulations separate (ISO-02, ISO-03) | VERIFIED | `score_completion(completion, slot_values)` — no cell argument. **Matrix re-derived from raw sweep JSONs by this verifier: all 12 cells match published exactly.** 4 distinct pids (72355/72803/73385/73652), one git SHA `b6b2fedd`, base `adapter_enabled=False`, identical `(slot, seed_index, question)` triple set across all four records. Confabulations own category (0, 1, 1) |
| SC4 | Within-run diagonal-vs-off-diagonal contrast, Holm not BH, no Phase 14 thresholds (STAT-03, ISO-07) | VERIFIED | See headline table. `0.2486` appears in no Phase 17 driver or report (only in the ISO-07 guard test that scans for it). The single `0.2000` hit is an unrelated mask-fraction statistic in the training log |
| SC5 | Worst pair replicated at k=3, descriptive only; zeros carry denominators and bounds; no aggregate rate (ISO-05, STAT-02, STAT-06) | VERIFIED | `worst_pair` **falsified correctly**: returns the tie-break `(a,b)` under the all-zero tie, but returns `(b,c)` when a genuine worst pair is injected. Replication JSON contains **no** `p_value`/`alpha`/`rejected`/`holm`/`sign_test` keys; min/max/median all `0.000000`. Append-only proved **from git**: 62 insertions / 1 deletion, that deletion being exactly the `not yet measured` placeholder. Every zero cell carries denominator, Wilson `0.025355`, rule-of-three at both clustering ends, cluster bootstrap. No aggregate rate anywhere |

**Score:** 5/5 Success Criteria verified.

### Re-derived Matrix (computed by this verifier from raw completions)

| row (adapter) | `persona_a` | `persona_b` | `persona_c` | matches published |
|---|---|---|---|---|
| `persona_a` | 104/104 | 0/104 | 0/104 | yes |
| `persona_b` | 0/104 | 103/104 | 0/104 | yes |
| `persona_c` | 0/104 | 0/104 | 103/104 | yes |
| `base` | 0/104 | 0/104 | 0/104 | yes |

All six off-diagonals are 0/104. Denominator 104 on every cell.

### Requirements Coverage — all 13 accounted for

The 17-01 over-claim was genuinely reverted: commit `2d91e5e` (17-01) marks **only ISO-07**, not
STAT-03 or ISO-05. Each requirement's final marking commit maps to a plan that legitimately claimed
it. Verified in **both** directions as instructed.

| Req | Marked complete by | Claimant plan | Direction check | Status |
|---|---|---|---|---|
| STAT-01 | carried from Phase 16 | 17-08 | Under-claim risk — verified Phase-17 evidence directly | SATISFIED — question unit declared on every rate; `test_signs_use_the_question_unit` |
| STAT-02 | carried from Phase 16 | 17-08, 17-10, 17-11 | Under-claim risk — verified directly | SATISFIED — denominator + Wilson + rule-of-three at both ends + bootstrap on every cell |
| STAT-03 | `1c97a10` (17-08) | 17-08 ✓ | Correct claimant (not 17-01) | SATISFIED — Holm re-derived independently |
| STAT-04 | carried from Phase 16 | 17-01 | Under-claim risk — verified directly | SATISFIED — `pyproject.toml`/`requirements.txt` untouched since prereg; all Phase 17 imports stdlib or first-party |
| STAT-05 | carried from Phase 16 | 17-01, 17-09 | Under-claim risk — verified directly | SATISFIED — **all 21** tracked `results/phase17_*` artifacts descend from prereg commit `d549e0b7`, verified by manual `git merge-base --is-ancestor` |
| STAT-06 | carried from Phase 16 | 17-01, 17-08, 17-10 | Under-claim risk — verified directly | SATISFIED — no aggregate rate over the 9 cells anywhere |
| ISO-01 | `07dfaf0` (17-07) | 17-03, 17-05, 17-07 ✓ | Correct | SATISFIED — GO verdict + 24 contradictory values |
| ISO-02 | `68033ab` (17-09) | 17-04, 17-06, 17-09 ✓ | Correct | SATISFIED — cell-blind scorer, matrix re-derived |
| ISO-03 | `68033ab` (17-09) | 17-04, 17-06, 17-08, 17-09 ✓ | Correct | SATISFIED — base column computed, `adapter_enabled=False` |
| ISO-04 | `68033ab` (17-09) | 17-06, 17-09 ✓ | Correct | SATISFIED — canary mutation-tested, bites on all 5 |
| ISO-05 | `bc48d94` (17-10) | 17-10, 17-11 ✓ | Correct claimant (not 17-01) | SATISFIED — k=3 replication, descriptive only |
| ISO-06 | `40bfa8e` (17-02) | 17-02 ✓ | Correct | SATISFIED — AST guard mutation-tested red |
| ISO-07 | `2d91e5e` (17-01) | 17-01 ✓ | Correct | SATISFIED — Phase 14 thresholds absent |

No orphaned requirements: the union of all 11 plans' `requirements` frontmatter is exactly the 13
IDs assigned to Phase 17 in ROADMAP.md.

### Known Limitations — confirmed recorded, not glossed

| Limitation | Recorded where | Verified |
|---|---|---|
| Collateral collapse +211.60% / +225.95% / +241.37% vs Phase 14's +27.16%; adapters **NOT shippable demo substrate** | `17-09-SUMMARY.md:293-310`, `17-10-SUMMARY.md`, `STATE.md:236` (extends it to the 4 replicate adapters) | Cause confirmed in code: `run_one_persona_training` (`scripts/phase17_isolation.py:1138-1143`) passes no `replay_ratio`, taking `train_arm`'s committed default `0.0` (`teach_persona.py:530`). Training log shows `replay_ratio=0.0`, `0 replay` tokens for all three. **See W2/W3 below** |
| D-13 base-prior anchor partial miss (`the country` reproduced, `rose` did not) | `results/phase17_isolation_report.md:63` — dated addendum | Commit `9fcfc50` confirmed: **27 insertions / 0 deletions**, pure supersession. The pre-committed "investigate this sweep" pointer is left in place above it |
| ISO-05 pair is a TIE-BREAK outcome, not a finding about persona_a/persona_b | Published addendum §The selection, and §Replication (ISO-05) | Both sections state it explicitly: *"an outcome of the rule, and NOT a finding about those two personas."* `tie_break_decided: true` in `results/phase17_replication.json`. `worst_pair` falsified — returns the real worst pair when one exists |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Full suite | `.venv/bin/python -m pytest -q` | **651 passed, 1 skipped** in 126.87s | PASS — matches stated baseline exactly |
| Collection | `pytest -q --collect-only` | **652 collected** | PASS |
| Phase 17 + guards | `pytest -q tests/test_phase17_*.py tests/test_phase16_prereg.py tests/test_lora_inject.py` | **79 passed**, exit 0 | PASS |
| Gate re-derivation | imported `gate_cleared` over published rows | `True`, falsifies correctly | PASS |
| Matrix re-derivation | committed scorer over raw sweep JSONs | 12/12 cells match | PASS |
| ISO-04 canary | 5 mutations of the sweep records | `SystemExit` on all 5 | PASS |
| ISO-06 AST guard | reverted a consumer to `LoRAConfig()` | test turned red; file restored, git clean | PASS |
| STAT-05 ordering | manual `git merge-base --is-ancestor` over 21 artifacts | 21/21 descend from prereg | PASS |

### Probe Execution

Step 7c: **SKIPPED** — no `scripts/*/tests/probe-*.sh` exists in this repository and no Phase 17
plan or summary references a probe. Verification used direct pytest execution and independent
re-derivation instead.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|---|---|---|---|
| all 11 phase-modified files | `TBD` / `FIXME` / `XXX` | — | **Zero found.** Debt-marker gate passes |
| all 11 phase-modified files | `TODO` / `HACK` / `PLACEHOLDER` | — | **Zero found** |
| `scripts/phase17_*.py` | stubs, `NotImplementedError`, `pass`-only bodies | — | **Zero found** |
| `results/phase17_isolation_report.md` | leftover `not yet measured` placeholder | — | **Zero found** — replaced by the pointer |

### Findings Requiring a Human Decision

**W1 — WR-01 confirmed and quantified: §Categories under-documents the forced base row.**
Empirically proved by mutation. Replacing every base completion with garbage, then with
persona_a's value, then with all three personas' values, the base row's four category counts never
moved:

| base sweep mutation | `diagonal` | `leak` | `base_prior` | `confabulation` | `cell_rates` base row |
|---|---|---|---|---|---|
| REAL data | 0 | 0 | 104 | 0 | [0, 0, 0] |
| all completions = garbage | 0 | 0 | 104 | 0 | [0, 0, 0] |
| all completions carry persona_a's value | 0 | 0 | 104 | 0 | **[104, 0, 0]** |
| all completions carry all three values | 0 | 0 | 104 | 0 | **[104, 104, 104]** |

The counts are invariant; `cell_rates` moves. This confirms the brief's expectation on both halves:
**§The Matrix base row (0/104) comes from `cell_rates` and is a genuine, unaffected measurement.**

The published note explains only that `leak` and `diagonal` are forced. It does not say
`base_prior=104` and `confabulation=0` are equally tautological — branch 4 tests
`normalize(completion) in base_texts`, and for the base row `base_texts` is the base's *own*
completion set, so self-membership makes branch 5 unreachable at the call site. A reader of
§Categories sees two of four columns explained as structural and would reasonably infer the other
two are empirical. They are not. **Assessment: the under-documentation does mislead a reader of
§Categories.** It affects no gate, no requirement and no published rate.

*Nuance the review does not state:* branch 5 IS reachable in `classify` considered in isolation
(`own=None`, empty labels, completion absent from `base_texts` → `confabulation`). The forcing is a
property of the **call site** in `assemble_matrix`, not of the function signature.

**W2 — The collateral-collapse limitation is absent from every published artifact.**
`grep -ciE 'collateral|replay_ratio'` returns **0** for `results/phase17_isolation_report.md` and
`results/phase17_personas_report.md`. It is recorded only in planning artifacts (17-09-SUMMARY,
17-10-SUMMARY, STATE.md). The brief's requirement — *recorded, not silently dropped* — is met; but
a reader of the phase's published evidence cannot discover that these seven adapters are not
shippable demo substrate. Relevant because ROADMAP Phase 18 depends on Phase 17 for optional
cross-persona attacks.

**W3 — Factual error inside that recorded limitation (measured, contradicts the brief).**
`17-09-SUMMARY.md:305` states Phase 14's real arm *"trained at `replay_ratio=0.5`"*. Measured:

```
teach_persona.py:129   REPLAY_ARM_RATIO = 1.0  # one replay token per teaching token
teach_persona.py:151   REAL_RUN_REPLAY_RATIO = REPLAY_ARM_RATIO
teach_persona.py:338   want = int(round(replay_ratio * teaching_tokens))
```

`1.0 × 10,018 = 10,018` replay tokens — which matches the summary's own quoted
`20,036 tokens = 10,018 teaching + 10,018 replay`. The mechanism and token counts are right; the
**parameter value is wrong by 2x** (0.5 is the resulting replay *fraction of total*, not the
`replay_ratio` argument). This figure was repeated in the verification brief, so the error has
already propagated once.

**W4 — TWO summaries have malformed YAML frontmatter, not one.** The brief flagged 17-11 only.

| File | Line | Defect |
|---|---|---|
| `17-10-SUMMARY.md` | 32-33 | `- the same append-only property proved twice: synthetically on the writer (17-11) and on the` + continuation — unquoted `: ` in a multi-line sequence item |
| `17-11-SUMMARY.md` | 43-44 | `- resolve_seed is NOT reused for replicate path resolution: it resolves an adapter path through` + continuation — same defect class |

`yaml.safe_load` raises `ScannerError` on both; the other 9 parse cleanly. All 11 SUMMARY files are
present on disk, so GSD's file-glob detection is unaffected (11/11 confirmed), but any
frontmatter-parsing consumer fails on these two.

**W5 — 8 open review warnings, 0 critical.** `17-REVIEW.md` status is `issues_found`; none are
resolved. WR-06 (`run_replicate_mode` accepts `PENDING`) is a latent weakening only — the recorded
verdict is **GO**, so no published artifact was produced under `PENDING`. WR-08 (the product
assertion in `test_phase16_prereg.py` is a tautology) is real, but the following `assert checked`
saves the guard from vacuity, and this verifier confirmed the ordering independently for all 21
artifacts.

### STATE.md Coherence (hand-edited during 17-10)

**Coherent.** Frontmatter and body agree:

| Field | Frontmatter | Body |
|---|---|---|
| Status | `status: verifying` | `Status: Phase complete — ready for phase verification` |
| Position | `stopped_at: Completed 17-10-PLAN.md — all 11 Phase 17 plans done` | `Phase: 17 — ALL 11 PLANS COMPLETE`, `Plan: 11 of 11` |
| Activity | `last_activity: "2026-08-15 -- 17-10 complete: ..."` | `Last activity:` — verbatim match |
| Progress | `completed_plans: 22 / total_plans: 22`, `percent: 33` | consistent (1 of 3 milestone phases closed; 17 still `verifying`) |

No corruption from the broken `gsd-sdk` state verbs is visible.

### Gaps Summary

**No gaps. The phase goal is achieved.** Every Success Criterion is verified against the codebase
and the published artifacts by independent re-derivation, not by reading SUMMARY claims. The
headline gate re-derives to `True` and fails closed under both falsification tests. The full 3x3
matrix plus base row re-derives cell-for-cell from raw completions. All 13 requirement IDs carry
shipped evidence, and the recorded 17-01 over-claim is confirmed reverted.

Status is `human_needed` rather than `passed` because four artifact-quality items need a developer
decision, not because any must-have failed:

1. W1 — §Categories under-documents a structurally forced row (measured; misleads a reader).
2. W2 — the collateral-collapse caveat lives only in planning docs.
3. W3 — a wrong `replay_ratio` figure inside that caveat (0.5 stated, 1.0 measured).
4. W4 — two malformed YAML frontmatters, one of which was previously unreported.

None blocks Phase 18. All four are documentation-integrity items in a phase whose entire value
rests on documentation integrity, which is why they are escalated rather than waived.

---

_Verified: 2026-08-15T16:33:06Z at commit afd86ea_
_Verifier: Claude (gsd-verifier) — goal-backward, FORCE stance_
_Every number in this report was measured by the verifier in this session. Nothing was taken from SUMMARY.md._

---

## Human Gate Discharged — 2026-08-15

The four items above were referred for a human decision. All four were decided and executed; this section records the discharge rather than editing the `human_needed` verdict above, which stands as what the verifier found.

| # | item | resolution | commit |
| --- | --- | --- | --- |
| 1 | collateral caveat absent from both published reports | appended to `results/phase17_isolation_report.md` and `results/phase17_personas_report.md`, below the protected cut | `1383773` |
| 2 | WR-01 under-documented in §Categories | precision note appended, recording the verifier's correction that the forcing is a CALL-SITE property (branch 5 IS reachable in `classify` alone) | `1383773` |
| 3 | `replay_ratio` stated as 0.5 | corrected to **1.0** at source (`teach_persona.py:129,151`); dated note records the earlier revision | `3c31648` |
| 4 | malformed SUMMARY frontmatters | **five** found, not two — 17-04, 17-05, 17-06, 17-10, 17-11; `yaml.safe_load` now passes 11/11 | `a260d96` |

**Post-resolution state, measured:** full suite `651 passed, 1 skipped`, exit `0`. `test_report_addendum_is_additive` passes — every byte above the replication placeholder is unchanged. The personas report's `## Verdict` section still reads `GO`, contains no `PENDING`, and `assert_report_not_clobbered` remains armed.

Item 4 exceeded its stated scope: two files were reported, five were malformed, in three variants of one class (colon-space in a sequence item, colon-space on a continuation line, and a reserved backtick starting a plain scalar). All five were repaired rather than the two named.
