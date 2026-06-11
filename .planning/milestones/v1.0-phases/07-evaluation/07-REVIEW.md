---
phase: 07-evaluation
reviewed: 2026-06-09T00:00:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - scripts/evaluate.py
  - scripts/run_ablations.py
  - src/personacore/config.py
  - src/personacore/evaluation/__init__.py
  - src/personacore/evaluation/perplexity.py
  - src/personacore/model/gpt.py
  - tests/test_ablation_config.py
  - tests/test_perplexity.py
  - results/results.md
  - results/samples.md
findings:
  critical: 0
  warning: 5
  info: 4
  total: 9
status: issues_found
---

# Phase 7: Code Review Report

**Reviewed:** 2026-06-09T00:00:00Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Phase 7 ships the evaluation layer: a deterministic full-corpus `perplexity()` sweep, a no-CLI
`evaluate.py` driver (headline PPL + qualitative samples), a `run_ablations.py` cohort driver,
and two backward-compatible `ModelConfig` ablation flags (`weight_tying`, `use_pos_emb`) wired
into `GPT`. The core accounting in `perplexity()` is correct — I traced the window/stride logic
by hand and confirmed targets are scored exactly once (no double-count of the shared boundary
token), and the test suite's brute-force oracle is a genuinely independent reference. The
ablation-fairness reasoning (global-numpy RNG re-seeded per variant) checks out against
`training/data.py` and `seeding.py`.

No BLOCKER-tier defects were proven. The findings below are correctness-robustness gaps
(unguarded division, silent fallbacks, a self-contradicting committed artifact) and quality
issues. The most consequential is the unguarded `total_tokens == 0` division in `perplexity()`
(WR-01) and an internal numeric contradiction between the committed results and the driver
docstrings (WR-02).

## Warnings

### WR-01: `perplexity()` divides by zero on an empty or single-token corpus

**File:** `src/personacore/evaluation/perplexity.py:66`
**Issue:** The final `return math.exp(total_ce / total_tokens), total_tokens` has no guard for
`total_tokens == 0`. When `n <= 1` the loop `range(0, n - 1, block_size)` never executes (or only
yields windows of `numel < 2` that `continue`), leaving `total_tokens = 0` and raising an
unhandled `ZeroDivisionError`. This is a public function (`evaluation.__init__` re-exports it) and
the only validation guarding it is the caller's `VAL_BIN.exists()` check — an existing-but-empty or
1-token `val.bin` (a truncated/corrupt memmap) crashes with an opaque traceback instead of a clear
error. A truncated checkpoint/corpus is a realistic failure mode on a multi-session M3 run.
**Fix:**
```python
    if total_tokens == 0:
        raise ValueError(
            f"perplexity(): no scorable tokens in {val_bin_path!r} "
            f"(corpus length {n}); need at least 2 tokens."
        )
    return math.exp(total_ce / total_tokens), total_tokens
```

### WR-02: Committed `results.md` / `samples.md` headline PPL contradicts the driver docstrings

