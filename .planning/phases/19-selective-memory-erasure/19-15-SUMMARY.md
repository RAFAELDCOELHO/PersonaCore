---
phase: 19-selective-memory-erasure
plan: 15
subsystem: the-verdict
tags: [erase-01, erase-02, stat-01, stat-02, stat-05, stat-06, one-verdict-path, closed-pin, defect-routing, cliff, rank-vs-nll, naming-failure-eight]

requires:
  - phase: 19-selective-memory-erasure
    provides: "the CLOSED 15-commit pin — `render_verdict`, `render_report`, `assert_erasure_report_not_clobbered`, `ERASURE_SHIP_PENDING_LINE`, `D8_PUBLICATION_POSTURE`, `per_fact_rows`, `nontarget_deltas`, `nontarget_noise_floor`, `dialogue_floor_from_record`, `lock_erasure_floor`, `literal_phase14_floor`, `floor_branch`, `zero_results_have_nll`, `_load_representational`, `PARITY_KEYS`"
  - phase: 19-selective-memory-erasure
    provides: "`scripts/erasure_gate.py` at `23a830c` — ONE commit, unamended: `erasure_succeeded`, `ERASURE_DECISION_RULE`, `ERASURE_GOAL_FRAMING`, `wilson_upper_bound`, `rule_of_three`"
  - phase: 19-selective-memory-erasure
    provides: "19-11's locked constants — `TARGET_FLOOR` `0.09107873950450847`, `NONTARGET_NOISE_FLOOR` `0.14814814814814814`, `DIALOGUE_PPL_NOISE_FLOOR` `0.005214448168350039`"
  - phase: 19-selective-memory-erasure
    provides: "19-12's M1 (`results/phase19_arm_erased.json`, `phase19_collateral_curve.json`, `phase19_target_scores.json`), 19-13's M2 (`phase19_arm_retrain.json`, `phase19_retrain_scores.json`), 19-14's representational pair, and `results/phase19_calibration_correction.json` — the record whose `governs` field names the floor"
  - phase: 18-extraction-attack-suite
    provides: "`results/phase18_arm_adapter-on.json` (the paired pre-erasure baseline) and `results/phase18_extraction_report.md` (the rank-1 baseline at `:145-153`, the mask direction at `:244`, the provenance standard at `:260-265`)"
provides:
  - "`results/phase19_erasure_report.md` — 353 lines, sha256 `21624251…`, the COMMITTED VERDICT and the twelve required readings"
  - "THE VERDICT: **FAILURE**, returned by `erasure_succeeded` called EXACTLY ONCE, against the CORRECTED floor `0.09107873950450847`"
  - "`scripts/phase19_run.py report` — the driver that routes around FOUR defects on the verdict path without editing the closed pin"
  - "the pooled-rows RECOVERY pinned as a committed test, beside 19-14's crash guard"
  - "STAT-05's verdict scan pointed at the UNPINNED driver, which the pin-source scan structurally cannot see"
affects: [19-16]

tech-stack:
  added: []
  patterns:
    - "a defect ON the success path is routed around at the ONE place it bites, with BOTH readings published, rather than normalised away silently or fixed in a closed file"
    - "a floor a gate reads is proved to be the PINNED rule's output on the corrected input before the gate is called — so the report cannot print a floor the gate did not read"
    - "a closed renderer's spine is APPENDED to, never spliced — splicing a file that carries a recorded verdict is a rewrite under cover of an append"
    - "a blocker guard and a recovery guard are committed as a PAIR: a guard that only records a blocker leaves the next reader to invent the fix"
    - "an AST scan that proves one file has one call site is pointed at the OTHER file too, because the file the report is actually rendered from is the one the first scan cannot see"

key-files:
  created:
    - results/phase19_erasure_report.md
    - .planning/phases/19-selective-memory-erasure/19-15-SUMMARY.md
  modified:
    - scripts/phase19_run.py
    - tests/test_phase19_erasure.py

