---
phase: 07-evaluation
verified: 2026-06-09T00:00:00Z
status: human_needed
score: 2/3 must-have criteria fully verified in artifacts; criterion 3 wired but un-run
overrides_applied: 0
human_verification:
  - test: "Run the EVAL-03 ablation cohort and fill results/results.md"
    expected: "`python scripts/run_ablations.py` (M3, Python 3.11 venv, ~6.6h) calibrates REDUCED_MAX_STEPS, trains baseline + no_tie + no_pos + depth_cut through the untouched train() at identical seed/data/LR/budget, scores each with perplexity(), and OVERWRITES results/results.md so all four held-out PPL and best-val-loss cells contain real numbers (no `_pending` markers) plus per-run results/abl_*.csv curves."
    why_human: "The cohort is a ~6.6h manual M3 training run by explicit design (T-07-07 accept; reads data/train.bin + checkpoints, not runnable in CPU CI). The committed table currently has 4 `_pending M3 cohort run_` cells and no abl_*.csv exist — the comparison the criterion requires is not yet present. Cannot be executed by the verifier."
  - test: "Confirm the headline full-val perplexity number (EVAL-01)"
    expected: "`python scripts/evaluate.py` (M3) prints headline full-val perplexity and writes results/samples.md. The committed artifacts report 2.1066 over 12,636,922 tokens; confirm the number reproduces against the shipped best.pt."
    why_human: "Requires loading the 159MB gitignored checkpoints/best.pt + data/val.bin and running on MPS; not reproducible in CPU CI. The driver wiring is statically verified and the artifact is committed, but the runtime number is a manual attestation."
gaps: []
deferred: []
---

# Phase 7: Evaluation Verification Report

**Phase Goal:** Quantitative and qualitative proof of the trained model, plus the differentiating ablation study that lifts this above a student clone.
**Verified:** 2026-06-09
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP success criterion) | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Perplexity is computed and reported on a held-out set (EVAL-01) | ✓ VERIFIED (driver), ? human-attested number | `src/personacore/evaluation/perplexity.py` is a substantive (`reduction="sum"`, exact denominator, `@torch.no_grad()`) sweep; brute-force-oracle + token-count + partial-window tests pass (3/3). `scripts/evaluate.py:88` wires it to the real `best.pt`/`val.bin` and prints PPL + `total_tokens`. Headline 2.1066 / 12,636,922 tokens is recorded by the manual M3 run and appears in both committed artifacts. The runtime number itself needs human re-confirmation (best.pt is gitignored, MPS-only). |
| 2 | Curated qualitative generation samples captured for the writeup (EVAL-02) | ✓ VERIFIED | `results/samples.md` is committed and substantive: 4 fixed prompts × {greedy, warm}, real coherent TinyStories continuations (not placeholders), with an honest "representative, not cherry-picked" header. Produced by a real M3 run of `evaluate.py` against best.pt. |
| 3 | 2–3 architecture/LR ablations are run and presented in a comparison table (EVAL-03) | ✗ NOT YET RUN — wired, scaffolded, but no results | `scripts/run_ablations.py` is fully wired (calibrate + 4-variant cohort + table writer; verified-wired by a 30-step train() probe per SUMMARY). `results/results.md` is committed with all 4 rows and verified param counts. BUT all 4 held-out-PPL cells and all 4 best-val-loss cells read `_pending M3 cohort run_` (grep: 4 pending markers), and NO `results/abl_*.csv` curves exist. The cohort (~6.6h M3) was never executed, so the comparison the criterion demands is absent. Routed to human verification (cannot run in CI / by verifier). |

