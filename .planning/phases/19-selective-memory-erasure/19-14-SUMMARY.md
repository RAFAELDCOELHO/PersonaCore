---
phase: 19-selective-memory-erasure
plan: 14
subsystem: representational-read
tags: [erase-01, stat-06, descriptive-only, not-gated, ast-guard, cross-persona, fisher-overlap, closed-pin, report-blocker]

requires:
  - phase: 19-selective-memory-erasure
    provides: "the CLOSED 15-commit pin — `REPRESENTATIONAL_READ_LABEL`, `DESCRIPTIVE_ONLY_FUNCTIONS`, `delta_w_cells`, `delta_w_cosine`, `fisher_overlap`, `_cmd_representational`, `REPRESENTATIONAL_RECORD_PATH`, `_load_representational`, `render_report`"
  - phase: 19-selective-memory-erasure
    provides: "19-12's M1 result — `results/phase19_arm_erased.json` (the 78 ablated addresses this read partitions on) and `checkpoints/phase19_m1_erased_adapter.pt`"
  - phase: 19-selective-memory-erasure
    provides: "19-13's M2 result — `checkpoints/phase19_erase_reference_adapter.pt`, the retrain the pinned cosine is taken against"
  - phase: 17-persona-isolation
    provides: "`checkpoints/phase17_persona_{a,b,c}_adapter.pt` — the n=3 the fourth clause names by name"
  - phase: 14-persona-teaching
    provides: "`checkpoints/persona_adapter.pt` (`226f2ae5…`, 1,350,523 B) and `checkpoints/convbase_slim.pt`, the W0 every ratio is taken against"
provides:
  - "`results/phase19_representational.json` (`fa123c90…`) — the PINNED record: 36-cell taught-vs-M2 ΔW cosine and the Fisher overlap at 22 ablated cells against 14 preserved"
  - "`results/phase19_representational_reads.json` — the DESCRIPTIVE companion: the taught-vs-M1 cosine partitioned by the pin's own ablated/preserved sets, the M1-vs-M2 cosine, the cross-persona cosine at n=3, and the Fisher limits as REQUIRED FIELDS"
  - "THE ΔW READ SEPARATES THE TWO REGIONS EXACTLY: 14 preserved cells at 1.0 to fp64 round-off, 22 ablated cells spanning 0.4764 … 0.9590 with one undefined"
  - "THE REPRESENTATIONAL READ DISTINGUISHES M1 FROM M2 WHERE THE RANK INSTRUMENT COULD NOT — reported as numbers, adjudicating nothing"
  - "A LIVE BLOCKER FOR 19-15: the pinned `report` subcommand SystemExits on the committed arm records (19-09's defect C in the (b) position), pinned as a committed test"
affects: [19-15, 19-16]

tech-stack:
  added: []
  patterns:
    - "a descriptive read is kept descriptive STRUCTURALLY at three layers — the producers by AST, the consumers by AST across both the pin and the unpinned driver, and the ARTIFACT by a key-name scan a source scan cannot reach"
    - "a guard's RED is watched on the REAL function's REAL source, mutated in memory, with the file's sha256 asserted unchanged in the same test — a hand-typed stub is free to stop resembling what it stands in for"
    - "a limitation that does not describe the measurement is recorded as FALSIFIED rather than dropped, so a later reader cannot import a discount the number does not carry"
    - "driving a renderer end to end means redirecting its path default, never letting a test produce a downstream plan's deliverable"
    - "a companion record proves it describes the same object by RECOMPUTING the pinned quantity and reproducing it cell for cell, rather than by citing the pinned file"

key-files:
  created:
    - results/phase19_representational.json
    - results/phase19_representational_reads.json
    - .planning/phases/19-selective-memory-erasure/19-14-SUMMARY.md
  modified:
    - scripts/phase19_run.py
    - tests/test_phase19_erasure.py
    - tests/test_phase16_prereg.py

