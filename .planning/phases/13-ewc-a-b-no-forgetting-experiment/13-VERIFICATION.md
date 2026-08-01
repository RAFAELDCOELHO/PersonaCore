---
phase: 13-ewc-a-b-no-forgetting-experiment
verified: 2026-08-01T22:29:17Z
status: human_needed
score: 23/23 must-haves verified
overrides_applied: 0
re_verification:
  pass: 2
  head: a807e56
  previous_status: gaps_found
  previous_score: 22/23
  gaps_closed:
    - "Committed evidence artifacts make no provenance claim the artifacts themselves contradict (honest-evidence core value)"
  gaps_remaining: []
  regressions: []
  warnings_closed:
    - "CR-02: PROD_*_4000 pre-registration literals printed but never compared — now enforced by tests/test_phase13_driver.py::test_prod_csv_matches_preregistered_literals (mutation-tested)"
    - "WR-03: test_gate_boundary could not distinguish > from >= — rewritten to (MARGIN, 0.0); mutation-tested, dies under >="
  warnings_remaining:
    - "plot_phase13.py:_series truthiness filter — a missing column silently yields an empty, valid-looking PNG (latent; today's figures are byte-reproducible)"
    - "plot_phase13.py:rows[-1] on sweep CSVs with no step-1250 assertion (latent; all five CSVs confirmed to end at 1250)"
human_verification:
  - test: "Accept the roadmap-wording supersession: ROADMAP.md:164 SC1 says 'λ=0 vs λ*' but Phase 12 §8 recorded λ* = None, so Phase 13 ran λ=0 vs a pre-chosen λ=0.01"
    expected: "The substitution is documented in results/phase13_ab_report.md:303-305 (## Reconciliation, 'ROADMAP wording superseded') with D-02/D-09 rationale. Confirm this is the intended record, or update ROADMAP.md Phase 13 SC1"
    why_human: "A scope/wording acceptance decision, not a code fact. The substance of SC1 (identical seeds, config, data order; one-bit difference) is fully verified"
---

# Phase 13: EWC A/B No-Forgetting Experiment — Verification Report

**Phase Goal:** Committed, unconfounded evidence that EWC mitigates catastrophic forgetting — both retention AND acquisition reported for both arms
**Verified:** 2026-08-01T22:29:17Z (pass 2, re-verification at `a807e56`)
**Status:** human_needed (23/23 truths verified; one roadmap-wording acceptance decision remains)
**Re-verification:** Yes — after gap closure. Pass 1 (`2026-08-01T19:39:27Z`, `gaps_found`, 22/23) is retained verbatim below as the audit trail.

---

# Re-Verification Pass 2 — 2026-08-01T22:29:17Z

## Verdict

**The single pass-1 gap is genuinely closed, and nothing regressed.** Score moves 22/23 → 23/23.
Both pass-1 anti-pattern WARNINGs that had named fixes (CR-02, WR-03) are also closed, and I
mutation-tested both rather than taking the test names at face value.

Every claim below was re-derived in this verifier's own process at `a807e56`. I did not read the
gap-closure commit messages as evidence.

## Gap closure: the provenance claim (pass-1 truth 23)

Pass 1 failed this truth because two committed artifacts asserted "both arms draw from the
identical stream, so a text difference is a weight difference" while `seed_everything(SEED)` was
called once per **arm**, outside the prompt loop — so an early stop in one arm shifted every
later prompt's stream in that arm. I had located the materialized defect independently via a
151-char EWC completion on prompt 20081 against a 195–244 char band.

Four independent checks, all passed:

**1. The mechanism is real, not cosmetic.** `scripts/make_retention_samples.py:164` now builds
`torch.Generator(device=device).manual_seed(SEED + story_idx)` *inside* the per-prompt loop and
passes it as `generator=gen_rng`. I traced the kwarg through the actual call chain rather than
assuming it is honored: `_complete(**kw)` → `collect(**kw)` → `generate(..., generator=generator)`
(`generation/core.py:73`) → `next_token(..., generator=generator)` →
`torch.multinomial(probs, num_samples=1, generator=generator)` (`generation/sampling.py:103`).
The kwarg is not swallowed anywhere.

**2. The MPS generator is genuinely isolated** (the way this fix could have been silently
worthless). PyTorch has historically had backends that accept a `generator` and ignore it. I
tested it directly on the real device:

```
device: mps
same seed, global stream perturbed (997 global draws) -> identical: True
different seed -> different: True
not degenerate: True
```

So a fresh per-prompt generator is immune to global-stream state, and an early stop inside prompt
*k* provably cannot shift prompt *k+1* — the generator for *k+1* is constructed fresh. The
pairing claim now holds **by construction**, not by luck of the run.

**3. The committed artifact was actually regenerated, and its numbers are real.** Independent
re-measurement of `results/phase13_retention_samples.md` (parsed the markdown myself, recounted
role-token strings in the 40 generation blocks):

| measurement | pass-1 file | pass-2 file | report says |
|---|---|---|---|
| EWC prompt-20081 warm length | **151 chars (outlier)** | 231 chars (in band) | — |
| warm length band, naive / EWC | — | 192–236 / 187–231 | — |
| eos termination, naive / EWC | 0/20, **1/20** | 0/20, **0/20** | 0/20, 0/20 ✓ |
| role-token leakage, naive / EWC | 79, **70** | **79**, **69** | 79, 69 ✓ |

The 151-char outlier is gone; no warm block in either arm shows an early stop, which is exactly
what `0/20` for both arms predicts. My recount (79 / 69) matches the samples file's proxy table
and the report's inline citation at `:178` — three independent derivations agree.

