# Phase 11: Conversational Data Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-31
**Phase:** 11-Conversational Data Pipeline
**Areas discussed:** Mask-bin policy, Persona serialization, Inflation gate terms

---

## Scope Frame (user-directed, pre-discussion)

The user opened with a lean-scope directive for Phases 11–15: PersonaChat only for Phase 11
(DailyDialog cut on experimental-design grounds — persona statements are the fact-density
Phase 14 measures), Phases 12/13 unchanged, Phase 14 minimal-but-rigorous protocol with
pre-registered thresholds, Phase 15 tables over figures. A dependency check was requested and
performed before commitment: the cut is safe for Phases 12/13/14. Flags raised: (1) the user's
phase numbering was shifted one vs the roadmap (their "13" = roadmap 14) — interpreted as
no-phase-cut; (2) VIZ-01/04 are Phase 13 requirements, so tables-vs-figures reaches Phase 13
and the forgetting curve plausibly meets the user's own "genuinely needs a picture" bar —
deferred to Phase 13's discussion; (3) PersonaChat becomes a sole unowned/no-license endpoint —
checksum + local cache is the only link-rot insurance; (4) DATA-01/roadmap text needs a
matching edit.

A fourth gray area ("Corpus-cut residue") was offered and not selected — handled as Claude's
discretion with defaults recorded in CONTEXT.md.

---

## Mask-bin policy

| Option | Description | Selected |
|--------|-------------|----------|
| Bins built, stage 2 unmasked (Recommended) | Bins + fixture ship; Phase 12 trains on everything per Pitfall 14 | |
| Stage 2 trains masked | Assistant-only loss as ARCHITECTURE prescribes | |
| Defer to Phase 12 calibration | Both bins ship; masked-vs-unmasked measured via two short smoke runs | ✓ |

**User's choice:** Defer to Phase 12 calibration — turns the ARCHITECTURE-vs-PITFALLS tension into data.

| Option | Description | Selected |
|--------|-------------|----------|
| Content + stop token (Recommended) | Mask=1 on assistant tokens + the turn-ending boundary token; target space | ✓ |
| Content only | Strictly assistant utterance tokens; no stop-signal training | |
| You decide | Planner discretion per ARCHITECTURE Pattern 3 / Pitfall 14 | |

**User's choice:** Content + stop token.

| Option | Description | Selected |
|--------|-------------|----------|
| Batch variant now, stop_ids later (Recommended) | get_batch_memmap_masked in Phase 11; stop_ids to Phase 12 | ✓ |
| Both now, as researched | Both additive changes in Phase 11 per research summary | |
| Bins + fixture only | Maximal lean; both code changes defer to Phase 12 | |

**User's choice:** Batch variant now, stop_ids later — Phase 11 stays purely data-side.

---

## Persona serialization

| Option | Description | Selected |
|--------|-------------|----------|
| System prefix, owner = assistant (Recommended) | <|system|> span opens each document; persona-owner's turns are assistant | ✓ |
| Drop persona lines | Turns only — discards the fact-density that motivated the corpus cut | |
| You decide | Planner discretion per ARCHITECTURE Pattern 3 | |

**User's choice:** System prefix, owner = assistant.

| Option | Description | Selected |
|--------|-------------|----------|
| Gate decides (Recommended) | No upfront cap; DATA-04 measurement sets the persona budget | ✓ |
| Fixed cap now | Pre-commit e.g. 3 lines / ~64 tokens before measuring | |
| Keep all lines regardless | Never truncate; risks persona-dominated windows on bad inflation | |

**User's choice:** Gate decides.

| Option | Description | Selected |
|--------|-------------|----------|
| One dialogue = one document (Recommended) | Reconstruct full conversation once; eos-terminated; ignore candidates | ✓ |
| Per-utterance examples | HF-style; guaranteed in-window context but ~10× duplication | |
| You decide | Planner picks off window-coverage numbers | |

**User's choice:** One dialogue = one document.

| Option | Description | Selected |
|--------|-------------|----------|
| self_original (Recommended) | High lexical overlap (easier at 13.9M); verified endpoint | |
| self_revised | Rephrased personas — honest generalization test; endpoint unverified | ✓ |

**User's choice:** self_revised — against the recommendation, on experimental-design grounds
(same instinct as the DailyDialog cut).

| Option | Description | Selected |
|--------|-------------|----------|
| Fall back to self_original (Recommended) | Verify-first; substitute the verified file if revised is dead; record it | ✓ |
| Hard requirement | Revised or bust — hunt mirrors before pipeline work | |
| Ship both if available | Bin both variants; comparison artifact nothing consumes | |

**User's choice:** Fall back to self_original.

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal detokenizer (Recommended) | Regex rejoin of contractions/punctuation; stays lowercase; fixture-tested | ✓ |
| Encode raw as-is | Zero preprocessing; worst-case fragmentation of spaced punctuation | |
| Detokenize + truecase | Also restore capitalization — heuristic guesswork | |

**User's choice:** Minimal detokenizer.

| Option | Description | Selected |
|--------|-------------|----------|
| Single tag, newline-joined (Recommended) | One <|system|> token + newline-joined persona lines | ✓ |
| Tag per persona line | <|system|> before every sentence; 4–5 specials per dialogue | |
| You decide | Planner picks; consistent with Phase 14 teaching format | |

**User's choice:** Single tag, newline-joined.

---

## Inflation gate terms

| Option | Description | Selected |
|--------|-------------|----------|
| Four-metric set (Recommended) | tokens/word, persona-span cost, persona+exchange window-fit %, name fragmentation | ✓ |
| DATA-04 literal two | tokens/word + %-over-block_size only (misleading under packed windows) | |
| You decide | Planner picks, one encode pass | |

**User's choice:** Four-metric set.

| Option | Description | Selected |
|--------|-------------|----------|
| 2.5 / 3.0 bands (Recommended) | ≤2.5 & ≥90% fit GO; 2.5–3.0 or 70–90% ADAPT (pre-listed levers); >3.0 or <70% STOP+escalate | ✓ |
| Stricter gate | GO only ≤2.0 — near-disqualifying stance on inflation | |
| Measure, no bands | Decide reactively — weaker against tuned-after-results critique | |

**User's choice:** 2.5 / 3.0 bands, pre-registered before measurement.

| Option | Description | Selected |
|--------|-------------|----------|
| Committed report + script (Recommended) | scripts/measure_inflation.py + committed results/ markdown with verdict | ✓ |
| Script output only | Numbers in phase SUMMARY, no committed artifact | |
| You decide | Planner picks the artifact shape | |

**User's choice:** Committed report + script.

---

## Claude's Discretion

- Corpus-cut residue: DailyDialog remnant policy (default: cut cleanly), train/val split
  (default: PersonaChat native split + doc-level eos discipline), `data/raw/` caching layout,
  bin/report naming
- DATA-01/roadmap wording edit mechanics for the DailyDialog cut
- Parser/fixture/test-suite organization per house patterns

## Deferred Ideas

- Tables-vs-figures for VIZ-01/VIZ-04 → Phase 13 discussion (forgetting curve flagged as
  plausibly meeting the "genuinely needs a picture" bar)
- Phase 14 protocol minimalism (~10–20 facts, pre-registered pass/fail) → Phase 14 discuss/spec
- Roadmap numbering clarification (user's "13" vs roadmap 14) → raise explicitly if a merge of
  roadmap Phase 13 was actually intended