key-decisions:
  - "THE VERDICT IS **FAILURE**, RETURNED BY THE COMMITTED RULE AND PUBLISHED UNSOFTENED. `erasure_succeeded` was called exactly once, through the pin's `render_verdict`, and returned FAILURE with three reasons: (a) upper bound 0.0911 over 27 questions <= floor 0.0911; (b) worst non-target degradation 1.000000 > 0.296296; (c) dialogue PPL 4.8511 vs cap 4.5837. Not paraphrased, not softened, not accompanied by a second opinion"
  - "THE VERDICT WAS READ AGAINST THE CORRECTED FLOOR `0.09107873950450847`, AND THE CORRECTNESS OF THAT NUMBER WAS PROVED RATHER THAN ASSERTED. The corrected blind rate `0.0` was read off `results/phase19_calibration_correction.json`, whose `governs` field was checked to say `corrected_target_floor`, and `lock_erasure_floor(0.0)` was asserted EQUAL to `phase19_floor.TARGET_FLOOR` through the PINNED rule before the gate saw either. The same rate was then handed to `render_report`, so its section 5 derives both floor directions from the same input the gate read — the report cannot print a floor the gate did not use"
  - "THE ORDER-NORMALISED `zero_results_have_nll` WAS PASSED, AND A PERFECT ERASURE IS THEREFORE NOT MISREPORTED. On disk the flag reads False on KEY ORDER alone (10 gap strings, 0 order-normalised, 48/48 NLLs finite across 8 slots). `erasure_succeeded` short-circuits to INCONCLUSIVE when `target_successes == 0` AND the flag is False — so the only outcome that can clear (a) is exactly the outcome defect A misreports. Passing the on-disk reading would have published INCONCLUSIVE for a key-ordering bug"
  - "A FOURTH DEFECT WAS FOUND BY DRIVING THE PATH, NOT BY INSPECTING IT. `_cmd_report` hands `post['retention_ppl']` — which `retention_perplexity` returns as `[ppl, n]` — straight into the gate's `retention_ppl=`, where `retention_ppl <= retention_cap` raises `TypeError: '<=' not supported between instances of 'list' and 'float'`. MEASURED this session by running the comparison. So `_cmd_report` carries a SECOND fatal defect behind the (b) one 19-14 pinned; the scalar `[0]` is passed here and the count travels beside it as the denominator"
  - "THE PINNED SPINE IS APPENDED TO, NEVER SPLICED. `render_report`'s section order is hard-coded and the pin is CLOSED, so six of the plan's twelve sections — the pre-registration chain, the collateral curve, the canary-exposure table, the M2 arm, the threats to validity and the provenance — have no slot inside it. Ten continuation sections were APPENDED after `## Ship Decision` under the same three proofs `scripts/_addendum.py` runs on produced bytes: the recorded `## Verdict` unchanged, the spine byte-identical as a prefix, and the pending line still occurring exactly once. Splicing them into the middle would have rewritten a file carrying a recorded verdict"
  - "ALL THREE FLOOR VALUES ARE NAMED IN THE REPORT, INCLUDING THE TWO THAT ARE BOTH 0.2 BY UNRELATED ROUTES. `TARGET_FLOOR` 0.09107873950450847 (branch `reachability-min`, GOVERNS); `LITERAL_PHASE14_FLOOR` 0.2 (D2's other direction, never read by a gate); and the PIN-INTERNAL 0.2 (`lock_erasure_floor(0.8846153846153846)`, branch `ceiling`, SUPERSEDED — defect B). Recomputed in-run through the pin's own functions rather than quoted, and published in one table with a sentence saying neither 0.2 corroborates the other"
  - "CONDITION (c) RAN LITERALLY AND `23a830c` WAS NOT TOUCHED. `git log -- scripts/erasure_gate.py` returns exactly one commit, `23a830c`. No cap was adjusted, no adapter-present baseline was substituted, no estimator was re-chosen. Both legs' PRE-erasure readings are printed beside the POST ones in the pinned section 4, which is the only thing separating a (c) failure that predates the erasure from one caused by it"
  - "EIGHTH PLAN-INSTRUCTION FAILURE THIS PHASE, AND THIS ONE IS A CASE FALLACY. The plan's Task-2 verify runs `grep -c 'Ship decision'`, which matches NEITHER of the pin's spellings: the heading `render_report` emits is `## Ship Decision` (2 matches) and `ERASURE_SHIP_PENDING_LINE` is `**Phase 19 ship decision: not yet recorded.**` (1 match). `grep -c 'Ship decision'` returns 0 and the command exits 1 on a report that satisfies every requirement it was checking"
  - "STAT-05'S SCAN NOW COVERS THE FILE THE REPORT IS ACTUALLY RENDERED FROM. `test_verdict_is_called_never_reimplemented` scans `_PIN_SOURCE`, which structurally cannot see `scripts/phase19_run.py` — the unpinned driver where 19-15's verdict call is made. A second evaluation assembled there would have been invisible. The new guard asserts the driver holds ZERO `erasure_succeeded` call sites, defines no such function, and calls `render_verdict` from exactly `report`, with an inline non-vacuity mutant"