key-decisions:
  - "THE ΔW READ SEPARATES THE ABLATED AND PRESERVED REGIONS EXACTLY, PER CELL. Taught vs M1, partitioned by the pin's OWN `ablated_cells`/`preserved_cells`: all 14 preserved cells read cosine 1.0 to fp64 round-off (min 0.9999999999999886, max 1.0000000000000169), and the 22 ablated cells span 0.47639907415543037 … 0.9590456893929075 (median 0.8123793589594848) with exactly one undefined. The undefined cell is `(5, 'fc_in')` — the ONE cell of 22 whose all 8 rank-1 components were ablated, so its ΔW is exactly zero and has no direction. The read's `None` lands precisely where the ablation census says it must"
  - "THE REPRESENTATIONAL READ DISTINGUISHES M1 FROM M2 WHERE THE RANK INSTRUMENT RETURNED BIT-IDENTICAL READINGS. Taught vs M2: 36 of 36 cells defined, every cosine in [0.8868463602142158, 0.9622065663322942], median 0.934733296993185. Taught vs M1: 35 defined, one undefined, min 0.47639907415543037. Two entirely different shapes on the same instrument, on the same pair of comparisons the exposure instrument reported as equal in every rank and every `exposure_bits` value across all eight slots. PUBLISHED AS THE NUMBERS THEY ARE — this read is DESCRIPTIVE and adjudicates nothing; it is not evidence that either mechanism is better, and no threshold separates the two shapes"
  - "THE FISHER OVERLAP: 22 ABLATED CELLS AT 1.6354876707549402 AGAINST 14 PRESERVED AT 0.51367324964733, both sides with their own denominator and no ratio published. The cache is mean-normalized, so these read as multiples of an average parameter's importance. Reported and not interpreted: the read cannot attribute mass to a component (it has no rank-1 resolution) and it is anchored at weights the ablation was not performed on"
  - "THE PLAN'S TWO NAMED FISHER LIMITS ARE BOTH FALSIFIED, AND THE FALSIFICATION TRAVELS AS A FIELD. The pinned path loads `checkpoints/fisher_tinystories.pt` anchored at `checkpoints/best.pt`; it does NOT estimate a Fisher over the persona bin, so `inject -> estimate -> mark trainability` never happens and P19-8's trap is never reached. Measured: the cache samples 512,000 tokens (2000 windows x 256) from `data/train.bin`'s 1,251,956,121, so window overlap is NEGLIGIBLE, not 'heavy on a 20,036-token bin'; and the corpus is TinyStories, which has no user turns for the no-mask limit to score. Four REAL limits recorded in their place, each with its measurement"
  - "THE PINNED `report` SUBCOMMAND CANNOT RUN AGAINST THE COMMITTED ARM RECORDS — MEASURED BY DRIVING IT, NOT INSPECTED. `_cmd_report` hands `post['per_fact']` to `nontarget_deltas`, and `_nontarget_rates` proves every row carries `N_TARGET_QUESTIONS` = 27 while the committed rows carry one tier's count (13 or 14). That is 19-09's published defect C in the (b) position, which `scripts/phase19_run.py`'s own module docstring already records as making the pinned (b) path unrunnable. 19-07 fixed four `report` crashes on SYNTHETIC records; this fifth one survived because nothing had driven it on the real ones. The pin is CLOSED, so 19-15 must assemble the pooled rows through `per_fact_rows` and call `render_report` directly. Pinned as a committed test so it is inherited, not rediscovered"
  - "THE RECORD SATISFIES `render_report`'s READS, PROVED BY DRIVING THE PINNED SUBCOMMAND WITH IT ON THE INPUT. Section 6 renders all 36 cosine cells and the Fisher line carrying `reduction`, `granularity`, `ablated_mean`, `n_ablated_cells`, `preserved_mean` and `n_preserved_cells` — the seven keys `_load_representational`'s docstring names. The committed test that already drove `report` used a HAND-BUILT representational fixture in a tmp_path; the file the pinned subcommand actually writes had never been on that path"
  - "THE PLAN'S ARTIFACT NAME IS RIGHT FOR THE FIRST TIME IN SEVEN PLANS — AND ITS VERIFY COMMAND IS STILL WRONG. `REPRESENTATIONAL_RECORD_PATH` resolves to exactly `results/phase19_representational.json`, so the six-plan naming streak ends. But the plan's Task-1 verify reads `d['status']`, `d['fisher_limits']` and `d['reads']` off that path, and `_cmd_representational` writes exactly four keys — `cosine`, `fisher`, `ablated_components`, `config` — with no extension point and no force flag. It raises `KeyError: 'status'`. The three demanded fields live in the companion, where the identical command passes"
  - "THE GUARD WAS WATCHED RED TWICE ON REAL PATHS, WITH BOTH FILES PROVED BYTE-IDENTICAL AFTERWARDS. (1) The REAL `delta_w_cosine`'s REAL source was mutated in memory with `if cosines > 0.5:` and the scan fired with `ordering comparison ['Gt']`; the pin's sha256 is asserted unchanged inside the same test, because the mutation lived in a string and was never written. (2) The consumer scan was driven RED against an ON-DISK mutation of the driver's real representational path and restored byte-identically — `0fa083a8b49ccd68c9c084dc5d8f24f708c3b8dfcbd99a62016c64c5fa35ac15` before and after"