**4. Greedy blocks are byte-unchanged; only warm blocks moved.** I extracted all 20 greedy and
all 20 warm blocks at `e3d99b0` and at `HEAD` and compared:

```
greedy blocks identical old vs new: True (20 blocks)
warm blocks changed: 20 of 20
```

Argmax consumes no RNG, so byte-identical greedy halves prove the **same step-4000 checkpoints**
produced the new file — the regeneration swapped the sampler seeding and nothing else. This is
the check that rules out "the arms were quietly re-run or re-curated".

**Both previously-false sentences now match the implemented protocol** — verified by reading
them, not by trusting the diff:

- `results/phase13_retention_samples.md:7-11` — "Warm sampling draws from an explicit per-PROMPT
  `torch.Generator` seeded `1337 + story_idx`, identical across arms, so a text difference is a
  weight difference — and an early stop in one prompt cannot shift any later prompt's stream."
- `results/phase13_ab_report.md:342-345` — same protocol, same scope, with "so each prompt is
  genuinely paired".

Both statements are now true of the code that produced the file. **Truth 23: ✗ FAILED → ✓ VERIFIED.**

The residual `seed_everything(SEED)` at `:157` is retained and correctly commented as
"belt-and-braces only … not load-bearing for the pairing claim" — accurate, since the explicit
generator is what `torch.multinomial` reads.

## Regression checks — nothing in the headline evidence moved

The pass-1 verdict rested on numbers that must be untouched by a sampling fix. I re-derived them
rather than reasoning from the diff.

| Invariant | Check | Result |
|---|---|---|
| Driver still byte-frozen (D-10 pre-registration) | `git diff c3d942e HEAD -- scripts/finetune_ab.py` | **empty** ✓ |
| Pre-registration table byte-unchanged | `git diff 8fa2aa1 HEAD -- results/phase13_ab_report.md` removals | only the 7 `_Pending_` placeholder lines; zero pre-reg edits ✓ |
| Arm CSVs / prod CSV / sweep CSVs untouched | `git diff --stat e3d99b0 HEAD` on all 8 CSVs | **empty** ✓ |
| 2×2 cells | final rows re-read from both arm CSVs | naive 4.192794562524908 / 8.52417066884246; EWC 4.573349242745997 / 3.8911400839446597 — unchanged ✓ |
| Gate verdict | imported the frozen driver's own `ewc_mitigates` + `MARGIN` | `True`, delta 4.633030584897801, MARGIN 0.13786, ratio **33.6068×** (report: 33.61×) ✓ |
| Acquisition delta | recomputed | +0.3805546802210893 ✓ |
| D-11 cross-check | \|EWC ret − prod ret\| | 1.0832683e-07; `ewc_penalty` bit-identical (0.13435843586921692) ✓ |
| Trajectory table | (pass 1 re-derived all 16 deltas; naive CSV byte-untouched since) | unchanged ✓ |
| Gate strictness | `ewc_mitigates(5.0+MARGIN, 5.0)` / `+1e-9` | `False` / `True` — strict `>` intact ✓ |
| Working tree clean | `git status --porcelain` | only untracked `AGENTS.md` (not a phase artifact) ✓ |

None of the four gap-closure commits touched a file that feeds any headline number. The report
diff since pass 1 is exactly two hunks: the `79 (naive) vs 70 → 69 (EWC)` inline citation at
`:178`, and the protocol sentence + proxy table at `:339-359`. The 2×2, gate verdict, D-11
cross-check, trajectory table and Reconciliation sections are byte-unchanged.

## Figures — SC3 / SC4 still hold, still byte-reproducible

`phase13_forgetting_curve.png` was regenerated (`0794cdc`: plain-number log ticks + larger
legend). I regenerated **both** figures into a scratch dir from the committed CSVs and hashed
them against the committed files:

```
phase13_forgetting_curve.png reproducible: True  332e7324100c7e7d == 332e7324100c7e7d
phase13_frontier.png        reproducible: True  65e9299a4bc6c4e7 == 65e9299a4bc6c4e7
```

Both are SHA-256 identical — the committed PNGs are still exactly what the committed data
produces. I also rendered and inspected both at full size:

- **SC3** (`forgetting_curve`): left panel = retention PPL vs fine-tuning step, both arms; gray
  dashed axhline labeled "v1.0 headline 2.1066 (full-val, unmasked)" (`HEADLINE_RETENTION = 2.1066`
  confirmed by import); right panel = acquisition companion (masked dialogue PPL), same two arms.
  The log y-axis on the acquisition panel now reads **4, 5, 6, 7, 8, 9, 10, 20, 30** instead of
  `4×10⁰`/`10¹`, and both legends are legible. ✓
- **SC4** (`frontier`): retention (y) vs dialogue (x), **6** annotated points — `build_frontier_points()`
  executed live returns exactly 6 tuples labelled λ=0, 0.01, 0.1, 1, 10, 100 — caption
  "1250-step sweep endpoints (LR 9e-5, unmasked) — not the 4000-step A/B arms". No label
  collisions and **no clipping at λ=100** (its annotation sits inside the axes). ✓

## Pass-1 WARNINGs now closed — mutation-tested, not name-tested

