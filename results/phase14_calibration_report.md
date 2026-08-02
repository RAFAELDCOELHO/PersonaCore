# PersonaCore — Phase 14 Calibration Report (D-09 / D-14 / D-15 / D-21)

> **What these numbers are.** A measurement on THROWAWAY fact sets that are disjoint
> from the real one, run for the sole purpose of deriving four numbers — the recall
> thresholds, the taught/held-out family allocation, the replay verdict, and the
> teaching-register verdict — under a decision rule committed to git BEFORE this run
> produced a single number. One calibration run answers four questions from one measured
> source instead of four separately-justified guesses.
>
> **What they are not.** These are NOT a Phase-14 result. They are not the demo's recall
> rate, they are not comparable to `results/phase14_recall_report.md`, and they say
> nothing about whether the real persona was learned — they were measured on invented
> facts the shipped adapter is never taught. Citing a number from this file as a
> PersonaCore recall result would be a category error.

## Pre-Registration (committed before this run)

Every literal below was committed in **`d7d79174bd4293bfc95fe5647c1bb7ec0dea509b`**
(*feat(14-07): commit CALIBRATION_DECISION_RULE before any calibration number exists*),
which strictly precedes every output of this run. **Git history order is the
pre-registration proof** (D-09 condition 2) — re-derive it with:

```
git log -S 'CALIBRATION_DECISION_RULE = (' -- scripts/teach_persona.py
```

| Literal | Value | What it does |
|---|---|---|
| `CAL_MARGIN_K` | 2 | Phase 12's noise-floor margin, reused BLIND and not re-chosen for Phase 14 |
| `THRESHOLD_DISCOUNT` | 0.6 | the fraction of the calibration ceiling the real threshold is set to — the calibration set is disjoint and disposable, so its rate is a CEILING estimate, not a target |
| `THRESHOLD_FLOOR` | 0.2 | below this the metric is indistinguishable from the closed-book control at 8 seeded samples |
| `SATURATION_DELTA` | 0.05 | the per-family recall gain below which a taught family counts as saturated and MOVES to held-out |
| `HELDOUT_VARIANCE_TRIGGER` | 0.15 | the held-out per-family std above which the real set needs MORE held-out families |
| `COLLAPSE_PPL_TRIGGER` | 0.1 | the fractional masked dialogue-val PPL increase above which replay becomes MANDATORY |
| `REGISTER_WIN_MARGIN` | 0.1 | the absolute held-out margin by which first person must beat second person to count as a win |

(`RATIO_DECIMALS = 10` is a boundary-arithmetic constant added in the same
commit, not a fifth policy number: both trigger comparisons round the measured ratio to
ten decimals first, so 'exactly on the boundary' means the decimal value rather than
whichever double happens to bracket it.)

## Arm Design

| Arm | Fact set | Register | Replay ratio | Role |
|---|---|---|---|---|
| `cal_first_person` | `CALIBRATION_FACTS` (10 facts) | first person (D-01) | 0.0 | **the baseline.** Supplies the thresholds, the allocation inputs, and the no-replay PPL pair |
| `cal_first_person_replay` | `CALIBRATION_FACTS` (10 facts) | first person | 1.0 | D-15's PAIRED comparison — the ONLY difference from the baseline arm is the PersonaChat replay slice |
| `cal_second_person` | `REGISTER_ARM_FACTS` (6 facts) | **second person** (`FAMILIES_SECOND_PERSON`) | 0.0 | D-21's register arm. Its facts are DISJOINT from both the real set and the calibration set |

**The calibration facts are disposable as an EVIDENCE SOURCE, not exempt from the
validity discipline** (D-09 condition 1). Both throwaway pools passed the SAME D-02/D-03
pre-flight gate as the real set — `CALIBRATION_POOL` 10/10 and `REGISTER_ARM_POOL` 6/6,
recorded in `results/phase14_factset_report.md` under commit
`446afab372dcffbc16cbc9a667529097f6e5ccab`. That matters because a calibration set with GUESSABLE facts
would produce an inflated ceiling, and every threshold derived from it would be a number
the base could clear without having learned anything.