requirements-completed: [ERASE-01, STAT-06]

metrics:
  duration: "pinned read 0.8 s; companion 1.1 s; session ~1 h including the guards and the report drives"
  completed: 2026-08-19
---

# Phase 19 Plan 14: The DESCRIPTIVE Representational Read — Summary

The ΔW read separates the ablated region from the preserved region exactly — 14 untouched cells at
cosine 1.0 to fp64 round-off against 22 edited ones spanning 0.4764 to 0.9590 — and it distinguishes
M1 from M2 where the rank instrument returned bit-identical readings. None of it reaches a gate, and
that is enforced at three layers rather than promised in prose.

## The read, per cell, with its n

Five reads, every one carrying its denominator. The pinned subcommand ran FIRST and owns the first
of them; the companion adds the four its four-key writer has no room for.

| read | n | defined | undefined | min | median | max |
|---|---|---|---|---|---|---|
| taught vs **M2 retrain** *(the pinned record)* | 36 cells | 36 | 0 | 0.8868463602142158 | 0.934733296993185 | 0.9622065663322942 |
| taught vs **M1 erased** | 36 cells | 35 | **1** | **0.47639907415543037** | 0.8863320227695015 | 1.0000000000000169 |
| — its **ablated** region | **22 cells** | 21 | 1 | 0.47639907415543037 | 0.8123793589594848 | 0.9590456893929075 |
| — its **preserved** region | **14 cells** | 14 | 0 | **0.9999999999999886** | 0.9999999999999999 | **1.0000000000000169** |
| **M1 vs M2** | 36 cells | 35 | 1 | 0.4532760063337228 | 0.840118957873893 | 0.9622065663322942 |
| **cross-persona**, n=3 personas / 3 pairs | 108 cosines | 108 | 0 | 0.05118319098287871 | 0.12534931989724518 | 0.3368681508113163 |

The ablated/preserved partition is the **pin's own**, read off `results/phase19_representational.json`
rather than re-derived: a second `select_ablation_prefix` sweep could stop somewhere the published
erasure never did, which is `_cmd_representational`'s stated reason for reading it back.

## The ΔW read distinguishes the two regions, per cell

**All 14 preserved cells read cosine 1.0 to fp64 round-off.** Not approximately — the spread is
0.9999999999999886 to 1.0000000000000169, which is round-off on a dot product of 147,456 to 589,824
fp64 terms:

| cell | cosine | | cell | cosine |
|---|---|---|---|---|
| (0, q_proj) | 1.0000000000000027 | | (4, k_proj) | **1.0** |
| (1, k_proj) | 1.000000000000013 | | (4, q_proj) | 0.9999999999999939 |
| (1, q_proj) | 1.0000000000000053 | | (4, v_proj) | 0.999999999999999 |
| (1, v_proj) | 1.0000000000000007 | | (5, c_proj) | 0.9999999999999918 |
| (2, k_proj) | 0.9999999999999954 | | (5, k_proj) | 0.9999999999999998 |
| (2, q_proj) | 1.0000000000000169 | | (5, q_proj) | 0.999999999999996 |
| (3, k_proj) | 0.9999999999999886 | | (5, v_proj) | 1.0000000000000078 |

The 22 ablated cells, in full:

