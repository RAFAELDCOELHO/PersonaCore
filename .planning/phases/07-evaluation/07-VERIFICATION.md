---
phase: 07-evaluation
verified: 2026-06-10T00:00:00Z
status: passed
score: 3/3 must-have criteria verified
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 2/3 (criterion 3 wired but un-run)
  gaps_closed:
    - "EVAL-03 ablation cohort run at the D-07-calibrated budget; results/results.md filled with real PPL + val-loss in all four rows (no _pending cells); per-variant abl_*.csv curves produced"
    - "Headline EVAL-01 perplexity 2.1066 over 12,636,922 tokens reproduced against best.pt and recorded in 07-HUMAN-UAT.md (status: complete)"
  gaps_remaining: []
  regressions: []
gaps: []
deferred: []
---

# Phase 7: Evaluation Verification Report

**Phase Goal:** Quantitative and qualitative proof of the trained model, plus the differentiating ablation study that lifts this above a student clone.
**Verified:** 2026-06-10
**Status:** passed
**Re-verification:** Yes — after the EVAL-03 ablation cohort was run and the headline PPL confirmed (the two human-attested items from the initial verification).

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP success criterion) | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Perplexity is computed and reported on a held-out set (EVAL-01) | ✓ VERIFIED | `src/personacore/evaluation/perplexity.py` is a substantive deterministic sweep (`reduction="sum"`, exact `corpus_len - n_windows` denominator, `@torch.no_grad()`, now with a zero-token guard from WR-01); brute-force-oracle + token-count + partial-window tests pass (3/3 re-run green). `scripts/evaluate.py:89` wires it to the real `best.pt`/`val.bin`. Headline **2.1066 over 12,636,922 scored target tokens** is recorded in `results/samples.md` (committed) and was reproduced on the M3 against `best.pt` (07-HUMAN-UAT item 2: passed). |
| 2 | Curated qualitative generation samples captured for the writeup (EVAL-02) | ✓ VERIFIED | `results/samples.md` is committed and substantive: 4 fixed prompts × {greedy, warm}, real coherent TinyStories continuations (verified by reading the file — e.g. "Once upon a time, there was a little girl named Sue…"), with an honest "representative, not cherry-picked" header and the headline PPL line. |
| 3 | 2–3 architecture/LR ablations are run and presented in a comparison table (EVAL-03) | ✓ VERIFIED | The cohort was **run** at the D-07-calibrated budget. `grep '_pending' results/results.md` returns NO matches (exit 1) — all four PPL and val-loss cells contain real numbers: baseline 2.8212 / 1.0426, no_tie 2.7870 / 1.0312, no_pos 2.9221 / 1.0796, depth_cut 3.0074 / 1.1078, all over 12,636,922 tokens. Five tracked CSVs exist (`abl_baseline/no_tie/no_pos/depth_cut.csv` each ending at step 2500 + `abl_calibration.csv` showing the 8k baseline curve, final val 0.8495). The table isolates exactly ONE knob per variant (verified against `KNOBS` dict, lines 68-73). Param counts reproduce exactly via live import. |

