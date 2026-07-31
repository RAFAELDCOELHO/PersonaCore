"""DATA-04 inflation gate: measure, report against the D-09 bands, render the verdict (D-10).

Thin no-CLI driver — the metric logic lives in ``personacore.dialogue.inflation`` and every
number flows through ``encode_dialogue``, the SAME tokenization path the bin builder uses
(Pitfall 4: gate and bins can never tokenize differently). Numbers are REPORTED as evidence
against the pre-registered D-09 bands, not asserted (estimate_fisher report-don't-gate
posture); the committed ``results/inflation_report.md`` is the phase's evidence artifact —
Phase 15's tokenizer-tax number reads straight off it.

D-09 bands are RELATIVE (baseline-corrected 2026-07-31): the ratio is the full-corpus dialogue
tokens/word divided by the TinyStories baseline recomputed IN THIS RUN with the same frozen
tokenizer and word-count rule. The verdict itself is the USER'S at the blocking checkpoint —
this script only renders the band the numbers land in; the report's ``## Verdict`` section
stays PENDING until the user decides.

Run manually AFTER ``scripts/fetch_personachat.py``; NOT part of automated verification.
"""

import pathlib

from personacore.dialogue import compute_inflation_metrics, parse_episodes
from personacore.tokenizer import from_json

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"  # FROZEN production artifact
TRAIN_TXT = _REPO_ROOT / "data" / "raw" / "personachat" / "train_self_revised.txt"
VALID_TXT = _REPO_ROOT / "data" / "raw" / "personachat" / "valid_self_revised.txt"
TINYSTORIES_VALID = _REPO_ROOT / "data" / "TinyStoriesV2-GPT4-valid.txt"  # baseline corpus
REPORT_PATH = _REPO_ROOT / "results" / "inflation_report.md"  # COMMITTED evidence (D-10)

BLOCK_SIZE = 256  # ModelConfig.block_size — the training window metric 3 is judged against
RESEARCH_BASELINE = 2.864  # research-smoke TinyStories tokens/word — cited only if file absent


def _tinystories_tokens_per_word(tok):
    """TinyStories tokens/word under the SAME word-count rule (whitespace split).

    Documents are split on the ``<|endoftext|>`` separator and plain-encoded per document, so
    the separator contributes to NEITHER numerator NOR denominator (matching the dialogue
    metric, which excludes role tokens from both).
    """
    text = TINYSTORIES_VALID.read_text(encoding="utf-8")
    total_tokens = 0
    total_words = 0
    for doc in text.split("<|endoftext|>"):
        if not doc.strip():
            continue
        total_tokens += len(tok.encode(doc, allowed_special="none"))
        total_words += len(doc.split())
    return total_tokens / total_words, total_tokens, total_words


def _render_band(ratio, fit):
    """The pre-registered D-09 relative bands, exactly as locked before this run."""
    if ratio > 1.5 or fit < 0.70:
        return "STOP"
    if ratio > 1.2 or fit < 0.90:
        return "ADAPT"
    return "GO"