| cell | cosine | | cell | cosine |
|---|---|---|---|---|
| (0, c_proj) | 0.851929580479837 | | (3, c_proj) | 0.733294751863513 |
| (0, fc_in) | **0.47639907415543037** | | (3, fc_in) | 0.785254365846873 |
| (0, fc_out) | 0.6572062413969334 | | (3, fc_out) | 0.763863343983479 |
| (0, k_proj) | 0.8488628658689261 | | (3, q_proj) | 0.9590456893929075 |
| (0, v_proj) | 0.8745869393364739 | | (3, v_proj) | 0.6079816827494126 |
| (1, c_proj) | 0.9530314871639681 | | (4, c_proj) | 0.8123793589594848 |
| (1, fc_in) | 0.49171580478157145 | | (4, fc_in) | 0.6746643187102502 |
| (1, fc_out) | 0.6614341556465002 | | (4, fc_out) | 0.8791826480720152 |
| (2, c_proj) | 0.8522759407896114 | | **(5, fc_in)** | **undefined** |
| (2, fc_in) | 0.8136595663240188 | | (5, fc_out) | 0.9188111836947392 |
| (2, fc_out) | 0.8863320227695015 | | | |
| (2, v_proj) | 0.7905307707691142 | | | |

**The one undefined cosine is an internal consistency check that passed.** `(5, 'fc_in')` is the
ONLY cell of the 22 whose **all 8** rank-1 components were ablated — the 78 addresses distribute
`{1: 3 cells, 2: 5, 3: 4, 4: 4, 5: 3, 7: 2, 8: 1}` — so its ΔW is exactly zero and has no direction.
`delta_w_cosine` returns `None` there rather than `0.0`, for its own stated reason: writing `0.0`
would publish the cell as ORTHOGONAL, a claim the arithmetic does not make. The read's single
`None` lands exactly where the ablation census says it must, and nowhere else.

## Where the two instruments differ — reported, not adjudicated

19-13 recorded that the rank instrument returns **bit-identical** readings for M1 and M2 across all
eight slots — identical `rank` AND identical `exposure_bits` — while M1's bystanders generate 0/27
and M2's generate 27/27. On the same two adapters, this read returns two different shapes:

| | taught vs M1 | taught vs M2 |
|---|---|---|
| cells with a defined cosine | **35 of 36** | **36 of 36** |
| minimum | **0.47639907415543037** | 0.8868463602142158 |
| cells at 1.0 (round-off) | **14** | 0 |

**This is DESCRIPTIVE and it adjudicates nothing.** It is not evidence that either mechanism is
better, no threshold separates the two shapes, and nothing downstream reads either number. It is
reported because `ERASURE_DECISION_RULE`'s fourth clause asks for representational consistency to be
reported with its bounds, and because a phase whose co-headline is two instruments disagreeing should
say plainly what a third one saw.

The two shapes are also what one would expect from the mechanisms: M1 is a surgical edit that leaves
14 cells untouched by construction, and M2 is a separate 200-step training run. That is the point at
which the description stops.

## Cross-persona, at the n the clause names

108 cosines over three pairs of the Phase 17 persona adapters, **n=3 personas** stated beside every
number because that is the exact n the pre-registration names as unable to support a threshold:

| pair | n | min | median | max |
|---|---|---|---|---|
| persona_a vs persona_b | 36 | 0.05983301059397933 | 0.11837481135342343 | 0.26796178926356734 |
| persona_a vs persona_c | 36 | 0.05118319098287871 | 0.1456475868766255 | 0.3368681508113163 |
| persona_b vs persona_c | 36 | 0.059770679394254456 | 0.1392853844200455 | 0.2958014595090707 |
| **pooled** | **108** | 0.05118319098287871 | 0.12534931989724518 | 0.3368681508113163 |

All six adapters read here carry the SAME base fingerprint (`04e724c6…`, step 4000,
val_loss 1.5235939979553224), so the cells are comparable cell-for-cell. Verified in-run, recorded as
a field.

## The Fisher overlap, and the four limits that actually describe it

| quantity | value |
|---|---|
| ablated cells | **22** |
| preserved cells | **14** |
| ablated mean | **1.6354876707549402** |
| preserved mean | **0.51367324964733** |
| reduction | `mean` (the cache is mean-normalized, so these read as multiples of an average parameter) |
| ratio | **not published** — dividing two means-of-means would weight a 384x384 attention cell equally with a 1536x384 MLP cell |

Both sides with their own denominator, straight out of the pin's `fisher_overlap`. **Reported and
not interpreted.** The four limits below are why; each is a REQUIRED FIELD of
`results/phase19_representational_reads.json` with its measurement beside it, not report prose.