Scoring is the same harness the real run uses: `phase14_recall.load_adapted_model`
(`weights_only=True`, load-before-inject), 1 greedy draw plus
`N_SEEDED_SAMPLES` seeded draws per question, scored by `contains_value`. Questions
whose own frame names the fact value — `F4` (reversed direction), `F5` (verification)
— are dropped by the same mechanical `contains_value(question, value)` filter the harness
uses, because a question containing its own answer measures copying from context.

Every arm is scored **adapter ON and adapter OFF** (`adapter_disabled`: same process,
same weights, same prompts, same per-question seeds, only the 36 LoRA `enabled` flags
flipped). The OFF pass is the closed-book baseline — without it a held-out rate is
unjudgeable — and its taught half is the second term of the per-family GAIN below.

## Measured Results

### `cal_first_person`

| Measurement | Value |
|---|---|
| final train loss | 0.0754 |
| taught recall rate (adapter ON) | **0.6825** (860/1260) |
| held-out recall rate (adapter ON) | **0.5519** (447/810) |
| taught recall rate (adapter OFF — closed book) | 0.0000 (0/1260) |
| held-out recall rate (adapter OFF — closed book) | 0.0000 (0/810) |
| per-family gain (taught ON − taught OFF) | `F1` +0.6889, `F2` +0.7022, `F6` +0.6500 |
| held-out rate by family | `F3` 0.6296, `F7` 0.5519, `F8` 0.4741 |
| held-out per-family std (population) | 0.0635 |
| masked dialogue-val PPL, adapter OFF | 4.5737 |
| masked dialogue-val PPL, adapter ON | 14.8559 |
| PPL delta (ON vs OFF) | +224.81% over 270,203 scored targets |
| measured mask fraction | 0.3426 (band (0.15, 0.95)) |
| teaching corpus tokens | 9,065 (9,065 teaching + 0 replay) |
| episodes | 220 |
| scored questions | 140 taught + 90 held-out |
| wall clock | 1192s |
| adapter | `phase14_cal_first_person_adapter.pt` sha256 `59b2de61df5bdfd4…` |
| run CSV | `results/phase14_cal_first_person/run.csv` |

### `cal_first_person_replay`

| Measurement | Value |
|---|---|
| final train loss | 0.5555 |
| taught recall rate (adapter ON) | **0.4143** (522/1260) |
| held-out recall rate (adapter ON) | **0.2506** (203/810) |
| taught recall rate (adapter OFF — closed book) | 0.0000 (0/1260) |
| held-out recall rate (adapter OFF — closed book) | 0.0000 (0/810) |
| per-family gain (taught ON − taught OFF) | `F1` +0.4489, `F2` +0.4244, `F6` +0.3583 |
| held-out rate by family | `F3` 0.2556, `F7` 0.2370, `F8` 0.2593 |
| held-out per-family std (population) | 0.0097 |
| masked dialogue-val PPL, adapter OFF | 4.5737 |
| masked dialogue-val PPL, adapter ON | 5.9180 |
| PPL delta (ON vs OFF) | +29.39% over 270,203 scored targets |
| measured mask fraction | 0.3854 (band (0.15, 0.95)) |
| teaching corpus tokens | 18,130 (9,065 teaching + 9,065 replay) |
| episodes | 220 |
| scored questions | 140 taught + 90 held-out |
| wall clock | 1245s |
| adapter | `phase14_cal_first_person_replay_adapter.pt` sha256 `d9bd0c003bbffe0c…` |
| run CSV | `results/phase14_cal_first_person_replay/run.csv` |

### `cal_second_person`