| Pass-1 warning | Fix | My mutation check | Verdict |
|---|---|---|---|
| CR-02 — `PROD_DIALOG_4000` / `PROD_RETENTION_4000` printed but never compared; the declared D-11 tripwire did not exist | `tests/test_phase13_driver.py::test_prod_csv_matches_preregistered_literals` asserts both literals against `finetune_prod.csv` at 1e-9, placed **outside** the frozen driver | drifted the prod CSV's `retention_ppl` by 1e-6 → assertion returns `False` | **closed** — tripwire is live and fires on drift, on every commit rather than only on a 37-min re-run |
| WR-03 — `test_gate_boundary` used `(5.0, 5.0 - MARGIN)`, whose fp round-trip is 0.13785999999999987 < MARGIN, so it passed under both `>` and `>=` | rewritten to `(MARGIN, 0.0)` | `MARGIN - 0.0 == MARGIN` → `True` (delta is bit-exact); under `>` → `False` (test asserts False), under `>=` → `True` (**test would fail**) | **closed** — the mutation is now caught |

Two latent WARNINGs remain unchanged and non-gating: `plot_phase13.py:_series` truthiness
filtering (a missing column would plot an empty, valid-looking PNG) and `rows[-1]` on the sweep
CSVs with no step-1250 assertion. Both are hardening for future re-runs; today's figures are
byte-reproducible and all five sweep CSVs were re-confirmed to end at step 1250.

## Stale-citation sweep

Grepped `results/`, `scripts/`, `tests/` and the phase dir for the superseded `70` leakage and
`1/20` eos figures. **Zero stale citations survive in any published evidence artifact.** The
report's inline citation (`:178`), its proxy table (`:349-350`) and the samples file
(`:17-18`) all read 79 / 69 and 0/20 / 0/20 consistently. The remaining `70` / `1/20` matches are
confined to point-in-time planning records — `13-03-SUMMARY.md`, `13-04-SUMMARY.md`,
`13-REVIEW.md`, `13-SECURITY.md`'s explicitly-labelled "original analysis is retained below as the
audit trail" block, and pass 1 of this file. Those are audit trail, not claims about the current
artifact, and `13-SECURITY.md` records the cascade (`1/20 → 0/20`, `70 → 69`) explicitly.

**One cosmetic residue, non-gating (ℹ️ INFO):** `results/phase13_retention_samples.md:47`
(generated from `make_retention_samples.py:218-220`) still reads "A 0.00-0.05 stop-id fraction is
expected … nearly every completion is budget-truncated", while the report's parallel sentence was
tightened to "The zero eos fraction … every completion is truncated". Both arms now measure
exactly 0.00, so the samples file's phrasing is loose but not false (0.00 lies in [0.00, 0.05]).
It asserts an expectation, not a measurement, and the measured table directly above it reads
`0/20 = 0.00` for both arms.

## Re-run spot-checks (this verifier's process, at `a807e56`)

| Behavior | Command | Result | Status |
|---|---|---|---|
| Full suite green | `.venv/bin/python -m pytest tests/ -q` | **285 passed**, 1 skipped, 116s (was 284 — the new CR-02 test) | ✓ PASS |
| Lint + format | `ruff check scripts/ tests/ src/`; `ruff format --check` | All checks passed; 84 files already formatted | ✓ PASS |
| Debt markers in phase-13 files | grep `TBD\|FIXME\|XXX\|TODO\|HACK\|PLACEHOLDER` on all 7 touched files | none | ✓ PASS |
| MPS generator isolation | seeded draws with a perturbed global stream | identical; different seed → different; non-degenerate | ✓ PASS |
| Gate on real data | import frozen driver, `ewc_mitigates(8.52417…, 3.89114…)` | `True`, 33.6068× MARGIN | ✓ PASS |
| Gate boundary strictness | `(MARGIN, 0.0)` and `(MARGIN+1e-9, 0.0)` | `False` / `True` | ✓ PASS |
| D-11 literal tripwire fires | drift prod CSV by 1e-6 | assertion `False` | ✓ PASS |
| Figures reproduce | regenerate → `sha256` vs committed | **both identical** | ✓ PASS |
| Frontier point count | `build_frontier_points()` | 6 tuples, correct λ labels | ✓ PASS |
| Greedy-block invariance | parse + diff 20 greedy blocks `e3d99b0` vs `HEAD` | identical | ✓ PASS |
| Samples proxies re-derived | recount role tokens + block lengths from the markdown | 79 / 69, no early stops | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` exist and no PLAN/SUMMARY declares a probe; not a
migration/tooling phase. **Step 7c: SKIPPED (no probes declared or discoverable).** The runnable
evidence is the spot-check table above, all executed in this verifier's own process.

## Requirements coverage (re-confirmed)

| Requirement | Source Plan | Status | Evidence |
|---|---|---|---|
| DEMO-04 | 13-01, 13-02, 13-03, 13-04 | ✓ SATISFIED | Truths 1, 2, 18 — both columns of the 2×2, plus movement-from-anchor; the "retention-only sleight of hand" is explicitly avoided |
| VIZ-01 | 13-03 | ✓ SATISFIED | Truth 3 — figure re-rendered and inspected, byte-reproducible, log ticks now plain numbers |
| VIZ-04 | 13-03 | ✓ SATISFIED | Truths 4, 16 — 6 points, 5 read live from sweep CSVs, λ=0 carries its pre-registered provenance exception |

`REQUIREMENTS.md:113-115` maps exactly DEMO-04, VIZ-01, VIZ-04 to Phase 13; all three appear in
plan frontmatter, all three marked Complete. **Orphaned requirements: none.**

## Human verification remaining

Pass-1 item 2 (the CR-01 resolution) is **resolved** — Option A was taken, and I verified the
resulting artifact independently above.

Pass-1 item 3 (figure legibility) is **resolved by inspection** — I rendered both figures at full
size this pass. The three named concerns all clear: no label collisions, the acquisition log axis
now reads plain numbers, and the λ=100 annotation is not clipped. Final portfolio aesthetic taste
is of course still the developer's, but there is no defect left to judge.

### 1. Accept (or amend) the roadmap-wording supersession — STILL OPEN

**Test:** `ROADMAP.md:164` SC1 reads "λ=0 vs λ\*", but Phase 12 §8 recorded λ\* = None. Phase 13
ran λ=0 vs a pre-chosen λ=0.01.
**Expected:** The substitution is recorded in `results/phase13_ab_report.md:303-305` under
`## Reconciliation` — "the roadmap describes Phase 13 as 'λ=0 vs λ\*'. There is no λ\* — §8
recorded λ\* = None … that substitution is recorded here rather than silently absorbed into the
roadmap's phrasing." Confirm this is the intended record, or update ROADMAP.md Phase 13 SC1 to
name λ=0.01.
**Why human:** A scope/wording acceptance decision, not a code fact. The *substance* of SC1
(identical seeds, config, data order; a single-bit arm difference) is fully verified — this is
only about which λ symbol the roadmap names. I confirmed this pass that both texts are unchanged.