| # | limit | measured |
|---|---|---|
| 1 | the Fisher is over the **PRETRAINING** corpus, not the persona teaching data — it scores importance for the TinyStories LM task, not for the taught facts | `data/train.bin`, 2000 windows x block 256, seed 1234, `empirical_diag_fisher/groundtruth_targets/mean_normalized` |
| 2 | it is **anchored at different weights** from the ones the ablation was performed on | anchor `best.pt` (`3a46815d…`, step 49000, val_loss 0.7378001868724823) vs the adapters' base (`04e724c6…`, step 4000, val_loss 1.5235939979553224); 1 distinct adapter base across all six |
| 3 | `estimate_fisher` has **no mask support** — every token of every sampled window is scored | its keyword-only signature is `['n_examples', 'block_size', 'device', 'seed', 'normalize']` |
| 4 | **no rank-1 resolution** — a cell counts as ablated when ANY of its rank-1 components was zeroed | 78 ablated components reduce to 22 ablated cells against 14 preserved |

## The plan's two Fisher limits are both FALSIFIED

The plan prescribed estimating a Fisher over the LoRA parameters of the taught adapter — inject,
estimate, THEN mark trainability — and named two limits to record. **The pinned path does none of
that.** `_cmd_representational` loads the committed `checkpoints/fisher_tinystories.pt` cache
anchored at `checkpoints/best.pt`; no estimation runs, so P19-8's `mark_only_lora_trainable` trap is
never reached. Recording the plan's limits would have published a discount the number does not carry.

| the plan named | measured, and falsified |
|---|---|
| "no mask support, so **USER TURNS are scored**" | the no-mask half holds structurally and is recorded as limit 3 — but its named consequence does not apply: this cache is over TinyStories, which has no user turns |
| "**heavy window overlap** on a 20,036-token bin (`data/persona_real_train.bin`)" | no Fisher over that bin exists on this path. The cache samples **512,000** tokens from `data/train.bin`'s **1,251,956,121**, so overlap is negligible rather than heavy |

Both are recorded in the artifact under `plan_named_limits_falsified`, so a later reader cannot
import them.

A second, structural reason the plan's Fisher could not be used even if it had been estimated:
`fisher_overlap` `_prove`s its input covers `extract_deltas.KEYS` exactly — the 36 base-model
`blocks.N.….weight` cells. A LoRA-parameter Fisher is keyed `…lora_A`/`…lora_B`, which
`extract_deltas.fisher_cells` cannot reduce. Building a second reduction outside the pin would have
put a second overlap statistic beside the pinned one under the same name, which is the defect this
phase spends its guards refusing.

## It reaches no gate — enforced at three layers, two of them watched RED on real paths

**Layer 1, the producers (19-05, unchanged).** `test_representational_read_is_not_gated` scans
`DESCRIPTIVE_ONLY_FUNCTIONS` = `('delta_w_cells', 'delta_w_cosine', 'fisher_overlap')` by AST for
ordering comparisons, `sign_test_exact`/`holm`/`wilson_upper_bound` calls, and reads of any
module-level number. **Unweakened — not one character of it changed.**

**Layer 2, the consumers (new).** The 19-05 scan covers the three producers; a threshold added by a
READER of the record would be invisible to it. `test_no_consumer_branch_reads_the_representational_numbers`
scans every module-level function in **the pin AND the unpinned driver** that references
`REPRESENTATIONAL_RECORD_PATH`, `REPRESENTATIONAL_READS_PATH` or `_load_representational`, and
asserts none holds an ordering comparison or an inferential call. It also asserts the pin's only
reader of the record is `_cmd_report`. This is Phase 18's "no branch anywhere reads these bounds —
`rejected` comes from `holm` alone" stated for this path.

**Layer 3, the artifact (new).** A source scan structurally cannot see JSON.
`test_the_committed_representational_records_carry_no_verdict_shaped_key` walks both committed
records and fails on any key ANYWHERE whose name matches
`verdict|passed|failed|pass_fail|succeed|success|threshold|gate|exceeds|above|below|significant|reject`.
It found one on its first run — the companion's own `not_gated` key, matching on `gate`. **That is
the scan working**, and the key was renamed to `descriptive_only` rather than the regex narrowed.

