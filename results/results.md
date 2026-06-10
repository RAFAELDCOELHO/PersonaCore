# PersonaCore — Architecture Ablation Cohort (EVAL-03)

> **Reduced-budget, self-consistent cohort (D-06).** All four runs below train through
> the UNTOUCHED `train()` harness at IDENTICAL seed (1337), data, LR, warmup, and
> budget (`max_steps=2500`, calibrated per D-07) — only the ablated knob
> differs. The numbers are comparable to EACH OTHER, NOT to the headline 50k `best.pt`.
>
> The headline production figure is reported SEPARATELY (EVAL-01, `scripts/evaluate.py`):
> deterministic full-val perplexity **2.1066** over **12,636,922** scored target tokens
> on the 50k-step `best.pt` — a different (larger) budget, listed here only for context.

| Variant | Param count | Held-out PPL (reduced budget) | Best val-loss | What this shows |
| --- | --- | --- | --- | --- |
| baseline | 13,891,584 | 2.8212 (over 12,636,922 tokens) | 1.0426 | The fair reference — full 6-layer tied + positional arch at the reduced budget. |
| no_tie | 17,037,312 | 2.7870 (over 12,636,922 tokens) | 1.0312 | Whether sharing the input/output embedding helps (or hurts) at this scale. |
| no_pos | 13,793,280 | 2.9221 (over 12,636,922 tokens) | 1.0796 | Whether the learned positional embedding is load-bearing for coherence. |
| depth_cut | 8,568,192 | 3.0074 (over 12,636,922 tokens) | 1.1078 | The depth-vs-params tradeoff: half the layers (~38% fewer params), equal budget. |

## Notes

- **Fairness (07-RESEARCH Pitfall 3):** the data each variant sees is bit-for-bit the
  same — `seed_everything` re-seeds the global numpy RNG (the data sampler's source)
  before each variant build, so only the ablated knob (and the torch init stream it
  consumes) varies.
- **Held-out PPL** is the deterministic non-overlapping-window `perplexity()` sweep (Plan
  01), reported with its auditable token denominator. Same sweep for every variant.

> **Footnote (deferred idea — strided / sliding-window PPL):** this cohort uses
> non-overlapping windows, which slightly OVER-estimate perplexity versus a strided
> (sliding-window) sweep that gives most tokens more left-context (07-RESEARCH State of
> the Art). A strided variant of `perplexity()` is deferred; because the bias is uniform
> across variants at the same block_size, the RELATIVE ranking in the table holds.