**Score:** 3/3 criteria achieved with concrete committed artifacts.

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/personacore/evaluation/perplexity.py` | Deterministic full-val PPL sweep | ✓ VERIFIED | `reduction="sum"`, memmap re-open, returns (ppl, total_tokens); WR-01 zero-token guard added; tests green. |
| `src/personacore/config.py` | Additive weight_tying / use_pos_emb (default True) | ✓ VERIFIED | Both present, default True; live import reproduces baseline arch. |
| `src/personacore/model/gpt.py` | Flag-gated tie + pos-emb seams | ✓ VERIFIED | Live import: untie → distinct param count (+3,145,728); no_pos → wpe dropped (-98,304). |
| `scripts/evaluate.py` | Headline PPL + curated samples driver | ✓ VERIFIED | Wires perplexity() (line 89) + generate_text_str; WR-02 removed the stale hardcoded literal — now single-sources from best.pt. |
| `scripts/run_ablations.py` | Calibration + 4-run cohort driver | ✓ VERIFIED | KNOBS isolates one knob/variant; `seed_everything(SEED)` before each build; untouched `train()`; per-variant `perplexity()` scoring; WR-03 calibration guard now ENFORCED (lines 341-346 fail loudly on divergence). |
| `results/results.md` | Committed comparison table with real data | ✓ VERIFIED | All 4 rows filled, NO `_pending` cells; param counts + D-06 fairness framing + strided footnote; cohort/headline budgets correctly separated. |
| `results/samples.md` | Committed qualitative samples | ✓ VERIFIED | Committed, real generated text, headline PPL line. |
| `results/abl_*.csv` (×4 + calibration) | Per-run restart-safe curves | ✓ VERIFIED | All five git-tracked; per-variant curves end at the locked 2500 budget; final val-losses match the table exactly. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| perplexity.py | GPT.forward | `model(x)` + `cross_entropy(reduction="sum")` | ✓ WIRED | Present. |
| evaluate.py | perplexity | `perplexity(model, VAL_BIN, ...)` | ✓ WIRED | Line 89; headline number reproduced. |
| run_ablations.py | train | `train(train_config=..., model=..., model_config=...)` | ✓ WIRED | Lines 214-227; cohort ran end-to-end. |
| run_ablations.py | seed_everything | re-seed before each GPT(ModelConfig(**knob)) | ✓ WIRED | Line 207 — fairness guarantee. |
| run_ablations.py | perplexity | per-variant scoring | ✓ WIRED | Line 233; four real PPL values produced. |
| run_ablations.py | calibrate guard | `abs(recommended - REDUCED_MAX_STEPS) > EVAL_INTERVAL` → SystemExit | ✓ WIRED | Lines 341-346 (WR-03 fix); budget lock now enforced. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| results/samples.md | greedy/warm text + headline PPL | generate_text_str + perplexity(best.pt) on M3 | Yes — real coherent text, reproduced number | ✓ FLOWING |
| results/results.md | PPL / val-loss cells | run_cohort() perplexity() per variant | Yes — 4 real values, no `_pending`; match per-variant CSVs | ✓ FLOWING |
| results/abl_*.csv | per-step val-loss curves | train() CSVLogger per variant | Yes — distinct curves per variant, ending at step 2500 | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Perplexity accounting tests | `pytest tests/test_perplexity.py` | 3 passed | ✓ PASS |
| Ablation flag tests | `pytest tests/test_ablation_config.py` | 3 passed | ✓ PASS |
| Param counts reproduce | live import of GPT for all 4 knobs | 13,891,584 / 17,037,312 / 13,793,280 / 8,568,192 — exact match to table | ✓ PASS |
| No pending cells | `grep '_pending' results/results.md` | exit 1 (no matches) | ✓ PASS |
| Per-variant CSV budget | tail of each abl_*.csv | all end at step 2500 (locked budget) | ✓ PASS |
| CSV val-loss matches table | cross-check final rows | baseline 1.0426 / no_tie 1.0312 / no_pos 1.0796 / depth_cut 1.1078 — exact | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| EVAL-01 | 07-01, 07-02 | Perplexity computed on held-out set | ✓ SATISFIED | perplexity() tested + wired; evaluate.py reports it; 2.1066 reproduced (UAT item 2 passed). |
| EVAL-02 | 07-02 | Curated qualitative samples captured | ✓ SATISFIED | results/samples.md committed with real coherent generations. |
| EVAL-03 | 07-01, 07-02, 07-03 | 2–3 ablations run + comparison table | ✓ SATISFIED | Cohort RUN at calibrated budget; 4-row table with real PPL + val-loss (no `_pending`), one knob isolated per variant, five tracked CSV curves. |

All three requirement IDs declared in the plans appear in REQUIREMENTS.md (lines 53-55, 125-127), mapped to Phase 7 and marked Complete. No orphaned requirements.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| — | — | No `_pending` / TBD / FIXME / XXX markers in phase artifacts | — | The prior Warning (4 `_pending` cells) is RESOLVED. |

No blocker, warning, or info anti-patterns remain. The two prior code-review notes are closed: WR-01 (zero-token guard added) and WR-03 (calibration recommendation now enforced via fail-loud guard, not discarded). Full suite reported 122 passed / 1 skipped in 07-REVIEW-FIX.md; the 6 phase-specific tests re-run green here.

### Human Verification Required

None. Both items from the initial verification are now satisfied by committed artifacts and reproduced numbers (07-HUMAN-UAT.md status: complete, 2/2 passed, 0 pending):
1. EVAL-03 cohort ran (2026-06-10), all four cells filled, five CSVs committed.
2. Headline EVAL-01 perplexity 2.1066 over 12,636,922 tokens reproduced against best.pt.

### Gaps Summary

No gaps. All three roadmap success criteria are achieved with concrete, committed, self-consistent artifacts:

- **EVAL-01** — deterministic `perplexity()` sweep, tested and wired; headline 2.1066 / 12,636,922 tokens reproduced.
- **EVAL-02** — `results/samples.md` with real, coherent, honestly-labeled generations.
- **EVAL-03** (the differentiator) — the ablation cohort is now genuinely RUN, not scaffolded. `results/results.md` carries real numbers in all four rows with zero `_pending` cells (grep-confirmed), each variant isolating exactly one knob (KNOBS dict + live-import param counts verified), backed by five git-tracked CSV curves at the D-07-calibrated, fairness-locked 2500-step budget. The relative ranking (no_tie best, depth_cut worst) is a real comparison that supports the per-variant "what this shows" conclusions.

The phase's differentiating claim — that the architecture choices are empirically justified, not asserted — is now demonstrated by data. Phase goal achieved; ready to proceed to Phase 8 (Demo & Writeup).

---

_Verified: 2026-06-10_
_Verifier: Claude (gsd-verifier)_