**The two RED watches, on real paths, both files proved byte-identical afterwards:**

| watched | how | result |
|---|---|---|
| the producer scan | the **REAL** `delta_w_cosine`'s **REAL** source mutated in memory with `if cosines > 0.5:` | fires; pin sha256 asserted unchanged **inside the same test** — the mutation lived in a string and was never written |
| the consumer scan | an **ON-DISK** mutation of the driver's real representational path | `AssertionError: a consumer in the driver branches on the representational read: ["representational_reads: ordering comparison ['Gt']"]` |

The driver's sha256 was `0fa083a8b49ccd68c9c084dc5d8f24f708c3b8dfcbd99a62016c64c5fa35ac15` **before**
the mutation and `0fa083a8b49ccd68c9c084dc5d8f24f708c3b8dfcbd99a62016c64c5fa35ac15` **after** the
restore, and the guard went green again in the same run.

The 19-05 non-vacuity drives a hand-typed stub named `delta_w_cosine`. A stub is free to stop
resembling the function it stands in for, which is why the new RED mutates the real source and
anchors on a line the test asserts still exists.

**No p-value was computed.** Zero calls to `sign_test_exact`, `holm` or `wilson_upper_bound` on this
path, in the pin or the driver — scanned by AST, not grepped.

## `report` DRIVEN, and it does not complete on the committed records

The ordering contract required driving `report` end to end after writing the record. Driven, and the
result is a **live blocker for 19-15**:

```
scripts/phase19_erasure.py:3793  in _cmd_report
    deltas = nontarget_deltas(nontarget_pre, nontarget_post)
scripts/phase19_erasure.py:1353  in nontarget_deltas
scripts/phase19_erasure.py:1308  in _nontarget_rates
SystemExit: [phase19_erasure] PROOF FAILED: pre-erasure fact 'cand_cat_zibby' carries 13 questions
against the pooled per-core-fact count 27. `erasure_gate`'s clustering note fixes the unit as the
QUESTION and never the draw, and a draw-unit denominator is K times too large — every (b) delta
computed from it would be divided by the wrong number
```

This is **19-09's published defect C in the (b) position**, which `scripts/phase19_run.py`'s own
module docstring (reason 5) already records as making the pinned (b) path unrunnable: the committed
`per_fact` rows carry ONE TIER's count (measured: `{14}` post, 13 pre for the same fact) rather than
D5's pooled 27, because `run_erasure_arm`'s `rows.update(per_fact_rows(...))` loop lets one tier
overwrite the other.

**19-07 fixed four `report` crashes; this fifth survived because 19-07's test drove it on SYNTHETIC
records**, whose `per_fact` rows happen to carry 27. It is now pinned as
`test_the_pinned_report_subcommand_cannot_reach_the_committed_arm_records`, with a counter-assertion
that fails if the committed rows ever DO carry 27 — so the guard is rewritten rather than silently
outlived. **The pin is CLOSED at 15 commits, so the fix cannot land in `_cmd_report`: 19-15 must
assemble the pooled rows through the pin's own `per_fact_rows` (once per tier, as `_pooled_rows`
already does) and call `render_report` directly.**

**Separately, and this is what the ordering contract was actually protecting:** the record this plan
produced DOES satisfy `render_report`'s reads. `test_report_renders_section_6_from_the_committed_representational_record`
drives the pinned `_cmd_report` with the **real** `results/phase19_representational.json` on its
input — the committed 19-07 test used a hand-built fixture in a `tmp_path`, so the file the pinned
subcommand actually writes had never been on that path. Section 6 renders **all 36 cosine cells** and
the Fisher line carrying `reduction`, `granularity`, `ablated_mean`, `n_ablated_cells`,
`preserved_mean` and `n_preserved_cells`.

Both tests redirect `render_report`'s `path` (bound at def time, so the CALL is redirected) and
assert `results/phase19_erasure_report.md` is **still absent** afterwards. That file is 19-15's
deliverable and `assert_erasure_report_not_clobbered` has no force flag: a test that wrote it would
leave 19-15 unable to render without deleting evidence in a reviewed commit. Verified on disk after
the full suite: **the file does not exist.**

## Deviations from Plan

### The naming streak ends — and the verify command is still wrong