## Pass-2 Summary

The phase goal is achieved and the evidence is now internally consistent. The one defect pass 1
raised — a committed provenance sentence the committed data contradicted — was fixed at the
mechanism level (per-prompt generator, verified isolated on the real MPS device) rather than by
softening the sentence, the artifact was regenerated with proof that the same checkpoints
produced it (byte-identical greedy halves), and the dependent proxy numbers were cascaded
everywhere they are published. Both named-fix WARNINGs are closed and mutation-tested. Nothing in
the headline evidence moved, and the frozen driver plus the pre-registration table are still
byte-identical to their pre-registration commits — the D-10 guarantee survives the fix intact.

Status is `human_needed` solely because of the roadmap-wording acceptance decision, which is a
documentation choice rather than a code gap.

---
---

_The report below is pass 1, retained verbatim as the audit trail. Truth 23 is now VERIFIED and
the CR-02 / WR-03 warnings are closed — see pass 2 above._

---

# Pass 1 — Phase 13 Verification Report (2026-08-01T19:39:27Z, gaps_found, 22/23)

**Phase Goal:** Committed, unconfounded evidence that EWC mitigates catastrophic forgetting — both retention AND acquisition reported for both arms
**Verified:** 2026-08-01T19:39:27Z
**Status:** gaps_found (1 evidence-integrity gap; all four ROADMAP success criteria VERIFIED)
**Re-verification:** No — initial verification

## Goal Achievement

The phase goal is achieved. All four ROADMAP success criteria hold against the codebase, not
against SUMMARY prose: I recomputed the 2×2 from the committed CSVs, recomputed the gate
verdict by importing the driver's own constants, re-derived the within-run trajectory table,
regenerated both PNGs and hash-matched them byte-for-byte against the committed files, and
confirmed the pre-registration ordering in git history.