**Score:** 2/3 criteria fully achieved in committed artifacts. Criterion 3's *driver + scaffold* are verified, but its *result* (the actual ablation comparison) is not present and requires a manual run.

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/personacore/evaluation/perplexity.py` | Deterministic full-val PPL sweep | ✓ VERIFIED | 66 lines, `reduction="sum"`, np.memmap re-open, returns (ppl, total_tokens); wired to GPT.forward; tests green. |
| `src/personacore/evaluation/__init__.py` | Barrel re-export | ✓ VERIFIED | `from .perplexity import perplexity`. |
| `src/personacore/config.py` | Additive weight_tying / use_pos_emb flags (default True) | ✓ VERIFIED | Both present at lines 93-94, default True. |
| `src/personacore/model/gpt.py` | Flag-gated tie + pos-emb seams | ✓ VERIFIED | `if config.use_pos_emb` gates wpe registration (line 163) + forward (line 200); `if config.weight_tying` gates the tie (line 183). Untie → distinct data_ptr; no_pos → wpe absent (both confirmed by live import). |
| `scripts/evaluate.py` | Headline PPL + curated samples driver | ✓ VERIFIED | Wires perplexity() + generate_text_str + preflight gate + RuntimeConfig; loads real best.pt; no argparse; writes results/samples.md. |
| `scripts/run_ablations.py` | Calibration + 4-run cohort driver | ✓ VERIFIED (wiring) | Wires seed_everything before each variant, untouched train(), perplexity() scoring, preflight gate + RuntimeConfig; train() call kwargs match the keyword-only signature (loop.py:150). |
| `results/results.md` | Committed comparison table | ⚠️ SCAFFOLD ONLY | Committed + git-tracked; 4 rows + verified param counts + D-06 framing + strided footnote — but PPL/val-loss cells all `_pending`. No comparison data. |
| `results/samples.md` | Committed qualitative samples | ✓ VERIFIED | Committed, git-tracked, real generated text. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| perplexity.py | GPT.forward | `logits, _ = model(x)` + `cross_entropy(..., reduction="sum")` | ✓ WIRED | Present line 60-63. |
| perplexity.py | val.bin memmap | `np.memmap(..., mode="r")` | ✓ WIRED | Line 49. |
| evaluate.py | perplexity | `perplexity(model, VAL_BIN, ...)` | ✓ WIRED | Line 88. |
| evaluate.py | generate_text_str | greedy + warm sample calls | ✓ WIRED | Lines 118, 121; export confirmed. |
| run_ablations.py | train | `train(train_config=..., model=..., model_config=...)` | ✓ WIRED | Lines 138, 208; signature matches. |
| run_ablations.py | seed_everything | re-seed before each GPT(ModelConfig(**knob)) | ✓ WIRED | Lines 134, 201. |
| run_ablations.py | perplexity | `perplexity(model, VAL_BIN, ...)` | ✓ WIRED | Line 228. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| results/samples.md | greedy/warm text | generate_text_str(best.pt) on M3 | Yes — real coherent text committed | ✓ FLOWING |
| results/results.md | PPL / val-loss cells | run_cohort() perplexity() per variant | No — cohort never run; cells `_pending` | ✗ DISCONNECTED (un-run, by design) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Perplexity accounting tests | `pytest tests/test_perplexity.py` | 3 passed | ✓ PASS |
| Ablation flag tests | `pytest tests/test_ablation_config.py` | 3 passed | ✓ PASS |
| Untie produces distinct head | live import of GPT(ModelConfig(weight_tying=False)) | distinct data_ptr True | ✓ PASS |
| no_pos drops wpe | live import of GPT(ModelConfig(use_pos_emb=False)) | no wpe attr True | ✓ PASS |
| Drivers parse | `ast.parse` evaluate.py + run_ablations.py | OK | ✓ PASS |
| Full ablation cohort produces PPL | `python scripts/run_ablations.py` | NOT RUN (~6.6h M3, gitignored data) | ? SKIP → human |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| EVAL-01 | 07-01, 07-02 | Perplexity computed on held-out set | ✓ SATISFIED (number human-attested) | perplexity() tested + wired; evaluate.py reports it; 2.1066 in committed artifacts. |
| EVAL-02 | 07-02 | Curated qualitative samples captured | ✓ SATISFIED | results/samples.md committed with real generations. |
| EVAL-03 | 07-01, 07-02, 07-03 | 2–3 ablations run + comparison table | ⚠️ PARTIAL | Driver wired + verified, table scaffolded with verified param counts, but the cohort was NOT run — all PPL/val-loss cells pending. The "run" half of the criterion is outstanding. |

All three requirement IDs declared in the plans appear in REQUIREMENTS.md (lines 53-55, 125-127), mapped to Phase 7. No orphaned requirements.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| results/results.md | 14-17 | `_pending M3 cohort run_` in all PPL/val-loss cells | ⚠️ Warning | The comparison table has no comparison data; EVAL-03's analytical payload is absent until the manual run. Honestly marked, not fabricated. |
| scripts/run_ablations.py | 319 | `calibrate()` return discarded; cohort uses module constant | ℹ️ Info | Code-review WR-03: calibration recommendation is not enforced against REDUCED_MAX_STEPS — human foot-gun on the long run, not a wiring defect. |
| src/personacore/evaluation/perplexity.py | 66 | unguarded `total_ce / total_tokens` | ℹ️ Info | Code-review WR-01: ZeroDivisionError on an empty/1-token corpus. Not triggered by the real val.bin; robustness gap only. |

No 🛑 blocker anti-patterns. No TBD/FIXME/XXX debt markers in any phase-modified source file.

### Human Verification Required

#### 1. Run the EVAL-03 ablation cohort (the differentiator)

**Test:** On the M3 (Python 3.11 venv): `python scripts/run_ablations.py`
**Expected:** Calibrates REDUCED_MAX_STEPS, trains baseline + no_tie + no_pos + depth_cut through the untouched `train()` at identical seed/data/LR/budget, scores each with `perplexity()`, and OVERWRITES `results/results.md` so all four held-out-PPL and best-val-loss cells contain real numbers (no `_pending`) and `results/abl_*.csv` curves are produced. Verify the table then supports the per-variant "what this shows" conclusions.
**Why human:** ~6.6h manual M3 run by design (T-07-07 accept); reads gitignored `data/train.bin` + checkpoints; not runnable in CPU CI or by the verifier. This is the un-run half of criterion #3.

#### 2. Confirm the headline perplexity (EVAL-01)

**Test:** `python scripts/evaluate.py` on the M3.
**Expected:** Prints headline full-val perplexity (committed artifacts claim 2.1066 over 12,636,922 tokens) and regenerates `results/samples.md`.
**Why human:** Requires the 159MB gitignored `best.pt` + `val.bin` on MPS; driver wiring is statically verified and the artifact is committed, but the runtime number is a manual attestation.

### Gaps Summary

There are no code-level gaps: every artifact exists, is substantive, is wired, and the test suite (6/6 phase tests, full suite reported green) passes. EVAL-01 and EVAL-02 are achieved with concrete committed artifacts (real samples; the headline PPL recorded in both artifacts).

The single outstanding item is the **un-run EVAL-03 ablation cohort**. The driver and table scaffold are honestly delivered and verified-wired, but the comparison table presents no comparison — all four PPL and val-loss cells read `_pending M3 cohort run_` and no per-run CSV curves exist. The roadmap criterion is "2–3 ablations are **run** and presented"; the "run" half is outstanding. This is not a code defect to fix (there is nothing to re-plan) but a deliberate ~6.6h manual M3 task (T-07-07) that only a human can execute. It is therefore surfaced as a human-verification item rather than a gap, and it is NOT covered by any later phase (Phase 8 is Demo & Writeup). Until that run lands and fills the table, the phase's differentiating claim — the thing meant to lift this above a student clone — is asserted by infrastructure but not yet demonstrated by data.

Two code-review robustness notes (WR-01 unguarded division, WR-03 unenforced calibration) are informational and do not block the goal.

---

_Verified: 2026-06-09_
_Verifier: Claude (gsd-verifier)_