**`results/phase19_representational.json` is CORRECT.** `REPRESENTATIONAL_RECORD_PATH` resolves to
exactly the path the plan frontmatter names. After six consecutive plans whose artifact names the
pin refused, this one matches. Resolved from the constant before anything was written, as standing
instruction requires.

**[Rule 1 — Bug] The plan's Task-1 verify command cannot pass at that path.** It asserts
`d['status'] == 'DESCRIPTIVE'`, `d['fisher_limits']` and `all('n' in v for v in d['reads'].values())`.
`_cmd_representational` writes exactly four keys — `cosine`, `fisher`, `ablated_components`,
`config` — with no extension point and a `_prove` refusing a second run. Measured:

```
$ .venv/bin/python -c "...json.load(open('results/phase19_representational.json'))...['status']..."
KeyError: 'status'

$ (the identical command against results/phase19_representational_reads.json)
['cross_persona', 'fisher_overlap', 'm1_erased_vs_m2_retrain', 'taught_vs_m1_erased', 'taught_vs_m2_retrain']
```

**The requirement was met, not dropped**, in 19-13's register: the three demanded fields moved to the
companion, the pinned schema was not widened and the pin was not edited. `_load_representational`
checks its two keys by SUBSET, so the pinned record remains valid input to `render_report` unchanged.

**[Rule 3 — Blocking] The plan's Task-2 verify command deselects almost everything it names.**
`pytest -q tests/test_phase19_erasure.py -k descriptive tests/test_phase16_prereg.py tests/test_package.py -x`
applies `-k descriptive` across ALL the given paths, so it runs **1 test and deselects 109**,
including the whole of `test_phase16_prereg.py` and `test_package.py`. Run without the filter, the
three files are **110 passed**.

### The pinned cosine is against M2, not M1 — so the plan's headline read was missing

The plan asked for a three-way cosine "so the surgical edit and the retrain can be seen against the
same baseline". `_cmd_representational` computes taught-vs-M2 only. The pinned record therefore
contains **no reading of the surgically edited adapter at all**, and its ablated/preserved partition
is a *Fisher* partition, never a ΔW one — so the must_have "the ΔW read distinguishes the ablated
region from the preserved region, per cell" is not satisfiable from the pinned record alone. The
companion supplies taught-vs-M1 and M1-vs-M2 through the SAME pinned `delta_w_cells` /
`delta_w_cosine` functions the guard scans, partitioned by the pin's own cell sets.

The companion proves it describes the same object rather than asserting it: it **recomputes** the
taught-vs-M2 cosine and refuses to write unless it reproduces the pinned record **cell for cell**.
It did (`taught_vs_m2_round_trip_reproduced: true`).

### The artifact guard caught my own key on its first run

`not_gated` matched the scan's `gate` alternative. Renamed to `descriptive_only` and the record
regenerated, rather than narrowing the regex — a blunt regex over key names is the feature. The
record's own string value is unchanged.

### Auto-fixed issues

**[Rule 2 — Missing critical] The companion had no ancestry guard.** `PHASE19_TARGET_ARTIFACT_GLOBS`
names exact paths, so `results/phase19_representational_reads.json` matched nothing and would have
been a Phase 19 target artifact no guard watched — the exact gap that tuple's own docstring says it
exists to close. Added by name, in the same commit as the guards over it.
`tests/test_phase16_prereg.py`: **6 passed**, ancestry green.

**[Rule 1 — Bug, self-inflicted and repaired] `deferred-items.md` was truncated and restored.**
Logging this plan's one deferred item, the file was written rather than appended to, discarding
19-10's committed entry on `perplexity.py`'s stale denominator docstring. Caught immediately by the
diff (`-42/+12`), restored from `HEAD` and re-appended: the file is now **+14 insertions, 0
deletions** against `HEAD`. Nothing was lost. The correct move for an existing record is to extend
it, which is the same discipline 19-12 applied to `results/phase19_reference_set_correction.md`.

**Stray tool-call scaffolding in this SUMMARY, caught before the commit.** Two literal closing tags
had leaked onto the end of this file; stripped in place. `19-13-SUMMARY.md` has the same defect and
is logged in `deferred-items.md` rather than edited — it is a committed artifact of another plan and
nothing here touched it.

## Authentication Gates

None.

## Verification (fresh, this session)

