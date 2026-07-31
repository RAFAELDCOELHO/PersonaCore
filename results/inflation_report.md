# PersonaChat Tokenizer-Inflation Report (DATA-04, D-08/D-09/D-10)

> **What these numbers are:** the four pre-registered D-08 inflation metrics for the FULL
> PersonaChat self_revised corpus (train + valid COMBINED: 8,939 + 1,000
> = 9,939 episodes), tokenized through the frozen production tokenizer
> (`artifacts/tokenizer.json`) via `encode_dialogue` — the SAME path the bin builder uses, so
> gate and bins can never tokenize differently (Pitfall 4). **What they are not:** comparable
> to any other tokenizer, word-count rule, or serialization format; the ratio below is only
> meaningful against the TinyStories baseline recomputed in this same run.

## D-08 Metrics

| # | Metric | Value | Auditable denominator |
| --- | --- | --- | --- |
| 1 | Dialogue tokens/word | **3.229** | over 4,800,385 utterance tokens / 1,486,754 whitespace words |
| 2 | Persona-span cost (tokens) | p50 94 / p90 126 / max 182 | over 9,939 episodes (`<|system|>` + persona ids) |
| 3 | Fit fraction (persona + first exchange <= 256) | **0.9996** | 9,935 / 9,939 episodes (block_size 256 = ModelConfig.block_size) |
| 4 | Fragmentation samples | see below | token count per fixed probe word |

| Probe word | Tokens |
| --- | --- |
| `halloween` | 5 |
| `cheetah` | 5 |
| `remodel` | 6 |
| `mermaids` | 7 |
| `anchorage` | 6 |

## Baseline (same run, same tokenizer, same word-count rule)

- TinyStories tokens/word: **2.860** — recomputed this run (over 12,609,293 tokens / 4,408,824 words)
- Relative inflation ratio: **1.129x** = 3.229 / 2.860

## D-09 Bands (RELATIVE — pre-registered, locked before this measurement ran)

| Band | Condition | Action |
| --- | --- | --- |
| GO | ratio <= 1.2x AND fit >= 90% | proceed to bins as designed |
| ADAPT | ratio 1.2-1.5x or fit 70-90% | apply turn truncation within the phase |
| STOP | ratio > 1.5x or fit < 70% | halt before any bin is built; escalate |

> **Baseline correction (2026-07-31):** the original ABSOLUTE bands (GO <= 2.5 tokens/word)
> were superseded because the frozen tokenizer's own home corpus (TinyStories) measures
> 2.864 tokens/word — above the old GO ceiling — so the absolute band would have
> rejected the model's known-working base training corpus. The bands are therefore RELATIVE.

**Rendered band on this run's numbers: GO** (smoke signal was 3.251/2.864 = 1.135x -> GO).

## Notes

- Turn truncation — the remaining ADAPT lever — shortens documents and can move metric 3, but
  mathematically CANNOT move tokens/word: the ratio is a property of tokenizer x register.
- The D-07 persona cap (**140 tokens**, pinned in CONTEXT) applies in plan 11-04 REGARDLESS of
  this verdict; the full-corpus p90 above is the sanity check against the smoke's p90 of 131.
- Phase 15 reads its honest "tokenizer-tax" number off metric 1 of this report.

## Verdict

PENDING — user decision at checkpoint (D-09).
