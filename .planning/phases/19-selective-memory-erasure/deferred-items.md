# Phase 19 — Deferred Items

Out-of-scope discoveries logged during execution. Not fixed here.

## `perplexity.py`'s stated denominator invariant is stale prose

**Found during:** 19-10 Task 3 (verifying the retention window accounting before recording it)

`src/personacore/evaluation/perplexity.py:11-13` states:

> A length-L window predicts L-1 transitions: token 0 is context-only, never scored.
> So the denominator is `corpus_len - n_windows` (each scored window loses its first
> token as unpredictable).

That form is only correct for **disjoint** slices. The code slices `data[i : i + block_size + 1]`
at stride `block_size` (`:62`), so consecutive windows **share their boundary token** — it is
window *k*'s last target and window *k+1*'s first context token — and every target `1..n-1` is
scored exactly once. The true denominator is `corpus_len - 1`.

Measured on the retention corpus (`data/retention_val.bin`, n = 1,000,286, block 256):

```
n_windows                 = 3908
measured denominator      = 1000285
n - 1                     = 1000285   match: True
n - n_windows (docstring) = 996378    match: False
```

**The module's own test already knows.** `tests/test_perplexity.py:98-104` describes the shared
boundary token correctly and `:122` asserts `ntok == n_tokens - 1`. Only the module docstring
(and `test_perplexity.py:11`'s summary line, which repeats it) carries the stale form.

**Why deferred:** `perplexity.py` is the frozen gate-metric module (DEBT-02 for the retention
wrapper, TUNE-01 for `masked_perplexity`). The defect is in **prose only** — no measured number
in this repository is wrong because of it, and every committed PPL denominator is the correct
`n - 1`. Editing a frozen module's docstring mid-phase to fix a comment is not worth the churn
against Phase 19's ancestry discipline. 19-10 recorded the correct accounting in
`results/phase19_noise_floors.json` (`n_scored_tokens == corpus_tokens - 1`, asserted by
`tests/test_phase19_noise_floors.py`), so the artifact is right regardless.

**Fix when:** any phase already touching `src/personacore/evaluation/perplexity.py`. One-line
docstring correction; no code change.