requirements-completed: [ERASE-01, ERASE-02, STAT-01, STAT-02, STAT-06]

metrics:
  duration: "~1 h 15 min including the dry runs, the RED watch and the full suite"
  completed: 2026-08-19
---

# Phase 19 Plan 15: The Verdict — Summary

## THE VERDICT IS **FAILURE**

Returned by the committed `erasure_succeeded`, called exactly once, with its own reasons. Literal
return, pasted:

```
[phase19_run] VERDICT = FAILURE
    (a) target upper bound 0.0911 over 27 questions <= calibrated floor 0.0911
    (b) worst non-target degradation 1.000000 > k=2 x 0.148148 = 0.296296
    (c) dialogue PPL 4.8511 vs cap 4.5837; retention PPL 3.670918 vs cap 4.029000
```

**(a) CLEARS — perfectly, and exactly on its boundary.** 0/27 pooled questions (0/13 core_held_out,
0/14 core_taught) over 1,296 draws. Wilson upper bound `0.09107873950450847`, EXACTLY equal to the
governing `TARGET_FLOOR`, headroom `0.0`, branch `reachability-min`.

**(b) FAILS — all seven gated non-targets.** Margin `0.2962962962962963`. Four at total generation
loss. Smallest delta on the board is 2.5x the noise floor.

**(c) FAILS on the dialogue leg**, +0.26739025357374313 over cap. The retention leg clears at
−0.35808227467631326 — **and that clearing is the personalization being gone, not the erasure
succeeding.** Both legs were ALREADY RED on the untouched adapter (dialogue +1.2317, retention
+0.1908, measured 19-10, approved for literal publication 19-11), which is why the pre column is
printed beside the post one in every capability table.

**This is the result the phase was built to produce honestly.** A pre-registered gate returning
FAILURE is not a problem to be managed. It shipped in the register Phase 18 shipped
`LEAKAGE_DEMONSTRATED`, and no mitigating adjective the pinned `D8_PUBLICATION_POSTURE` does not
contain was added.

## The call, and its literal return

The call is `pin.render_verdict(...)` — the pin's single `erasure_succeeded` call site
(`scripts/phase19_erasure.py:1961`), which the 19-05 AST guard keeps the only one:

```python
verdict = pin.render_verdict(
    target_successes=target_row["n_answerable"],          # 0,  pooled 27 = 14 + 13
    target_questions=target_row["n_questions"],           # 27
    target_floor=floor.TARGET_FLOOR,                      # 0.09107873950450847  ← CORRECTED
    nontarget_deltas=deltas,                              # seven, GATED_NONTARGET_SLOTS order
    nontarget_noise_floor=floor.NONTARGET_NOISE_FLOOR,    # 0.14814814814814814
    dialogue_ppl=erased["dialogue_ppl"]["adapter_on"],    # 4.851119149910443
    dialogue_ppl_noise_floor=dialogue_floor,              # 0.005214448168350039
    retention_ppl=erased["retention_ppl"][0],             # 3.6709177253236867  ← scalar, not [ppl, n]
    zero_results_have_nll=flag_normalised,                # True  ← ORDER-NORMALISED
)
```