The single gap is a false provenance sentence about the *supplementary* D-12 samples file. It
touches no number in the headline claim.

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | **(SC1)** Naive and EWC arms run with identical seeds, config, and data order, differing ONLY in the penalty | ✓ VERIFIED | `finetune_ab.py:262-299` — one `build_train_config()`, one `fns` dict, one `seed_everything(SEED)` immediately before `GPT(...)`; `penalty_fn=penalty_for_arm(arm, penalty)` is the sole arm-conditional kwarg (plus `checkpoint_extra`, RNG-free). `_optimizer_step` (`loop.py:159`) evaluates the penalty inside the micro-batch loop with no RNG draw; `batch_fn` call count is arm-independent. Empirically: the EWC arm's step-250 `train_loss` (1.623079776763916) and `ewc_penalty` (0.08073534071445465) are **bit-identical** to `finetune_prod.csv`, and both arms' step-0 `dialog_ppl` is identical to the last digit (31.903875386436905). Roadmap wording "λ*" superseded — see human verification |
| 2 | **(SC2)** Headline is a 2×2 reporting both acquisition and retention for both arms | ✓ VERIFIED | `phase13_ab_report.md:53-57`. All four cells re-read by me from the CSV final rows: naive 4.192794562524908 / 8.52417066884246; EWC 4.573349242745997 / 3.8911400839446597 — exact match to the printed precision |
| 3 | **(SC3)** Forgetting-curve figure committed: retention PPL vs steps per arm, dashed baseline 2.1066, acquisition companion panel | ✓ VERIFIED | `results/phase13_forgetting_curve.png` tracked by git. Rendered and inspected: left panel = retention vs step, both arms; gray dashed axhline labeled "v1.0 headline 2.1066 (full-val, unmasked)"; right panel = masked dialogue PPL, same two arms. `plot_phase13.py:96-101` uses `HEADLINE_RETENTION = 2.1066`, never the 2.107553 sub-bin anchor |
| 4 | **(SC4)** λ frontier plot committed: retention vs acquisition, one point per λ from the sweep logs | ✓ VERIFIED | `results/phase13_frontier.png` tracked. Rendered and inspected: 6 annotated points, axes retention (y) vs dialogue (x), caption "1250-step sweep endpoints (LR 9e-5, unmasked) — not the 4000-step A/B arms". 5 points read live from `ft_lam_{0.01,0.1,1,10,100}.csv`; λ=0 is the documented provenance exception (`ft_lr_9e-5.csv` header confirmed to have no `retention_ppl` column) |
| 5 | Driver refuses (SystemExit) to overwrite either arm's existing outputs on re-run | ✓ VERIFIED | `finetune_ab.py:134-142` raises SystemExit naming the path; called at `:180` before any work. Pinned by `test_refuse_to_rerun_guard` |
| 6 | Gate verdict returns False at delta == MARGIN and True strictly above | ✓ VERIFIED | `ewc_mitigates` uses strict `>` (`finetune_ab.py:116`). Executed: boundary → False, boundary−1e-9 → True. (The *test* for this is weak — see anti-patterns WR-03) |
| 7 | Pre-registration constants committed in code AND report preamble BEFORE either arm ran (D-10) | ✓ VERIFIED | git history: `c3d942e` driver 14:28 → `91aedd1` tests 14:30 → `8fa2aa1` preamble 14:31 → `ead34c1` EWC CSV 15:14 → `389e861` naive CSV 15:53 → report fill 16:13/16:17. `git diff c3d942e HEAD -- scripts/finetune_ab.py` is **empty** — the driver is byte-identical to its pre-registration commit. `git diff 8fa2aa1 HEAD -- results/phase13_ab_report.md` removes only 7 `_Pending_` placeholder lines; the pre-registration table is byte-unchanged |
| 8 | λ_EWC = 0.01 is the headline λ, justified as the only sweep point moving both axes favorably | ✓ VERIFIED | `finetune_ab.py:87-90` with citation comment; report pre-registration table row + `## Reconciliation` "Why λ=0.01 is the headline (D-02)" with the λ=100 counter-case |
| 9 | Gate is retention-only: K=2 × Phase-12 noise floor, NO acquisition gate (D-06) | ✓ VERIFIED | `K=2`, `DELTA_RET=0.068930`, `MARGIN=0.13786` verified by import. Report `## Gate Verdict` states "There is no pass/fail gate on acquisition (D-06)". No acquisition threshold constant exists anywhere in the driver |
| 10 | Both arms start fresh from `checkpoints/best.pt` with the recorded twin config | ✓ VERIFIED | `finetune_ab.py:208-215`; `build_train_config()` returns `TrainConfig(lr=9e-05, batch_size=32, max_steps=4000, warmup_steps=100, grad_clip=1.0, grad_accum_steps=1, weight_decay=0.1, seed=1337)` — matches the `finetune_prod_run.log` twin config quoted in the report |
| 11 | Both arm CSVs exist at D-07 scoped paths with a step-0 row and a step-4000 final row | ✓ VERIFIED | Both tracked; 17 rows each; step-0 `dialog_ppl 31.903875386436905 / retention_ppl 2.107553076833866 / ewc_penalty 0.0`; final step 4000. Headers byte-identical across arms |
| 12 | EWC arm step-4000 retention within MARGIN of `finetune_prod.csv` (D-11) | ✓ VERIFIED | 3.8911400839446597 vs 3.891139975617828 → \|Δ\| = 1.08e-7, 1.3e-6 of MARGIN. `ewc_penalty` bit-identical (0.13435843586921692 both). Driver exited clean (no D-11 SystemExit) |
| 13 | Phase-12 artifacts byte-untouched | ✓ VERIFIED | `results/finetune_prod.csv` and `results/finetune_smoke_report.md` last touched at `87198ec` (Phase 12-05); `git status --porcelain` on both is empty. `finetune_prod.csv` appears in the driver only as `PROD_CSV` opened read-mode at `:333` |
| 14 | Both arm endpoint checkpoints exist locally, gitignored | ✓ VERIFIED | `checkpoints/phase13_ewc_latest.pt` (278 MB, carries the EWC extras) and `checkpoints/phase13_naive_latest.pt` (167 MB, no extras — consistent with the arm-conditional `checkpoint_extra`). `git ls-files checkpoints/` empty; `.gitignore:14` covers `checkpoints/` |
| 15 | Exactly two arms at 4000 steps — no extra λ arms (D-04) | ✓ VERIFIED | `ARMS = ("naive", "ewc")`, `main()` SystemExits on any other value. Only two `results/phase13_*/run.csv` files exist |
| 16 | Frontier has exactly SIX λ points labeled as 1250-step sweep endpoints | ✓ VERIFIED | `build_frontier_points()` executed → 6 tuples, labels `λ=0, 0.01, 0.1, 1, 10, 100`. All five sweep CSVs independently confirmed to end at step 1250. Pinned by `test_frontier_has_six_points` |
| 17 | Retention samples from BOTH arm endpoints in one markdown file, one script run, shared seeded prompt set, measured proxies | ✓ VERIFIED | `results/phase13_retention_samples.md` tracked; 10 prompt sections × 2 arms × (greedy + warm); proxies table for both arms (0/20 and 1/20 eos; 79 and 70 leakage). `make_retention_samples.py:145-171` loads both checkpoints inside one `for label, ckpt_path in ARMS` loop; prompts built once from `default_rng(1337)` |
| 18 | Gate verdict applies exactly `ewc_mitigates`; acquisition descriptive, no gate | ✓ VERIFIED | Recomputed by importing the driver: delta 4.633030584897801, MARGIN 0.13786, ratio **33.6068×** — report states "33.61×". Acquisition delta +0.380556 reported with the explicit no-gate sentence |
| 19 | One D-09 reconciliation section explains §8 search vs Phase-13 demonstration | ✓ VERIFIED | `## Reconciliation: §8 Search vs Phase-13 Demonstration` — single section, verbatim §8 block quote, side-by-side table (question / arms / rule / budget / outcome), "§8 stands unamended" |
| 20 | D-11 cross-check table shows fresh EWC arm vs prod endpoints side by side, reported regardless of outcome | ✓ VERIFIED | `## D-11 Reproduction Cross-Check` — all six cells match the CSVs I read. Plus the step-250 early-twin paragraph, which honestly records that the *planned* exact-PPL check did not hold (3.6e-8) and names the sharper weight-derived discriminator used instead |
| 21 | D-05 threats register names the floor's regime, the not-reverified-at-4000 limitation, and the naive within-run trajectory check | ✓ VERIFIED | `## Threats to Validity` §2 names seed pair (1337, 2024), masked arm, LR 9e-5, 1250 steps, with the 5.074896/5.005966 → 0.068930 derivation; states "NOT re-verified at the 4000-step production budget" and frames the 33.6×/67.2× ratio as "a judgment, not a proof". Trajectory table re-derived by me: 16 intervals, 13 up / 3 down, range [−0.062183, +2.915207], all downward excursions < MARGIN — **every value matches the report to the printed precision** |
| 22 | The report scopes its claim to teacher-forced retention PPL and reports the generation negative honestly | ✓ VERIFIED | `## Threats to Validity` §1 is a dedicated section leading with the negative: both arms leak role tokens (79 naive / 70 EWC), "does **not** yield a qualitatively intact story generator", "It does **not** claim qualitative or generative retention, and no figure or sentence here should be read as claiming it". `## Gate Verdict` carries the same scoping sentence. The samples file states it independently. This is the honest-evidence handling the phase required |
| 23 | Committed evidence artifacts make no provenance claim the artifacts themselves contradict | ✗ **FAILED** | The identical-RNG-stream claim in `phase13_retention_samples.md:8-9` and `phase13_ab_report.md:342` is contradicted by the committed samples themselves. See Gaps Summary |