| Measurement | Value |
|---|---|
| final train loss | 0.0668 |
| taught recall rate (adapter ON) | **0.9405** (711/756) |
| held-out recall rate (adapter ON) | **0.8045** (391/486) |
| taught recall rate (adapter OFF — closed book) | 0.0000 (0/756) |
| held-out recall rate (adapter OFF — closed book) | 0.0000 (0/486) |
| per-family gain (taught ON − taught OFF) | `F1` +0.9630, `F2` +0.9741, `F6` +0.8704 |
| held-out rate by family | `F3` 0.6975, `F7` 0.9012, `F8` 0.8148 |
| held-out per-family std (population) | 0.0835 |
| masked dialogue-val PPL, adapter OFF | 4.5737 |
| masked dialogue-val PPL, adapter ON | 18.7520 |
| PPL delta (ON vs OFF) | +310.00% over 270,203 scored targets |
| measured mask fraction | 0.3778 (band (0.15, 0.95)) |
| teaching corpus tokens | 5,749 (5,749 teaching + 0 replay) |
| episodes | 132 |
| scored questions | 84 taught + 54 held-out |
| wall clock | 773s |
| adapter | `phase14_cal_second_person_adapter.pt` sha256 `31541c062cd2d2b7…` |
| run CSV | `results/phase14_cal_second_person/run.csv` |

### Run provenance

```
seed: 1337
driver git_sha: 75ac857663fbbd3bc647c4cd94ca7ec1da16f987
pid: 38560
wall clock (UTC): 2026-08-02T06:33:21Z
total wall: 3210s
preflight: {'device': 'mps', 'cc': None, 'torch': '2.7.1'}
device: mps  torch: 2.7.1
lr=0.0003 weight_decay=0.0 batch_size=8 max_steps=200 warmup_steps=20 block_size=256
decision-rule commit: d7d79174bd4293bfc95fe5647c1bb7ec0dea509b
FACTSET_GATE_SHA: 446afab372dcffbc16cbc9a667529097f6e5ccab
cal_first_person: adapter=phase14_cal_first_person_adapter.pt sha256=59b2de61df5bdfd4513e562dac3c5ef1fb3efb025b0bc6745552f23edeaa6a1c
cal_first_person: csv=results/phase14_cal_first_person/run.csv wall=1192s
cal_first_person_replay: adapter=phase14_cal_first_person_replay_adapter.pt sha256=d9bd0c003bbffe0cfc1b8ecf4cd2a9e0d52719198103d9d5c77773a4cb4e45e9
cal_first_person_replay: csv=results/phase14_cal_first_person_replay/run.csv wall=1245s
cal_second_person: adapter=phase14_cal_second_person_adapter.pt sha256=31541c062cd2d2b71307dcfa4fa4ab90539b681a1932021329b2b840dbbdc211
cal_second_person: csv=results/phase14_cal_second_person/run.csv wall=773s
```

## Derivation 1 — Recall Thresholds (D-09)

**Rule function:** `teach_persona.lock_thresholds(cal_taught_rate, cal_heldout_rate)`,
committed in `d7d79174bd4293bfc95fe5647c1bb7ec0dea509b`. **The function is UNCHANGED
between the two derivations below — only the arm supplying its inputs differs.**

### As first derived — inputs from `cal_first_person` (the no-replay arm)

| Input | Value | Source |
|---|---|---|
| `cal_taught_rate` | 0.6825 | `cal_first_person` taught, adapter ON (860/1260) |
| `cal_heldout_rate` | 0.5519 | `cal_first_person` held-out, adapter ON (447/810) |
| `THRESHOLD_DISCOUNT` | 0.6 | pre-registered |
| `THRESHOLD_FLOOR` | 0.2 | pre-registered |

| Output | Value | Bound by |
|---|---|---|
| `TAUGHT_THRESHOLD` | 0.4095 | the DISCOUNT |
| `HELDOUT_THRESHOLD` | 0.3311 | the DISCOUNT |

### As corrected at the checkpoint — inputs from `cal_first_person_replay`

Derivation 3 returned `replay_required = True`, which sets `REAL_RUN_REPLAY_RATIO = 1.0`.
That makes `cal_first_person_replay` — not the baseline — the arm whose configuration the
real run actually uses. The thresholds above were derived from the arm the real run will
NOT run under. The SAME committed function is re-applied to the matching arm's rates:

| Input | Value | Source |
|---|---|---|
| `cal_taught_rate` | 0.4143 | `cal_first_person_replay` taught, adapter ON (522/1260) |
| `cal_heldout_rate` | 0.2506 | `cal_first_person_replay` held-out, adapter ON (203/810) |
| `THRESHOLD_DISCOUNT` | 0.6 | pre-registered, unchanged |
| `THRESHOLD_FLOOR` | 0.2 | pre-registered, unchanged |

```
taught     max(THRESHOLD_FLOOR, round(0.4143 * 0.6, 4)) = max(0.2, 0.2486) = 0.2486
held-out   max(THRESHOLD_FLOOR, round(0.2506 * 0.6, 4)) = max(0.2, 0.1504) = 0.2000   <- the FLOOR binds
```

### Both threshold sets, side by side

| Threshold | From `cal_first_person` (as first derived) | From `cal_first_person_replay` (COMMITTED) | Bound by |
|---|---|---|---|
| `TAUGHT_THRESHOLD` | 0.4095 | **0.2486** | the DISCOUNT |
| `HELDOUT_THRESHOLD` | 0.3311 | **0.2000** | the FLOOR |

Both sets are shown rather than the first being silently replaced, so a reader can verify
independently that the correction NARROWS a wiring mismatch and does not relax the gate
below what the mechanism actually needed to clear. The held-out threshold does not fall to
0.1504: the pre-registered `THRESHOLD_FLOOR` catches it at 0.2000. That is the floor doing
exactly the job it was committed for — below it the metric is indistinguishable from the
closed-book control at 8 seeded samples, so no threshold derived from any arm may go lower.

**Deviation note, recorded at the checkpoint (verbatim):**

> lock_thresholds was fed cal_first_person (no-replay) while replay_required=True selected the replay config. Feeding it the matching arm is a wiring correction, not a threshold chosen to be cleared. Recorded post-hoc; both numbers shown.

### PROJECTED margins against the corrected gate — these are NOT the verdict

| Tier | `cal_first_person_replay` rate | corrected threshold | PROJECTED margin |
|---|---|---|---|
| taught | 0.4143 | 0.2486 | **+0.1657** |
| held-out | 0.2506 | 0.2000 | **+0.0506** |

**These two numbers are PROJECTIONS, not a result.** They are the calibration arm's OWN
rates measured against the gate that same arm just produced — an arm cannot be independent
evidence for a threshold derived from it, and they were measured on a THROWAWAY fact set
the shipped adapter is never taught. **Plan 14-11's real teaching run produces the number
that actually counts.** Nothing here says the real persona will clear either threshold; if
the real run lands below one, that is the result and it gets recorded as one.

The rule was applied MECHANICALLY in both derivations: the SAME committed function, the
SAME two pre-registered literals, evaluated on measured rates. **No number here was chosen
after seeing the results** — what was pre-registered is the PROCEDURE, because the number
cannot exist before the run but the rule that produces it must, or the threshold is just a
value picked to be cleared.

## Derivation 2 — Family Allocation (D-14)

**Rule function:** `teach_persona.lock_family_allocation(per_family_gain,
heldout_family_std, taught_ids, heldout_ids)`, committed in `d7d79174bd4293bfc95fe5647c1bb7ec0dea509b`.

| Input | Value |
|---|---|
| `per_family_gain` | {'F1': 0.6889, 'F2': 0.7022, 'F6': 0.65} |
| `heldout_family_std` | 0.0635 |
| `taught_ids` (before) | ['F1', 'F2', 'F4', 'F5', 'F6'] |
| `heldout_ids` (before) | ['F3', 'F7', 'F8'] |
| `SATURATION_DELTA` | 0.05 (a gain of exactly this is NOT saturated) |
| `HELDOUT_VARIANCE_TRIGGER` | 0.15 (a std of exactly this does NOT trigger) |

| Output | Value |
|---|---|
| `TAUGHT_FAMILY_IDS` | **['F1', 'F2', 'F4', 'F5', 'F6']** |
| `HELDOUT_FAMILY_IDS` | **['F3', 'F7', 'F8']** |
| taught family count | 5 → **5** |
| saturation trigger | did not fire |
| variance trigger | did not fire (std 0.0635 <= 0.15) |