def main() -> None:
    for path in (TRAIN_TXT, VALID_TXT):
        if not path.exists():
            raise FileNotFoundError(
                f"Missing {path}. Run `python scripts/fetch_personachat.py` first."
            )

    tok = from_json(TOKENIZER_PATH)  # FROZEN production artifact — never retrain (Pitfall 6)

    train_eps = parse_episodes(TRAIN_TXT)
    valid_eps = parse_episodes(VALID_TXT)
    print(
        f"[measure_inflation] parsed {len(train_eps):,} train / {len(valid_eps):,} valid episodes"
    )

    # Metrics over the COMBINED train+valid corpus (the report states this choice).
    episodes = train_eps + valid_eps
    m = compute_inflation_metrics(episodes, tok, BLOCK_SIZE)
    tpw = m["tokens_per_word"]
    fit = m["fit_fraction"]
    pc = m["persona_cost"]
    print(
        f"[measure_inflation] tokens/word = {tpw:.3f} "
        f"(over {m['total_tokens']:,} tokens / {m['total_words']:,} words)"
    )
    print(
        f"[measure_inflation] persona cost: p50={pc['p50']:.0f} p90={pc['p90']:.0f} "
        f"max={pc['max']} (over {pc['episodes']:,} episodes)"
    )
    print(
        f"[measure_inflation] fit fraction (persona + first exchange <= {BLOCK_SIZE}): "
        f"{fit:.4f} ({m['fit_count']:,}/{m['episodes']:,} episodes)"
    )
    frag = ", ".join(f"{w}={n}" for w, n in m["fragmentation"].items())
    print(f"[measure_inflation] fragmentation samples: {frag}")

    # TinyStories baseline recomputed in the SAME run (D-09 relative bands).
    if TINYSTORIES_VALID.exists():
        base_tpw, base_tokens, base_words = _tinystories_tokens_per_word(tok)
        base_note = f"recomputed this run (over {base_tokens:,} tokens / {base_words:,} words)"
    else:
        base_tpw, base_note = RESEARCH_BASELINE, "CITED from research (baseline file absent)"
    ratio = tpw / base_tpw
    band = _render_band(ratio, fit)
    print(f"[measure_inflation] TinyStories baseline tokens/word = {base_tpw:.3f} ({base_note})")
    print(f"[measure_inflation] relative inflation ratio = {ratio:.3f}x -> band: {band}")

    frag_rows = "\n".join(f"| `{w}` | {n} |" for w, n in m["fragmentation"].items())
    # Markdown table rows must be single output lines; compose them here to keep source <=100.
    row1 = (
        f"| 1 | Dialogue tokens/word | **{tpw:.3f}** | over {m['total_tokens']:,} utterance "
        f"tokens / {m['total_words']:,} whitespace words |"
    )
    row2 = (
        f"| 2 | Persona-span cost (tokens) | p50 {pc['p50']:.0f} / p90 {pc['p90']:.0f} / "
        f"max {pc['max']} | over {pc['episodes']:,} episodes (`<|system|>` + persona ids) |"
    )
    row3 = (
        f"| 3 | Fit fraction (persona + first exchange <= {BLOCK_SIZE}) | **{fit:.4f}** | "
        f"{m['fit_count']:,} / {m['episodes']:,} episodes "
        f"(block_size {BLOCK_SIZE} = ModelConfig.block_size) |"
    )
    report = f"""# PersonaChat Tokenizer-Inflation Report (DATA-04, D-08/D-09/D-10)

> **What these numbers are:** the four pre-registered D-08 inflation metrics for the FULL
> PersonaChat self_revised corpus (train + valid COMBINED: {len(train_eps):,} + {len(valid_eps):,}
> = {m["episodes"]:,} episodes), tokenized through the frozen production tokenizer
> (`artifacts/tokenizer.json`) via `encode_dialogue` — the SAME path the bin builder uses, so
> gate and bins can never tokenize differently (Pitfall 4). **What they are not:** comparable
> to any other tokenizer, word-count rule, or serialization format; the ratio below is only
> meaningful against the TinyStories baseline recomputed in this same run.

## D-08 Metrics

| # | Metric | Value | Auditable denominator |
| --- | --- | --- | --- |
{row1}
{row2}
{row3}
| 4 | Fragmentation samples | see below | token count per fixed probe word |

| Probe word | Tokens |
| --- | --- |
{frag_rows}

## Baseline (same run, same tokenizer, same word-count rule)

- TinyStories tokens/word: **{base_tpw:.3f}** — {base_note}
- Relative inflation ratio: **{ratio:.3f}x** = {tpw:.3f} / {base_tpw:.3f}

## D-09 Bands (RELATIVE — pre-registered, locked before this measurement ran)

| Band | Condition | Action |
| --- | --- | --- |
| GO | ratio <= 1.2x AND fit >= 90% | proceed to bins as designed |
| ADAPT | ratio 1.2-1.5x or fit 70-90% | apply turn truncation within the phase |
| STOP | ratio > 1.5x or fit < 70% | halt before any bin is built; escalate |

> **Baseline correction (2026-07-31):** the original ABSOLUTE bands (GO <= 2.5 tokens/word)
> were superseded because the frozen tokenizer's own home corpus (TinyStories) measures
> {RESEARCH_BASELINE} tokens/word — above the old GO ceiling — so the absolute band would have
> rejected the model's known-working base training corpus. The bands are therefore RELATIVE.

**Rendered band on this run's numbers: {band}** (smoke signal was 3.251/2.864 = 1.135x -> GO).

## Notes

- Turn truncation — the remaining ADAPT lever — shortens documents and can move metric 3, but
  mathematically CANNOT move tokens/word: the ratio is a property of tokenizer x register.
- The D-07 persona cap (**140 tokens**, pinned in CONTEXT) applies in plan 11-04 REGARDLESS of
  this verdict; the full-corpus p90 above is the sanity check against the smoke's p90 of 131.
- Phase 15 reads its honest "tokenizer-tax" number off metric 1 of this report.

## Verdict

PENDING — user decision at checkpoint (D-09).
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"[measure_inflation] wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