- **Full suite: 842 passed, 1 skipped**, 83 warnings in **186.69s** — run after both artifacts and
  all four guards landed. (Previous session's baseline was 837 passed / 1 skipped; the five new
  tests are this plan's.)
- **Lint:** `ruff check .` **All checks passed!**; `ruff format --check .` **170 files already
  formatted**.
- **Pin BYTE-IDENTICAL, UNTOUCHED:** `scripts/phase19_erasure.py` sha256
  **`c407246de3c470094ab0bdd868961b7b1c22529c5e00522fec67c3852cb6e303`**, **15 commits**.
  `scripts/phase18_extraction.py` still **26 commits**.
- **`tests/test_phase16_prereg.py`: 6 passed** with the new glob entry.
- **All three adapters intact, never moved or deleted:**
  `checkpoints/persona_adapter.pt` **`226f2ae59938e389b396d999bc5f3e1e464874db5f3352d513dc5cd85984ebfb`**,
  1,350,523 B; `checkpoints/phase19_m1_erased_adapter.pt`
  **`13f593013746f24288febd3dc080894811c1c42c793f0a727e0ca21c1c55c6fc`**;
  `checkpoints/phase19_erase_reference_adapter.pt`
  **`22e66552e92ec7d5f853a6b8d15f350cfc0f127f20ee85aaec1967147c375b57`**.
- **Artifacts:** `results/phase19_representational.json` sha256
  **`fa123c90edf14e6c0f74f178cc21d5a0c7ea40e51aac13124af90f9485f7eb02`**, 7,841 B;
  `results/phase19_representational_reads.json` 23,070 B. Both tracked.
- **`results/phase19_erasure_report.md` does not exist** — 19-15's deliverable, unwritten.
- **Reproducibility:** regenerating the entire companion read from scratch produced a byte-identical
  artifact apart from the recorded `config.git_sha`. The regenerated copy is the one committed.
- `grep -rn '0%' results/phase19_*` returns nothing (STAT-02).
- No `git rm` of any `results/phase19_*` artifact; no `git add -f`; no worktree, no stash.

## Carried Forward To 19-15

- **`_cmd_report` CANNOT BE USED.** It SystemExits on the committed arm records at defect C. Assemble
  the pooled 27 = 14 + 13 rows through the pin's own `per_fact_rows` (once per tier) and call
  `render_report` directly. Pinned as a test so this is inherited, not rediscovered.
- **Read the ORDER-NORMALISED `zero_results_have_nll` on BOTH arms** and say so — 19-12's and
  19-13's standing instruction, unchanged. `_cmd_report` passes the on-disk reading, which reports
  a perfect erasure as INCONCLUSIVE.
- **Section 6 renders from the committed record unchanged** — all 36 cells and both Fisher
  denominators, proved by driving it.
- **These numbers reach no gate, and three committed scans now enforce that** across the producers,
  the consumers in both files, and the artifacts. Any 19-15 line that compares one of them against
  anything turns two of the three red.
- **Do not carry the plan's two Fisher limits forward.** Both are falsified in the record; the four
  that describe the measurement are fields of `results/phase19_representational_reads.json`.

## Self-Check: PASSED

```
FOUND: results/phase19_representational.json            (fa123c90..., 7,841 B, tracked)
FOUND: results/phase19_representational_reads.json      (23,070 B, tracked)
FOUND: .planning/phases/19-selective-memory-erasure/19-14-SUMMARY.md
FOUND: checkpoints/persona_adapter.pt                   (226f2ae5..., 1,350,523 B — INTACT)
FOUND: checkpoints/phase19_m1_erased_adapter.pt         (13f59301... — untouched)
FOUND: checkpoints/phase19_erase_reference_adapter.pt   (22e66552... — untouched)
ABSENT (correctly): results/phase19_erasure_report.md   — 19-15's deliverable
FOUND commit: 3032f6c  feat(19-14): the DESCRIPTIVE representational read, per cell and with its n
FOUND commit: a823353  test(19-14): the 19-05 not-gated guard, re-run against the read that now exists
FOUND commit: f55307c  style(19-14): rewrap the companion record's descriptive_only string
```

Nothing was deleted or moved. The pin is byte-identical at 15 commits and the descriptive-only AST
scan is unweakened — not one character of `test_representational_read_is_not_gated` changed.