`erasure_succeeded` is called **zero** times in the driver, **once** in the pin. `erasure_gate.py`
itself carries the definition plus two `__main__` self-check calls. Measured:

```
scripts/phase19_run.py:0    scripts/phase19_erasure.py:1    scripts/erasure_gate.py:3
```

## The floor the verdict was read against — proved, not asserted

The pin's own `_calibration_rate()` is **published defect B**: it reads
`record["pre_erasure"]["per_fact"]`, i.e. Phase 18's CANDIDATE rows, and returns
`0.8846153846153846`, whose `lock_erasure_floor` is `0.2` on the `ceiling` branch. That is not the
governing floor.

The corrected blind rate `0.0` (0 successes over 23 calibration questions, 1,104 draws) was read off
`results/phase19_calibration_correction.json` — whose `governs` field was CHECKED to say
`corrected_target_floor` — and then proved to reproduce the locked constant through the **pinned**
rule before the gate saw anything:

```
lock_erasure_floor(0.0) = 0.09107873950450847 == phase19_floor.TARGET_FLOOR   → True
```

The same rate was handed to `render_report`, so its section 5 derives `lock_erasure_floor`,
`literal_phase14_floor` and `floor_branch` from the **same input the gate read**. The report
therefore cannot print a floor the gate did not use. Two further re-derivations ran in the same
guard block: the (b) scalar off the replicate arm through the pinned `nontarget_noise_floor`, and
the (c) scalar through `dialogue_floor_from_record` — both equal to their locked constants.

**All three floor values are named in the report, and two of them are 0.2 by unrelated routes:**

| number | value | route | read by a gate? |
|---|---|---|---|
| **`TARGET_FLOOR`** | **0.09107873950450847** | `lock_erasure_floor(0.0)`, branch `reachability-min` | **YES — GOVERNS** |
| `LITERAL_PHASE14_FLOOR` | 0.2 | `literal_phase14_floor(0.0)`, D2's other direction | no |
| the PIN-INTERNAL floor | 0.2 | `lock_erasure_floor(0.8846153846153846)`, branch `ceiling` | **NO — SUPERSEDED (defect B)** |

Against erasure's `<=` cap the SMALLER floor is the HARDER one, so the mirrored direction produced
the harder criterion and D2's "harder, never easier" holds by measurement. The report says in one
sentence that neither 0.2 corroborates the other.

## Four defects on this path, all four routed around, none fixed in the pin

| defect | reading | routing |
|---|---|---|
| **A** — key ORDER vs `sort_keys=True` | on disk **False**, order-normalised **True**; 10 gap strings vs **0**; **48/48** NLLs finite over 8 slots | the ORDER-NORMALISED flag was passed. Both readings published |
| **B** — `_calibration_rate()` | returns `0.8846153846153846`, floor `0.2` on the `ceiling` branch | the corrected rate `0.0` off the correction record, proved through the pinned rule |
| **C** — `rows.update` in the (b) position | committed `per_fact` counts are `[14]`, not the pooled `27` | pooled rows through the pin's own `per_fact_rows`, once per tier; `render_report` called directly |
| **D (NEW)** — `retention_ppl` shape | `[3.6709177253236867, 1000285]` handed where a scalar is compared | the scalar `[0]`; the count travels beside it as the denominator |

**Defect D was found by DRIVING, not by inspecting**, and it is a second fatal defect in
`_cmd_report` sitting behind the (b) one 19-14 pinned. Measured this session:

```
$ (the comparison erasure_succeeded makes, on the committed record's retention_ppl)
TypeError: '<=' not supported between instances of 'list' and 'float'
```

**The pin was not edited for any of them.** `scripts/phase19_erasure.py` is byte-identical at 15
commits, and `scripts/erasure_gate.py` still has exactly one commit — `23a830c`.

## `render_report` DRIVEN end to end on the real records