**['F4', 'F5'] carry NO measured gain, and that is an absence of measurement rather than a measurement of zero.** Every question those families generate names its own fact value inside the question — `F4` is the D-22 reversed direction (`who is varek?`) and `F5` is yes/no verification (`is your name varek?`) — so the same mechanical `contains_value` filter the scored harness uses removed all of them before scoring. They were TAUGHT in full; they are simply not SCORABLE, because a question containing its own answer measures copying from context. `lock_family_allocation` reads a missing key as `0.0` and therefore proposed moving them, which is why they appear in the refusal log below. Do NOT read that as evidence that reversed-direction or verification teaching failed — this run says nothing either way about those two families.

**Driver output, verbatim** — this is the one place a refused move lands, and an
unrecorded refusal is a silently altered allocation:

```
[teach_persona] allocation: REFUSED moving F4 to held-out — D-22 keeps F4 (reversed-direction forms) on the taught side — the reversal curse is a literature failure mode, and moving it would poison the evidence D-20(c) depends on
[teach_persona] allocation: REFUSED moving F5 to held-out — fact 'cand_person_quillon' would drop to 18 taught paraphrases, outside DEMO-05's [20, 50] band (W-03) — build_bins proof #5 would SystemExit the real run
```

The four invariants the rule preserved:

1. **Disjoint, and the union is still every key of `FAMILIES`** (B-02): `[]` is the intersection, and the union is `['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8']` against `FAMILIES` keys `['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8']`. The allocation MOVES families; it never drops one.
2. **`F4` stays taught** (D-22): `F4` IS in the taught set. Reversed-direction forms hit the documented reversal curse, so held out they would fail for a LITERATURE reason rather than for any property of this model.
3. **At least two families per side**: 5 taught, 3 held-out.
4. **Every locked fact's taught-instance count stays inside `PARAPHRASES_PER_FACT_TARGET` = (20, 50)** (W-03): every one of the 10 locked+soft facts carries [22] taught paraphrases, inside the band.

**The allocation is UNCHANGED, and that is a result rather than a no-op.** Every candidate move the rule proposed was REFUSED by invariant 4: at the committed allocation each locked fact carries 22 taught paraphrases against a (20, 50) band, and the smallest taught family carries 4 instances, so any move drops some fact to 17 or 18 — below the floor. The refusal is the invariant doing its job: a saturation-driven move would trip `build_bins` proof #5 and `SystemExit` the real run. If calibration genuinely demands more held-out families, the remedy is to ADD paraphrase instances (a fact-set change), not to relax a pre-registered threshold.

## Derivation 3 — PersonaChat Replay (D-15)

**Rule function:** `teach_persona.replay_required(ppl_adapter_off, ppl_adapter_on)`,
committed in `d7d79174bd4293bfc95fe5647c1bb7ec0dea509b`.

The instrument is the D-11.2 one exactly — `masked_perplexity` over
`data/dialog_val.bin` + its mask, adapter ON and OFF in ONE process on ONE set of
weights, so the only difference is the LoRA enabled flag. It is not a proxy.

| Arm | PPL adapter OFF | PPL adapter ON | Fractional increase |
|---|---|---|---|
| `cal_first_person` (no replay) | 4.5737 | 14.8559 | **+224.81%** |
| `cal_first_person_replay` (replay 1.0) | 4.5737 | 5.9180 | +29.39% |

| Output | Value |
|---|---|
| `replay_required` | **True** |
| `COLLAPSE_PPL_TRIGGER` | 0.1 (exactly at the trigger does NOT require replay — strict `>`) |
| `REAL_RUN_REPLAY_RATIO` | **1.0** |

**Replay IS required.** The no-replay arm's masked dialogue-val PPL rose past `COLLAPSE_PPL_TRIGGER` = 0.1, so the real run mixes PersonaChat replay at ratio 1.0 into its teaching bin.