**File:** `results/results.md:9-10`, `results/samples.md:8`, `scripts/evaluate.py:95`,
`scripts/run_ablations.py:264-266`
**Issue:** `evaluate.py:95` (and `run_ablations.py`'s preamble) describe `best.pt`'s recorded
random-batch figure as `val_loss 0.7378 / ppl 2.091`, and explicitly frame the deterministic
full-sweep number as "distinct." But the committed `results.md:9` and `samples.md:8` report the
full-sweep headline as **2.1066**. The narrative says the full-sweep PPL should differ from the
random-batch 2.091 — yet 2.1066 is essentially equal to 2.091 (and slightly *higher*, consistent
with the over-estimation footnote). That is internally plausible, but the committed `evaluate.py`
hardcodes the *old* "2.091" figure in a printed NOTE while the committed artifacts show 2.1066,
so the shipped driver prints a number that disagrees with the shipped artifact it generates. A
reviewer/portfolio reader sees two different "headline-adjacent" numbers with no reconciliation.
**Fix:** Make the hardcoded comparison figures in `evaluate.py:94-96` and `run_ablations.py:262`
single-source (read from `best.pt`'s `val_loss` at runtime, e.g.
`blob.get("val_loss")`) rather than embedding a stale literal, or update the literal and add one
sentence reconciling 2.091 (sampled batch) vs 2.1066 (full sweep) so the artifact is self-consistent.

### WR-03: `run_ablations.py` ignores the calibrated budget it computes

**File:** `scripts/run_ablations.py:319-322`
**Issue:** `main()` calls `calibrate(runtime)` (an ~8,000-step, multi-hour baseline train) purely
for its printed side effect; its return value is discarded, and `run_cohort()` uses the
module-level `REDUCED_MAX_STEPS = 6_000` constant. So the cohort can train at a budget that the
just-computed calibration *recommended against*, with no error and no enforced reconciliation —
the only safeguard is a human reading stdout and manually editing the constant. On a 6.6-hour run
this is a real foot-gun: a stale `REDUCED_MAX_STEPS` silently produces an unfair-budget cohort
while the calibration evidence scrolls past in the log. The "executor LOCKS it" convention is
documented but unenforced.
**Fix:** Either capture and assert agreement, or fail loudly on drift:
```python
    recommended = calibrate(runtime)
    if abs(recommended - REDUCED_MAX_STEPS) > EVAL_INTERVAL:
        raise SystemExit(
            f"Calibration recommends max_steps={recommended} but REDUCED_MAX_STEPS="
            f"{REDUCED_MAX_STEPS}. Update the constant and re-run (D-07)."
        )
```
At minimum, log a prominent WARNING when they diverge.

### WR-04: `_read_val_curve` crashes on non-finite val_loss values other than the literal `"nan"`

**File:** `scripts/run_ablations.py:118-120`
**Issue:** The skip filter is a literal string match: `if v not in (None, "", "nan")`. A CSV value
written by a diverged run as `"NaN"`, `"-nan"`, `"inf"`, or `"-inf"` (all valid `float(...)`
inputs) passes the filter, then `float(v)` yields a non-finite value that is appended to `curve`.
Downstream `calibrate()` arithmetic (`first_val - early`, slope comparisons, `1.0 <= val <= 1.3`)
silently produces `nan`/`inf` comparisons that evaluate `False`, so calibration falls through to
`curve[-1][0]` without flagging the divergence — masking a blown-up training run as a "didn't
flatten" result. Loss divergence during calibration is exactly the signal this function exists to
catch.
**Fix:** Filter on numeric finiteness, not string identity:
```python
            v = row.get("val_loss", "")
            if v in (None, ""):
                continue
            val = float(v)
            if not math.isfinite(val):
                continue
            rows.append((int(float(row["step"])), val))
```

### WR-05: `best_val_loss` fallback silently fabricates a derived metric under a misleading column

**File:** `scripts/run_ablations.py:229`
**Issue:** `best_val_loss = float(blob.get("val_loss", math.log(ppl)))`. When a checkpoint lacks a
`val_loss` key, the code substitutes `math.log(ppl)` — i.e. the full-sweep *mean CE*, a different
quantity than the random-batch `val_loss` the column purports to show. This value is then written
verbatim into the committed `results.md` "Best val-loss" column with no annotation, so the table
can present a full-sweep-derived number indistinguishable from a real recorded best-val-loss. Two
rows could thus be non-comparable while looking identical. Since this is a self-produced checkpoint
from the same `train()` harness, a missing `val_loss` key would itself indicate a problem worth
surfacing, not papering over.
**Fix:** Treat a missing key as an error (or mark the cell): `blob["val_loss"]` directly so a
missing key raises, or, if a fallback is intended, store and render it distinctly
(e.g. `best_val_loss = None` and emit `"n/a (sweep CE {math.log(ppl):.4f})"` in the table cell).

## Info

### IN-01: `perplexity()` accepts an unused `batch_size` parameter

**File:** `src/personacore/evaluation/perplexity.py:31,41`
**Issue:** `batch_size=32` is documented as "accepted for signature parity ... unused here." A
dead parameter invites a caller to pass `batch_size=N` expecting batched scoring and silently get
one-window-at-a-time behavior. Documented, but still a latent API-misuse trap.
**Fix:** Drop the parameter, or implement true batching. If kept for parity, consider a leading
underscore (`_batch_size`) to signal intentional non-use.

### IN-02: Unused import `ModelConfig` paths reconstruct `ModelConfig()` repeatedly

**File:** `scripts/run_ablations.py:145,215,228` and `scripts/evaluate.py:88`
**Issue:** `ModelConfig()` is re-instantiated inline several times (`ModelConfig().eos_id`,
`ModelConfig().block_size`, `ModelConfig(**knob)` built twice per loop iteration at lines 202 and
212). Minor duplication / magic re-construction; the per-variant `ModelConfig(**knob)` is built
once for the model and again for `train()`'s `model_config=`, which is redundant and risks the two
drifting if the call is edited. Bind once: `mc = ModelConfig(**knob)` and reuse.
**Fix:** Hoist a single `mc = ModelConfig(**knob)` per iteration and pass it to both `GPT(mc)` and
`model_config=mc`.

### IN-03: Greedy/warm sample labeling relies on undocumented kwarg passthrough

**File:** `scripts/evaluate.py:118-128`
**Issue:** The warm sample omits `greedy=False` and relies on `generate_text`'s default
(`greedy=False` in `core.generate`). This is correct today, but the contract is implicit two layers
deep (`generate_text_str` -> `generate_text(**kw)` -> `core.generate`). If the default ever flips,
the "warm" sample silently becomes greedy with no test catching it (the cohort/sample run is not in
CI). Low risk, noted for traceability.
**Fix:** Pass `greedy=False` explicitly in the warm call for self-documentation and defense against
a default change.

### IN-04: `results.md` token denominator inconsistency between artifacts

**File:** `results/results.md:10` vs `results/samples.md:8`
**Issue:** `results.md:10` formats the denominator as `12,636,922` (thousands separators) while
`samples.md:8` writes `12636922` (no separators). Both come from `total_tokens`, formatted
differently across the two writers (`run_ablations.py:266` hardcodes the comma'd literal;
`evaluate.py:112` uses `{total_tokens}` with no `:,`). Cosmetic, but the two committed portfolio
artifacts present the same canonical number two ways.
**Fix:** Use `{total_tokens:,}` in `evaluate.py:112` for consistent formatting, and prefer deriving
the `results.md` context line from the actual measured value rather than a hardcoded literal.

---

_Reviewed: 2026-06-09T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