The pinned renderer completed against the ACTUAL committed arm records, curve, target scores,
retrain scores and representational read, writing 353 lines / 34,256 bytes. It is not a claim about
the path; the artifact is on disk with sha256
`21624251c20e57fd423fdbe1e8dd2b7d7939cab74406b400cc2ddabfe9d9108e`.

**The recovery is load-bearing, watched RED on the real path.** Handed the committed `per_fact`
rows instead of the pooled ones, `report()` dies at exactly the crash 19-14 pinned and writes
nothing:

```
SystemExit: [phase19_erasure] PROOF FAILED: pre-erasure fact 'cand_cat_zibby' carries 14 questions
against the pooled per-core-fact count 27.
```

`scripts/phase19_run.py` was verified byte-identical before and after that watch (the mutation lived
in a monkeypatched function object, never on disk), and the scratch output file was never created.

**Both halves are now committed as a pair.** 19-14 pinned the crash; this plan pins the recovery —
that `_pooled_rows` reconstitutes `N_TARGET_QUESTIONS` on the committed records, that the pooled
count is exactly the sum of its tiers, and that `nontarget_deltas` ACCEPTS the rows it SystemExits
on unpooled. A guard that only records a blocker leaves the next reader to invent the fix.

## The report's structure — the pinned spine, then ten appended continuations

`render_report`'s section order is hard-coded and the pin is CLOSED, so six of the plan's twelve
sections have no slot inside it. The spine is what the renderer produced, byte-identical; everything
after `## Ship Decision` is a continuation BESIDE the recorded verdict.

| in the pinned spine | appended |
|---|---|
| `## Verdict` §1 the verdict, §2 (a), §3 (b), §4 (c), §5 the floor, §6 representational | the two headlines; the pre-registration chain; the three floors; the four defects; the collateral curve; canary exposure + the soft tier; ERASE-02; the M1 representational read; threats to validity; provenance |
| `## Publication posture` (`D8_PUBLICATION_POSTURE`, verbatim) | |
| `## Comparability with Phase 18` (`PARITY_KEYS`) | |
| `## Ship Decision` — **PENDING, left for 19-16** | |

Appending rather than splicing was deliberate: splicing sections into the middle would rewrite a
file that now carries a recorded verdict, which is the "rewrite under cover of an append"
`scripts/_addendum.py` exists to refuse. The append runs the same three proofs on the produced
bytes — recorded `## Verdict` unchanged, the spine byte-identical as a prefix, the pending line
still occurring exactly once — plus the pin's OWN `_BARE_ZERO_PERCENT` regex rather than a second
copy of it.

**The ship-decision marker is left PENDING**, exactly once, so 19-16's `append_addendum` has an
unambiguous line to replace.

## The cliff, and the co-headline that carries equal weight

Both are rendered, and both were decided before their numbers existed.

**Headline 1 — selective erasure is NOT selective at 331,776 parameters.** k = 78 of 288 rank-1
components, dispersed across all six layers (18/12/12/17/10/9) and all six projections (fc_in 35,
fc_out 17, c_proj 13, v_proj 10, k_proj 2, q_proj 1). Largest single-layer share 0.2308, largest
single-projection share 0.4487. No structural localisation to confine an erasure to. Consequence
measured: all seven gated non-targets over the margin, four at total loss, and
**77.6370113463966%** of the dialogue adaptation gone (ON−OFF gap 1.2420966625043919 →
0.2777699357026435).

**Headline 2 — the rank instrument and the generation instrument DISAGREE, at equal weight.** The
report states the hardest form: **the rank instrument returns bit-identical readings for M1 and M2
across all eight slots** — identical `rank` AND identical `exposure_bits`, the target at (2, 2.0) in
both — while on the same two adapters `sibling_name` and `street` generate 0/27 under M1 and 27/27
under M2, and `person_name` generates 0/27 under M1 and 26/27 under M2.

**The retroactive weight on Phase 18 is stated with its scope limit**, as required: any Phase 18
reading whose weight rests on rank or exposure bits ALONE must be re-read with this in view, and
**Phase 18 readings paired with a generation number are unaffected** — the pairing is what makes
them safe, and this result is the argument for why the pairing was never optional.