**What the paired arm shows replay actually BUYS, and what it costs.** Replay at ratio 1.0 moves the collapse from +224.81% to +29.39% — a large mitigation — while taught recall falls from 0.6825 to 0.4143, a fall of 0.2683. **The replay arm ITSELF still trips the trigger.** Replay at this ratio reduces the collateral collapse but does not eliminate it, so 'replay required' should not be read as 'replay solves it'. Whether the remaining +29.39% is acceptable, and whether a different ratio or a shorter teaching run is the better lever, is a judgment for the checkpoint — this run measured the tradeoff, it did not resolve it.

The paired arm is reported alongside because D-15 asks what replay BUYS, not only
whether it is needed: the two arms differ in the replay slice and in nothing else, so
the difference between their two ON/OFF deltas is attributable to replay alone.

## Derivation 4 — Teaching Register (D-21)

**Rule function:** `teach_persona.first_person_wins(fp_heldout_rate, sp_heldout_rate)`,
committed in `d7d79174bd4293bfc95fe5647c1bb7ec0dea509b`.

| Input | Value | Source |
|---|---|---|
| `fp_heldout_rate` | 0.5519 | `cal_first_person` held-out, adapter ON |
| `sp_heldout_rate` | 0.8045 | `cal_second_person` held-out, adapter ON |
| margin | -0.2527 |
| `REGISTER_WIN_MARGIN` | 0.1 (exactly at the margin is NOT a win — strict `>`) |

| Output | Value |
|---|---|
| `first_person_wins` | **False** |
| `REAL_RUN_SECOND_PERSON` | **False** |

**Both kinds of evidence, per D-21 condition 4.** The register lock in D-01 was made on
QUALITATIVE evidence and it stands on that evidence: 14-RESEARCH F3/F5 measured the
frozen conversational base copying the *structure* of a second-person prompt while
getting the *content* wrong. The recorded probe answered
`i have a dog named my name is cuddling`, which is a syntactically well-formed
first-person self-description with the wrong noun phrase spliced in.
That finding is what motivated teaching answers as
first-person self-description in the first place, and no number in this report replaces
it. What D-01 was MISSING was a measured head-to-head between the two registers, and
that is exactly and only what this arm supplies:
first person 0.5519 vs second person
0.8045 on held-out recall, a margin of
-0.2527 against a pre-registered win margin of 0.1.

**The first-person register did NOT clear the pre-registered margin, and that negative is recorded here unamended** (D-12). It does NOT reopen D-01 mid-phase. D-01's register lock rests on the qualitative evidence above, which this arm was designed to SUPPLEMENT with a measured head-to-head, not to replace; re-authoring the teaching set after seeing a number is the exact move the whole pre-registration block exists to prevent. `REAL_RUN_SECOND_PERSON` stays `False`.

**Caveat a reader should carry:** the two arms are scored on DIFFERENT fact sets (10 calibration facts vs 6 register-arm facts), because D-21 requires the register arm's facts to be disjoint from both the real and the calibration sets. The comparison is therefore between two register treatments over comparable-but-not-identical material, which is the strongest head-to-head the disjointness requirement allows.

## Verdict

ADAPT — the real run proceeds, with exactly one deviation.

**The deviation.** `lock_thresholds` was applied to `cal_first_person`'s rates while
Derivation 3 returned `replay_required = True`, which makes `cal_first_person_replay` the
arm whose configuration the real run uses. The identical committed rule function is
re-applied to the matching arm's rates: `TAUGHT_THRESHOLD` 0.4095 → **0.2486** and
`HELDOUT_THRESHOLD` 0.3311 → **0.2000** (the pre-registered `THRESHOLD_FLOOR` binds the
held-out side). Both threshold sets are shown side by side in Derivation 1, together with
the deviation note recorded verbatim and the projected margins labelled as projections.

**What is NOT adapted.** Derivation 2's allocation stands unchanged, refusals and all,
along with its F4/F5 absence-of-measurement note. Derivation 3's `replay_required = True`
and `REAL_RUN_REPLAY_RATIO = 1.0` stand. Derivation 4's negative register result stands
unamended (D-12) and does NOT reopen D-01 mid-phase — `REAL_RUN_SECOND_PERSON` stays
`False`. No measured number in this report was altered.
