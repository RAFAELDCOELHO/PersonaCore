# Phase 11: Conversational Data Pipeline - Context

**Gathered:** 2026-07-31
**Status:** Ready for planning

<domain>
## Phase Boundary

**PersonaChat only** — a user-directed lean-scope decision made at this discussion (2026-07-31)
supersedes the DailyDialog + PersonaChat scope in ROADMAP.md/REQUIREMENTS.md. PersonaChat's
persona statements are fact-dense, which is exactly what Phase 14's teach-then-recall consumes;
DailyDialog added conversational breadth nothing downstream measures. The cut was
dependency-checked against Phases 12/13/14 before commitment: safe (see D-00 flags).

The phase delivers: checksum-verified PersonaChat fetch + from-scratch parse → role-token
serialization (`<|user|>`/`<|assistant|>`/`<|system|>`, ids 8185–8187) through the frozen
tokenizer → `dialog_{train,val}.bin` (uint16) + parallel `dialog_{train,val}_mask.bin` (uint8)
→ `get_batch_memmap_masked` + hand-built-fixture mask test — with the **tokenizer-inflation
gate measured and verdict rendered BEFORE the format hardens** (DATA-01..04, PersonaChat-only).
eos 8184 stays a document separator only. No HF `datasets`, no network at train time, no
training runs in this phase.

</domain>

<decisions>
## Implementation Decisions

### Scope frame (user-directed, supersedes roadmap text)
- **D-00:** Single corpus: **PersonaChat**; DailyDialog is cut. Dependency check performed and
  accepted: Phases 12/13 consume bins corpus-agnostically; Phase 14 is *better* served
  (persona-fact-grounded base). Accepted risk: PersonaChat is the sole corpus on an unowned S3
  endpoint with no explicit license (never re-host) — **checksum + local cache of the raw JSON
  is the only link-rot insurance; treat the cached raw file as a precious artifact from day
  one.** DATA-01 and roadmap Phase 11 text (which name both corpora) need a matching edit when
  this lands.

### Mask-bin policy
- **D-01:** Mask bins encode **assistant content + the turn's stop token**: mask=1 on assistant
  utterance tokens AND the boundary token that ends the turn (the next `<|user|>`, or eos at
  dialogue end), so the model trains to emit its own stop signal. Mask is built in **target
  space** (after the +1 label shift), per Pitfall 14's off-by-one warnings. The DATA-03
  hand-built fixture pins exactly this definition.
- **D-02:** Masked-vs-unmasked for the stage-2 fine-tune is **deferred to Phase 12's
  calibration smoke** as a measured decision (two short runs, compare dialogue val PPL).
  Phase 11 ships both aligned bins so either arm is ready; this resolves the
  ARCHITECTURE-prescribes-masking vs Pitfall-14-says-train-on-everything tension with data,
  not debate.
- **D-03:** Additive code surface: `get_batch_memmap_masked` (draws aligned windows from token
  + mask bins, sets `y[mask_shifted==0] = -100`) **lands in Phase 11** with the bins;
  `stop_ids` in `generate()` **defers to Phase 12**, its first consumer — Phase 11 stays
  purely data-side.

### Persona serialization
- **D-04:** Document format: one `<|system|>` token + persona sentences **newline-joined** +
  turns as `<|user|>`/`<|assistant|>` spans; **persona-owner = assistant**, partner = user;
  one whole dialogue = **one eos-terminated document** (reconstructed once from the final
  utterance's full history + reply — never per-utterance examples, which duplicate early turns
  ~10×). The retrieval `candidates` field is ignored.
- **D-05:** Variant: **self_revised** — the user chose the honest generalization test (revised
  personas prevent trivial word-overlap grounding) over the easier, already-verified original.
  **Fallback pre-registered:** the revised endpoint is unverified; try it first and pin its
  checksum if live — if it 404s or can't be checksummed, fall back to the verified
  `personachat_self_original.json` and record the substitution in phase docs. Phase 11 never
  blocks on link archaeology.
- **D-06:** Text normalization: **minimal from-scratch regex detokenizer** — rejoin
  contractions ("' m" → "'m", "do n't" → "don't"), close space-before-punctuation; text stays
  lowercase (no truecasing); unit-tested on a fixture. Less byte-fragmentation through the
  frozen BPE, and the inflation measurement then reflects realistic text.