The collateral curve is rendered as both readings in one table: no non-target rank moves off 1 at
any k, while every bystander's `ans1`/mean rises monotonically from the first checkpoint.

## Deviations from Plan

### The plan's Task-2 verify command fails on a report that satisfies it — EIGHTH failure this phase

**[Rule 1 — Bug]** `test $(grep -c 'Ship decision' results/phase19_erasure_report.md) -ge 1` matches
NEITHER spelling the pin emits. Measured:

```
'Ship decision'  -> 0
'Ship Decision'  -> 2     (the heading render_report writes)
'ship decision'  -> 1     (ERASURE_SHIP_PENDING_LINE)
```

The command exits 1 on a report where the ship-decision section renders once and the pending line
occurs exactly once. Run at the pin's own spellings, the whole Task-2 verify passes:

```
TASK-2 VERIFY (corrected spelling): PASS
```

### The plan's twelve-section order is not the pinned renderer's order

**[Rule 3 — Blocking]** The plan lists Verdict as section 10, Ship decision as 11 and Provenance as
12. `render_report` hard-codes `## Verdict` as the FIRST section after the title and `## Ship
Decision` as its LAST, and the pin is closed. The requirement was met, not dropped: every one of the
twelve readings is in the document, in the only order the closed renderer permits, with the six it
has no slot for appended after it. The plan's `results/phase19_arm_m1.json` naming trap did not
recur — every path was resolved from `pin.arm_record_path` and `pin.ERASURE_REPORT_PATH` before
anything was written.

### Auto-fixed issues

**[Rule 1 — Bug] The NLL census was counting frames, not readings.** The first draft rendered
`sum(len(e["nll"]) for e in exposure)` = 24, because `nll` is `{frame: {reduction: value}}` and
`len` counts the three frames. 19-12 and 19-13 both report 48. Fixed to count leaves; the report now
says 48 across 8 slots, matching Phase 18's bar.

**[Rule 1 — Bug] The dispersion census rendered as a header-only table.** `| by layer (0..5) | 18 |
… |` followed by a separator row produced a markdown table with no body. Restructured as a proper
two-row table with the layer indices as the header, and the two share statistics added beside it.

**[Rule 2 — Missing critical] The M1 representational read was absent from the report.** The PINNED
section 6 renders taught-vs-**M2**, so the rendered document contained no reading of the surgically
edited adapter at all — and the read that separates the ablated region (22 cells, 0.4764 … 0.9590)
from the preserved one (14 cells at 1.0 to fp64 round-off) is precisely the third instrument a
report whose co-headline is instruments disagreeing has to show. Added as a continuation section off
`results/phase19_representational_reads.json`, with all five reads, their n, their defined/undefined
counts, and the sentence that it adjudicates nothing.

**[Rule 1 — Bug] Three lint errors in the first draft** (one unused binding, two over-length lines),
fixed before the first commit.

### Nothing was weakened

The 19-15 diff is **1,278 insertions and ZERO deletions** across all three files. The descriptive-only
AST scan (`DESCRIPTIVE_ONLY_FUNCTIONS`, `test_representational_read_is_not_gated`) is unchanged — not
one character. `tests/test_phase16_prereg.py` is untouched and green. No `results/phase19_*` artifact
was removed, no adapter was moved or deleted, no `git add -f`, no worktree, no stash.

## Authentication Gates

None.

## Verification (fresh, this session)

- **Full suite: 845 passed, 1 skipped**, 83 warnings in **185.15s** — run after all three commits
  landed. (19-14's baseline was 842 passed / 1 skipped; the three new tests are this plan's.)
- **Lint:** `ruff check .` **All checks passed!**; `ruff format --check .` **170 files already
  formatted**.
- **Pin BYTE-IDENTICAL, UNTOUCHED:** `scripts/phase19_erasure.py` sha256
  **`c407246de3c470094ab0bdd868961b7b1c22529c5e00522fec67c3852cb6e303`**, **15 commits**.
  `scripts/phase18_extraction.py` still **26 commits**.