**Score:** 22/23 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/finetune_ab.py` | Arm-parameterized A/B driver, `def ewc_mitigates` | ✓ VERIFIED | 361 lines, ruff-clean, import-safe (`main` under `__main__`), all six required module functions present, byte-unchanged since pre-registration |
| `tests/test_phase13_driver.py` | Guard + gate + config-identicality units | ✓ VERIFIED | 6 tests, all named in the plan, all pass. One is weak (WR-03) |
| `results/phase13_ab_report.md` | Complete A/B evidence report, `## Pre-Registration`, `## Reconciliation` | ✓ VERIFIED | 371 lines; all nine sections filled; every number I sampled traced to a committed CSV |
| `results/phase13_ewc/run.csv` | EWC forgetting curve, `retention_ppl` | ✓ VERIFIED | 17 rows, schema identical to `finetune_prod.csv` |
| `results/phase13_naive/run.csv` | Naive collapse curve, identical schema | ✓ VERIFIED | 17 rows, header byte-identical to the EWC arm |
| `scripts/plot_phase13.py` | VIZ-01 + VIZ-04 generation, `LAMBDA0_POINT` | ✓ VERIFIED | 167 lines, no torch import, `matplotlib.use("Agg")` before pyplot |
| `results/phase13_forgetting_curve.png` | VIZ-01 committed figure | ✓ VERIFIED | 104 KB, tracked, **byte-reproducible** from committed CSVs |
| `results/phase13_frontier.png` | VIZ-04 committed figure | ✓ VERIFIED | 62 KB, tracked, **byte-reproducible** from committed CSVs |
| `scripts/make_retention_samples.py` | D-12 one-run both-endpoints sampler | ⚠️ PARTIAL | Exists and ran; `STOP_IDS = {8184}`, `default_rng(1337)`, both checkpoints, output guard all present. Per-arm (not per-prompt) warm seeding makes its own stream-identity claim false — see gap |
| `results/phase13_retention_samples.md` | Representative samples, `REPRESENTATIVE` | ⚠️ PARTIAL | 10 prompts × 2 arms × 2 modes, proxies for both arms, honest negative framing. Header stream-identity claim false for 4 of 10 prompts |
| `tests/test_phase13_plots.py` | Frontier + baseline + smoke | ✓ VERIFIED | 3 tests, six-point assertion present, all pass |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `finetune_ab.py` | `personacore.training.train` | `penalty_fn=` seam | ✓ WIRED | `:279 penalty_fn=arm_penalty` — the sole arm-conditional value reaching `train()` besides `checkpoint_extra` |
| `finetune_ab.py` | `checkpoints/fisher_tinystories.pt` | `load_fisher` fingerprint-pinned | ✓ WIRED | `:222 load_fisher(FISHER_CACHE, expected_fingerprint=fingerprint)` with the git_sha/step/val_loss trio |
| `phase13_*/run.csv` | `finetune_prod.csv` | identical CSV schema | ✓ WIRED | `step,train_loss,val_loss,lr,tokens,wall_clock,dialog_ppl,ewc_penalty,retention_ppl` on all three |
| `plot_phase13.py` | `results/ft_lam_*.csv` | final-row endpoint reads | ✓ WIRED | 5 live reads executed; each CSV's final row confirmed at step 1250 |
| `make_retention_samples.py` | `checkpoints/phase13_naive_latest.pt` | both endpoints in ONE run | ✓ WIRED | Single `for label, ckpt_path in ARMS` loop over both checkpoints |
| `phase13_ab_report.md` | `results/phase13_naive/run.csv` | 2×2 cells from final rows | ✓ WIRED | All four cells verified against the CSVs |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `phase13_forgetting_curve.png` | `retention_ppl`, `dialog_ppl` series | `_series()` over both arm CSVs | Yes — regenerated PNG is **SHA-256 identical** to the committed file | ✓ FLOWING |
| `phase13_frontier.png` | 6 (λ, dialog, retention) points | 5 live CSV final-row reads + 1 cited constant | Yes — regenerated PNG **SHA-256 identical** | ✓ FLOWING |
| `phase13_ab_report.md` 2×2 | 4 endpoint cells | Final rows of both arm CSVs | Yes — every digit matches | ✓ FLOWING |
| `phase13_ab_report.md` gate verdict | delta, MARGIN, ratio | `ewc_mitigates` + arm CSVs | Yes — recomputed 33.6068× vs reported 33.61× | ✓ FLOWING |
| `phase13_ab_report.md` trajectory table | 16 interval deltas | naive arm CSV | Yes — all 16 values re-derived, exact match | ✓ FLOWING |
| `phase13_ab_report.md` D-11 table | 6 endpoint cells + Δ | fresh arm + `finetune_prod.csv` | Yes — all six verified | ✓ FLOWING |
| `phase13_retention_samples.md` proxies | eos fraction, leakage counts | 40 generations, both arms | Yes — measured, but the two arms' *warm* halves are not strictly paired after prompt 20081 | ⚠️ HOLLOW (pairing claim only; counts themselves are real measurements) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite green | `.venv/bin/python -m pytest tests/ -q` | 284 passed, 1 skipped, 109s | ✓ PASS |
| Gate boundary is strict | import driver; `ewc_mitigates(5.0, 5.0-MARGIN)` / `−1e-9` | `False` / `True` | ✓ PASS |
| Gate verdict on real data | `ewc_mitigates(8.52417..., 3.89114...)` | `True`, delta 4.633030584897801, ratio 33.6068× | ✓ PASS |
| One-bit difference | `penalty_for_arm("naive", S)` / `("ewc", S)` | `None` / `S` | ✓ PASS |
| Config identical across calls | `build_train_config() == build_train_config()` | `True` | ✓ PASS |
| Frontier point count | `build_frontier_points()` | 6 tuples, correct labels | ✓ PASS |
| Figures reproduce from committed data | regenerate to tmp, `shasum -a256` vs committed | **both SHA-256 identical** | ✓ PASS |
| Sweep CSVs are 1250-step endpoints | final row step of all 5 `ft_lam_*.csv` | all `1250` | ✓ PASS |
| Trajectory table re-derivation | recompute 16 naive-arm deltas | matches report exactly | ✓ PASS |
| Lint | `ruff check` + `ruff format --check` on 5 phase files | All checks passed; 84 files formatted | ✓ PASS |
| Both arms train end-to-end | — | ? SKIP | 37 min/arm on MPS; evidence is the committed CSVs + the bit-identical prod reproduction |