- **D-07:** Persona-line token budget is **set by the gate**, not pre-committed: the DATA-04
  measurement reports persona-span token cost, and the format hardens with a budget (keep all
  lines / cap at N) chosen from those numbers.

### Inflation gate (DATA-04)
- **D-08:** Four-metric set from one encode pass: (1) tokens/word on dialogue text,
  (2) persona-span token-cost distribution (feeds D-07), (3) **% of dialogues where persona +
  first user→assistant exchange exceeds block_size=256** — the window-utility metric that
  replaces DATA-04's literal "%-of-examples-over-block_size", which is misleading under the
  packed-window regime of D-04, (4) qualitative fragmentation samples of typical names/entities.
- **D-09:** Pre-registered bands and actions (locked before any measurement runs, in the same
  register as Phase 14's threshold pre-registration): tokens/word ≤ 2.5 AND persona+exchange
  fits in ≥ 90% of dialogues → **GO** as designed; tokens/word 2.5–3.0 or fit 70–90% →
  **ADAPT** within the phase using pre-listed levers only (persona-line cap, turn truncation);
  tokens/word > 3.0 or fit < 70% → **STOP** and escalate to the user before any bin is built.
- **D-10:** Artifact: thin `scripts/measure_inflation.py` (logic in the package) + a
  **committed results/ markdown report** with the numbers, the bands, and the resulting
  GO/ADAPT verdict — evidence-over-assertion, same register as the N=2000 Fisher convergence
  stats; Phase 15's tokenizer-tax number reads straight off it.

### Claude's Discretion
- **Corpus-cut residue** (area offered, not selected — sensible defaults): whether any
  DailyDialog fetch/checksum remnant stays documented as fallback (default: cut cleanly; the
  verified endpoint + checksum live in research/SUMMARY.md if ever needed); train/val split
  policy (default: honor PersonaChat's native train/valid JSON split, mapped onto doc-level
  eos-boundary discipline — no dialogue straddles the cut); raw-data caching layout under
  `data/raw/` (gitignored) per the research fetch discipline; exact bin/report file naming.
- Mechanics of the DATA-01/roadmap wording edit for the DailyDialog cut (ride the phase's
  planning or first commit).
- Parser/fixture organization, mask-bin dtype details (uint8 established by research), and
  test-suite layout — following house patterns (thin scripts, logic in package, CPU-only
  tests).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & roadmap
- `.planning/REQUIREMENTS.md` — DATA-01..04 requirement text (**note D-00: DATA-01's
  "DailyDialog +" clause is superseded — PersonaChat only**); Out of Scope table (no tokenizer
  retrain — locked; no HF datasets)
- `.planning/ROADMAP.md` — Phase 11 goal + 4 success criteria (criterion 1's DailyDialog
  mention superseded per D-00); dependency map (Phase 11 independent of 9/10; Phase 12
  consumes bins + masks)

### v2.0 research (converged — do not re-litigate)
- `.planning/research/SUMMARY.md` — verified endpoints + checksums (S3 `personachat_self_original.json`
  200 OK / 209,850,483 B — the D-05 fallback; ParlAI DailyDialog checksum retained here if ever
  needed); PersonaChat licensing (none explicit — never re-host); two-mechanism stage split
- `.planning/research/ARCHITECTURE.md` — Pattern 3 (loss masking in the data path via
  `ignore_index=-100`, parallel uint8 mask bins, `allowed_special="all"` encode, eos =
  document separator only, doc-level no-leakage split); Pattern 4 (`stop_ids` design — Phase 12
  now, per D-03); `get_batch_memmap_masked` spec; role-token vocab-budget notes (live ids
  547 → ~550; `forbid_ids` mask unchanged; rows 8185–8187 cold-start spike is Phase 12's
  calibration concern)
- `.planning/research/PITFALLS.md` — Pitfall 13 (inflation: measure before building; warning
  signs tokens/word > 2.5–3 — the D-09 band source; never repurpose dead ids; never re-litigate
  the retrain); Pitfall 14 (mask off-by-one in target space; golden-fixture test kills the bug
  family; keep LM-regime and QA-regime masking as two named code paths — Phase 11 builds the
  LM-regime path, Phase 14 builds QA)

### v1.0 seams this phase consumes (code)
- `src/personacore/tokenizer/special.py` — the LOCKED special-token registry: role ids
  8185–8187 reserved and decodable; eos 8184
- `src/personacore/training/data.py` — `get_batch_memmap` (the idiom `get_batch_memmap_masked`
  mirrors: re-opened memmap per call, `len - block_size - 1` bound, uint16→int64 cast);
  `load_split` doc-boundary no-leakage discipline
- `scripts/encode_corpus.py` — the v1.0 run-once encode discipline (`allowed_special="all"`,
  uint16 bins) that `prepare_dialog_corpus.py` mirrors
- `artifacts/tokenizer.json` — the frozen production tokenizer (loaded, never retrained)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `get_batch_memmap` (`training/data.py`): the exact template for the masked variant — same
  indexing, same fresh-memmap-per-call leak avoidance, plus aligned mask-window draw and the
  `-100` scatter
- `load_split` (`training/data.py`): doc-level eos-boundary split with the whitespace-tail
  guard — the no-leakage discipline the dialogue split reuses
- `scripts/encode_corpus.py`: run-once raw→bin encode pattern (`prepare_dialog_corpus.py` is
  its dialogue sibling)
- Frozen tokenizer via `tokenizer.from_json` + `SPECIAL_TOKENS` registry: role tokens encode
  atomically with `allowed_special="all"` — zero tokenizer work needed
- Test idioms: hand-built-fixture exactness tests (Phase 10's analytic Fisher oracle style),
  committed-fixture data tests (Phase 3), thin-script/package-logic packaging (Phase 9/10
  smoke scripts)

### Established Patterns
- **Purity/additivity:** `model/gpt.py` never touched; `training/data.py` gets one additive
  function; loss masking rides `F.cross_entropy`'s default `ignore_index=-100` — the LOCKED
  `forward(idx, targets=None)` contract is untouched by construction
- **Fetch discipline:** stdlib `urllib.request` + `hashlib` pinned checksum → `data/raw/`
  (gitignored); never network at train time; no HF `datasets`
- **From-scratch boundary:** parser and detokenizer are hand-rolled (regex + json stdlib)
- **CPU-only, GPU-free tests**; all existing tests (222 passed / 1 skipped) stay green

### Integration Points
- Phase 12 consumes: `dialog_{train,val}.bin` + `dialog_{train,val}_mask.bin`,
  `get_batch_memmap_masked`, the D-02 masked-vs-unmasked calibration decision, and the D-09
  gate verdict (ADAPT levers change its corpus, not its harness)
- Phase 14 consumes: the D-04 serialization format (its teaching-set documents must match the
  stage-2 format, single `<|system|>` span included) and builds the separate QA-regime mask
  path (Pitfall 14 two-code-paths rule)
- Phase 15 consumes: the committed inflation report (the "tokenizer-tax" honest number)

</code_context>

<specifics>
## Specific Ideas

- **Measurement gates before build commitments** is the phase's identity: the inflation gate's
  bands are pre-registered (D-09) *before* the numbers exist — deliberately the same
  pre-registration discipline the user wants for Phase 14's recall thresholds ("defined before
  any run, not tuned after seeing results")
- self_revised (D-05) was chosen *against* the easier option on experimental-design grounds —
  the same instinct as the DailyDialog cut: target the actual thing being measured
- Evidence-over-assertion register throughout: committed inflation report (D-10), measured
  masking decision (D-02)

</specifics>

<deferred>
## Deferred Ideas

- **Tables-vs-figures for VIZ-01/VIZ-04** (user's Phase 15 lean directive): flagged that both
  are **Phase 13** requirements and that the forgetting curve is the one artifact plausibly
  meeting the user's own "genuinely needs a picture" bar (its content is divergence *shape*
  across eval intervals × 2 arms). Decision deferred to Phase 13's discussion — not a Phase 11
  concern.
- **Phase 14 protocol minimalism** (~10–20 facts, pre-registered pass/fail): user directive
  recorded for Phase 14's discuss/spec pass (the roadmap already flags that phase for one).
- **Roadmap numbering clarification:** the user's scope message described "Phase 13" as LoRA
  personalization (roadmap: Phase 14) — interpretation confirmed as no-phase-cut; if the user
  intended to merge/drop roadmap Phase 13 (the A/B), that's a roadmap edit to raise explicitly.

</deferred>

---

*Phase: 11-Conversational Data Pipeline*
*Context gathered: 2026-07-31*