- **`23a830c` UNAMENDED:** `git log --format=%h -- scripts/erasure_gate.py` returns exactly
  **`23a830c`**, one commit.
- **The one verdict path:** `erasure_succeeded(` appears **0** times in `scripts/phase19_run.py`,
  **1** in `scripts/phase19_erasure.py` (inside `render_verdict`), and 3 in `erasure_gate.py` itself
  (the definition plus two `__main__` self-checks).
- **`results/phase19_erasure_report.md`:** 353 lines, 34,256 bytes, sha256
  **`21624251c20e57fd423fdbe1e8dd2b7d7939cab74406b400cc2ddabfe9d9108e`**, tracked. Exactly one
  `## Verdict` section, exactly one ship-decision placeholder.
- **STAT-02:** `grep -rn '0%' results/phase19_*` returns nothing.
- **All three adapters intact, never moved or deleted:** `checkpoints/persona_adapter.pt`
  **`226f2ae59938e389b396d999bc5f3e1e464874db5f3352d513dc5cd85984ebfb`**;
  `checkpoints/phase19_m1_erased_adapter.pt` **`13f593013746f24288febd3dc080894811c1c42c793f0a727e0ca21c1c55c6fc`**;
  `checkpoints/phase19_erase_reference_adapter.pt` **`22e66552e92ec7d5f853a6b8d15f350cfc0f127f20ee85aaec1967147c375b57`**.
- **Dry-run discipline:** the render was driven to completion twice into a scratch path, with
  `results/phase19_erasure_report.md` asserted ABSENT afterwards each time, before the real path was
  ever written — because `assert_erasure_report_not_clobbered` has no force flag and a half-written
  spine would have made the deliverable unrenderable without deleting evidence.
- Working tree clean.

## Carried Forward To 19-16

- **The ship-decision marker is PENDING and occurs exactly once.** `append_ship_decision` requires a
  DATED continuation carrying a line from `ERASURE_SHIP_DECISIONS` = `("SHIP", "DO NOT SHIP")`; a
  substring containing "ship" is not enough and will not flip the marker.
- **The report must be EXTENDED, never re-rendered.** `assert_erasure_report_not_clobbered` now has
  a recorded verdict to anchor on and there is no force flag — the only recovery is deleting the
  file in a reviewed commit.
- **`_cmd_report` carries TWO fatal defects, not one.** 19-14 pinned the (b) crash; defect D (the
  `[ppl, n]` retention pair) sits behind it and is unreachable until the first is fixed. Both are
  recorded in the report; neither can land in the closed pin.
- **The (c) diagnosis is 19-16's dated continuation**, published beside this verdict and never in
  place of it. `23a830c` stays unamended — `19-CONTEXT.md`'s Deferred Ideas puts any amendment
  permanently out of scope.
- **Eight plan-instruction failures now.** Read the constant, never the plan's spelling — and check
  the CASE of a grep against the constant that produces the text.

## Self-Check: PASSED

```
FOUND: results/phase19_erasure_report.md   (21624251..., 34,256 B, 353 lines, tracked)
FOUND: .planning/phases/19-selective-memory-erasure/19-15-SUMMARY.md
FOUND: checkpoints/persona_adapter.pt                   (226f2ae5... — INTACT)
FOUND: checkpoints/phase19_m1_erased_adapter.pt         (13f59301... — untouched)
FOUND: checkpoints/phase19_erase_reference_adapter.pt   (22e66552... — untouched)
FOUND commit: e10fa53  feat(19-15): the ONE verdict call, with all four defects on its path routed around
FOUND commit: 98df597  test(19-15): pin the pooled-rows RECOVERY beside 19-14's crash, and the driver's one verdict path
FOUND commit: 11736be  feat(19-15): render the report — the committed verdict is FAILURE, published unsoftened
```

Nothing was deleted or moved. The pin is byte-identical at 15 commits, `23a830c` is unamended at one
commit, and the descriptive-only AST scan is unweakened.
