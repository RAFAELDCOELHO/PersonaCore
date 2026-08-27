---
kind: assessment
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
created: 2026-08-27
author: execute-phase orchestrator
scope: >
  Does the seed-1337 matched-comparator reading settle branch (A) INVALID COMPARATOR
  at the MECHANISM level, and what does it NOT settle?
governs: nothing
---

# Mechanism assessment — seed 1337, deviation == 0.0

> **This file governs nothing.** It is information about priority and confidence. It is
> not a verdict, not a floor, and not a licence to change any pre-registered quantity.

> **Deliberately NOT written into `.planning/debug/sigma-zero-beats-control.md`.** Plan
> 23-19 owns that file's dated continuation and gates on
> `grep -c "PROTOCOL-MATCHED COMPARATOR" .planning/debug/sigma-zero-beats-control.md`
> plus an append-only deletion check. Writing this assessment there would satisfy a
> downstream plan's acceptance criterion with text that plan did not produce.

## Verdict, in one line

**YES at the mechanism level. NO as a substitute for the formal 5-seed floor.**

## What was measured

Re-derived by the orchestrator directly from `results/phase23_sigma_zero.json` and
`data/phase23_run_state.json`, not carried over from any SUMMARY.

### Identical — all four scored tiers, at seed 1337

| Tier | σ=0 DP arm | matched non-DP comparator |
|---|---|---|
| `primary` | 790/1008 = `0.7837301587301587` | 790/1008 = `0.7837301587301587` |
| `taught_off` | 0/1008 = `0.0` | 0/1008 = `0.0` |
| `heldout_on` | 346/648 = `0.5339506172839507` | 346/648 = `0.5339506172839507` |
| `heldout_off` | 0/648 = `0.0` | 0/648 = `0.0` |

`per_family_gain` (F1 `0.8444…`, F2 `0.8222…`, F6 `0.6597…`) and `heldout_family_std`
(`0.04933446717020304`) are identical too. **Deviation exactly `0.0`.**

### NOT identical — and this matters

| Quantity | σ=0 DP arm | matched comparator |
|---|---|---|
| `dp_seam_active` | `True` | `False` |
| `adapter_sha256` | `0a897d23…c6c64` | `0b64c1f5…e9580` |
| `adapter_bytes` | 1,351,601 | 1,352,601 |
| `final_train_loss` | `0.0603661946952343` | `0.06036620284430683` |

The two runs produced **different weights** (differing sha256, 1,000-byte size gap) and
train losses that agree to ~7 significant figures but not bitwise.

## What this establishes

One run passed through the DP seam at σ=0; the other never entered it (`dp_fn=None`).
They produced **different weights** and **identical readings**. Therefore, at σ=0, the DP
seam is inert *at the resolution of the scoring instrument*, and the σ=0 arm's
`0.78373` is a **protocol effect, not a DP effect**.

Branch **(A) INVALID COMPARATOR** is confirmed **empirically**, not merely by argument.
Branch (B) was already falsified independently by the two-leg gradient-identity probe
(worst relative difference `2.178e-07` across 72 LoRA tensors).

**This is an out-of-sample confirmation, which is its real strength.**
`.planning/debug/sigma-zero-beats-control.md` reached `status: root-caused` and named the
three mechanisms — fact-aligned packer, 8.125× lot volume, one-sided `grad_clip` — at
commit `263f5f8`, *before any matched comparator existed*. The run confirms a prediction
made in advance rather than explaining a result after the fact.

## Three limits, stated

1. **Identical scores from non-identical weights bound the claim.** The instrument counts
   k/n over 1008 and 648 draws; it cannot resolve weight differences of this magnitude.
   This shows inertness *at scoring resolution*, not weight-level equivalence. The
   stronger claim is not supported by this evidence.
2. **n = 1, and it is the least independent seed available.** 1337 is simultaneously the
   σ=0 arm's seed and the seed the OLD control's central reading was pinned at. Agreement
   at the one shared seed is the weakest point in the ladder for an independence claim.
3. **It produces no floor.** The formal verdict requires `phase23_prereg.noise_floor`
   reduced over the matched comparator's readings. This assessment reduces nothing.

## What it does NOT license

**It does not reopen N.** `phase23_prereg.choose_n_seeds` pinned N=5 blindly, at a
measured 996.27 s scoring cost, before any matched reading existed. Three readings on
screen is precisely the moment at which N must not move — the same discipline that
governed CTRL-03's N-seed requirement. The pre-registered ladder is
`(1337, 2024, 1338, 2025, 1339)`; seeds **2025 and 1339 remain owed**.

Provisional and **non-governing** — the three scored readings, already published in
`23-17-SUMMARY.md`, restated here only so this file is self-contained:
`0.7837301587301587`, `0.7678571428571429`, `0.7718253968253969`.
**No floor is reduced over them here, and none may be.**

## Priority implication

The remaining two seeds are now expected to **confirm rather than decide**. That lowers
the *risk* of the remaining ~40 minutes of compute. It does not lower the *requirement*.
Finish the ladder.