### Probe Execution

No `scripts/*/tests/probe-*.sh` exist in this repo and no PLAN/SUMMARY declares a probe. Not a
migration/tooling phase. **Step 7c: SKIPPED (no probes declared or discoverable).** The
equivalent runnable evidence is the behavioral spot-check table above, all executed in this
verifier's own process.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| DEMO-04 | 13-01, 13-02, 13-03, 13-04 | EWC A/B: identical seeds/config/data-order, differing ONLY in the penalty; both retention AND acquisition reported | ✓ SATISFIED | Truths 1, 2, 18. The "retention-only sleight of hand" the requirement names is explicitly avoided — both columns in the 2×2, plus a movement-from-anchor table |
| VIZ-01 | 13-03 | Forgetting-curve figure, dashed baseline 2.1066, acquisition companion panel, committed | ✓ SATISFIED | Truth 3; figure rendered and inspected; byte-reproducible |
| VIZ-04 | 13-03 | λ frontier plot, one point per λ from the sweep logs | ✓ SATISFIED | Truths 4, 16; 5 of 6 points read live from sweep CSVs, the 6th carries a pre-registered provenance exception |

**Orphaned requirements:** none. `REQUIREMENTS.md:113-115` maps exactly DEMO-04, VIZ-01, VIZ-04
to Phase 13; all three appear in plan frontmatter and all three are marked Complete.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `scripts/make_retention_samples.py` | 153 | Per-arm rather than per-prompt RNG seeding; the arms' streams desync after any early stop | ⚠️ WARNING | Materialized in committed evidence — the basis for the single gap below |
| `scripts/finetune_ab.py` | 103-106, 347 | `PROD_DIALOG_4000` / `PROD_RETENTION_4000` are printed but never compared; the only enforced D-11 check is against the mutable `finetune_prod.csv` (CR-02) | ⚠️ WARNING | The declared "tripwire" does not exist. Mitigated in fact: I confirmed `finetune_prod.csv` is byte-untouched since `87198ec`, so the recorded verdict is sound. The guard is missing for any future re-run |
| `tests/test_phase13_driver.py` | 57 | `ewc_mitigates(5.0, 5.0 - MARGIN)` — fp round-trip gives 0.13785999999999987 < MARGIN, so the assertion passes under both `>` and `>=` | ⚠️ WARNING | The "boundary is a FAIL" contract is stated but untested. Irrelevant to this phase's verdict (33.6× the margin); would matter for any future near-boundary result. Fix: `assert fab.ewc_mitigates(5.0 + fab.MARGIN, 5.0) is False` or compare against `fab.MARGIN` directly |
| `scripts/plot_phase13.py` | 64-71 | `_series` filters on truthiness; a missing column yields `([], [])` and plots an empty, valid-looking PNG | ⚠️ WARNING | Latent. Today's figures are correct and byte-reproducible; this is the exact Pitfall-1 failure mode the frontier is hardened against, left unguarded on the curve |
| `scripts/plot_phase13.py` | 81-83 | `rows[-1]` with no step-1250 assertion | ⚠️ WARNING | Latent. I confirmed all five sweep CSVs currently end at 1250 |

No `TBD` / `FIXME` / `XXX` / `TODO` / `HACK` / `PLACEHOLDER` markers in any file modified by
this phase — the debt-marker gate passes cleanly.

### Human Verification Required

#### 1. Accept (or amend) the roadmap-wording supersession

**Test:** SC1 reads "λ=0 vs λ\*", but Phase 12 §8 recorded λ\* = None. Phase 13 ran λ=0 vs a
pre-chosen λ=0.01.
**Expected:** The substitution is recorded in `results/phase13_ab_report.md` under
`## Reconciliation` ("ROADMAP wording superseded ... recorded here rather than silently absorbed
into the roadmap's phrasing") with D-02/D-09 rationale. Confirm this is the intended record, or
update ROADMAP.md Phase 13 SC1 to match.
**Why human:** A scope/wording acceptance decision. The *substance* of SC1 (identical seeds,
config, data order; one-bit difference) is fully verified — this is only about which λ symbol
the roadmap names.

#### 2. Decide the CR-01 resolution

**Test:** Choose Option A (thread a per-prompt `torch.Generator` into the warm `_complete()`
call and regenerate `results/phase13_retention_samples.md`) or Option B (keep the artifact and
correct the two claim sentences plus add a threats-register line).
**Expected:** The committed provenance sentence becomes true.
**Why human:** Both resolutions are defensible with different costs — a re-run versus a
two-sentence edit. Given the project's honest-evidence core value, the developer picks.

#### 3. Figure legibility at full size

**Test:** Open `results/phase13_forgetting_curve.png` and `results/phase13_frontier.png` at
full size; check for label collisions, log-axis readability on the acquisition panel, and
annotation clipping at λ=100.
**Expected:** Both read cleanly as portfolio artifacts.
**Why human:** Visual quality judgment. Structurally both figures are correct.

### Gaps Summary

**One gap. The phase goal is achieved; this is a correctness defect in a supplementary
artifact's provenance claim, not in the headline evidence.**

`scripts/make_retention_samples.py:153` calls `seed_everything(SEED)` once per **arm**, then
runs all 10 prompts inside that single global stream. `generation.core.generate` returns early
on a stop id, so the number of `torch.multinomial` draws consumed by a warm completion is
arm-dependent. The moment one arm stops early, every later prompt in that arm draws from a
shifted offset.

This already happened in the committed run. I located it independently of the code review by
measuring completion lengths in the committed markdown: the EWC arm's warm completion for
prompt **20081** is 151 characters against a 195–244 character band for every other warm
sample, while its greedy sibling is a normal 221 characters — and greedy consumes no RNG. That
prompt is the **6th of 10**, so the warm completions for the last four prompts in the EWC arm
were drawn from a shifted stream. It matches the reported `1/20` EWC stop exactly.

Two committed artifacts assert the opposite:

- `results/phase13_retention_samples.md:8-9` — "The warm-sampling RNG is re-seeded to 1337
  before EACH arm, so both arms draw from the identical stream and a text difference is a
  weight difference."
- `results/phase13_ab_report.md:342` — "warm-sampling RNG re-seeded per arm so both arms draw
  the identical stream" (no caveat; `## Threats to Validity` does not name it either).

For 4 of 10 prompts, a warm text difference is a weight difference **plus** an RNG-offset
difference. The greedy halves are unaffected (deterministic), and the 79/70 leakage counts and
0/20-vs-1/20 eos fractions remain real measurements of each arm — they are simply not a strictly
paired comparison on the warm half.

**What this does NOT touch.** No number in the headline evidence involves sampling: the 2×2
cells, the gate verdict (33.6× MARGIN), the D-11 reproduction (`ewc_penalty` bit-identical), the
within-run trajectory, and both figures all derive from teacher-forced eval over the committed
CSVs. I regenerated both PNGs and they are SHA-256 identical to the committed files. All four
ROADMAP success criteria hold.

**Why it is still a gap.** This project's stated core value is that the novel claim must be
*true and demonstrable* — the evidence has to be honest. A sentence in the committed report that
the committed data contradicts is exactly the class of defect that value exists to prevent, and
it costs two sentences to fix. Notably the phase's own report handles a much harder honesty
problem well: `## Threats to Validity` §1 leads with the measured negative that both arms fail
free-running story generation and explicitly refuses the qualitative retention claim. The same
standard applied to the sampling protocol closes this gap.

**Secondary (not gating, tracked as warnings):** the D-11 pre-registration literals are printed
but never compared (CR-02) — sound in fact here because `finetune_prod.csv` is byte-untouched
since Phase 12, but the declared guard does not exist for future re-runs; and
`test_gate_boundary` cannot distinguish `>` from `>=` because of a floating-point round-trip, so
the "boundary is a FAIL" contract is stated but untested.

---

_Verified: 2026-08-01T22:29:17Z (pass 2) / 2026-08-01T19:39:27Z (pass 1)_
_Verifier: Claude (gsd-verifier)_
